#!/usr/bin/env bash
set -euo pipefail

RAW_BASE_URL="${AGENT_BASE_URL}"
if [[ "$RAW_BASE_URL" == */v1 ]]; then
  BASE_URL="$RAW_BASE_URL"
  SERVER_URL="${RAW_BASE_URL%/v1}"
else
  SERVER_URL="${RAW_BASE_URL%/}"
  BASE_URL="${SERVER_URL}/v1"
fi
MODEL="${AGENT_MODEL:-Qwen3.6-35B-A3B-UD-Q4_K_S.gguf}"
API_KEY="${AGENT_API_KEY}"
TARGET_FILE="${1:-artifacts/options.js}"
TASK="${2:-Smoke test the review pipeline against this file. Confirm that you can read it, then return any concrete review output.}"
AUTH_HEADER="Authorization: Bearer ${API_KEY}"

if [[ ! -f "$TARGET_FILE" ]]; then
  echo "Target file not found: $TARGET_FILE" >&2
  exit 2
fi

health_url="${SERVER_URL}/health"
props_url="${SERVER_URL}/props"
models_url="${BASE_URL%/}/models"
completion_url="${SERVER_URL}/completion"

echo "Checking llama.cpp health: $health_url"
if ! curl -fsS -m 10 -H "$AUTH_HEADER" "$health_url" >/dev/null; then
  echo "Health check failed. Start llama.cpp, confirm the API key, then retry." >&2
  exit 1
fi

echo "Checking llama.cpp props: $props_url"
if ! curl -fsS -m 10 -H "$AUTH_HEADER" "$props_url" >/dev/null; then
  echo "Props check failed. Confirm llama.cpp exposes /props, then retry." >&2
  exit 1
fi

models_file="$(mktemp "${TMPDIR:-/tmp}/agents-review-models.XXXXXX")"
echo "Checking llama.cpp models: $models_url"
if ! curl -fsS -m 10 -H "$AUTH_HEADER" "$models_url" -o "$models_file"; then
  echo "Models check failed. Start llama.cpp with OpenAI-compatible /v1 support, then retry." >&2
  exit 1
fi

if ! python3 - "$models_file" "$MODEL" <<'PY'
import json
import sys

models_path, expected_model = sys.argv[1:3]
with open(models_path, encoding="utf-8") as models_file:
    payload = json.load(models_file)

model_ids = [
    item.get("id")
    for item in payload.get("data", [])
    if isinstance(item, dict) and isinstance(item.get("id"), str)
]
if expected_model not in model_ids:
    print(f"Configured model not advertised by /v1/models: {expected_model}", file=sys.stderr)
    if model_ids:
        print("Available models:", file=sys.stderr)
        for model_id in model_ids:
            print(f"  - {model_id}", file=sys.stderr)
    else:
        print("No model ids found in /v1/models response.", file=sys.stderr)
    sys.exit(1)
PY
then
  echo "Model validation failed. See: $models_file" >&2
  exit 1
fi

completion_file="$(mktemp "${TMPDIR:-/tmp}/agents-review-completion.XXXXXX")"
echo "Checking llama.cpp completion: $completion_url"
if ! curl -fsS -m 30 \
  -H "$AUTH_HEADER" \
  -H "Content-Type: application/json" \
  -d '{"prompt":"\n","n_predict":1}' \
  "$completion_url" \
  -o "$completion_file"; then
  echo "Minimum completion check failed. Confirm llama.cpp can generate tokens, then retry." >&2
  exit 1
fi

output_file="$(mktemp "${TMPDIR:-/tmp}/agents-review-smoke.XXXXXX")"
echo "Running review smoke test with model: $MODEL"
echo "Target: $TARGET_FILE"

AGENT_BASE_URL="$BASE_URL" \
AGENT_MODEL="$MODEL" \
AGENT_API_KEY="$API_KEY" \
  uv run agents -f "$TARGET_FILE" review "$TASK" | tee "$output_file"

if ! grep -q '[^[:space:]]' "$output_file"; then
  echo "Review command produced no output." >&2
  exit 1
fi

if grep -Eiq 'Traceback|Connection refused|Error code:|APIConnectionError' "$output_file"; then
  echo "Review command emitted an error marker. See: $output_file" >&2
  exit 1
fi

echo "Smoke output captured at: $output_file"
