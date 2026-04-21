# Agents

A generic looped or single-shot multi-agent pipeline designed to execute engineering tasks.

## Features

Uses [CrewAI](https://crewai.com), to orchestrates a team of AI agents in these tasks:

- Implement
- Refactor
- Review
- Strategize
 
Each task has a chain of four agents. Optimized for local LLMs (Ollama, llama.cpp, OpenAI) to keep your source code private.

## The 6-agent Looped Operator

Even with frontier models (e.g. ChatGPT 5.4 Extra High, Gemini Pro, Grok Heavy), LLM output on complex tasks is never 100% correct. By rotating through layers of agents:

- Strategize: blueprint the feature with a structured spec (JSON with acceptance criteria, edge cases, non-goals).
- Task: implement the feature.
- Reviewer 1: Review the implementation.
- Delta: Retrieve the delta between the review and the initial strategy blueprint; formulate a plan to fix the delta through tests - delineate "PASS", "PARTIAL", or "FAIL" conditions.
- Optimizer: Close the delta between the implementation and the issues from plan.
- Reviewer 2: Review the optimization. If it doesn't fufill initial strategy with each feature with "PASS", repeat from delta.

I found this ensures a tight workflow loop that closes massive amounts of issues under the least amount of effort. Finally, a human will review and check off the final diff. `--max-iterations` can be appended to get a human reviewer in the loop.

## Installation

This project uses `uv` for fast, reliable Python package management.

```bash
# Clone the repository
git clone [https://github.com/phooning/agents.git](https://github.com/phooning/agents.git)
cd agents

# Install dependencies
uv sync
```

## Configuration

Agents uses environment variables for easy configuration. You can export these in your shell or use a `.env` file.

| Variable | Description | Default |
| :--- | :--- | :--- |
| `AGENT_BASE_URL` | OpenAI-compatible API endpoint | `http://localhost:11434/v1` |
| `AGENT_MODEL` | The LLM model name | `qwen2.5-coder:32b` |
| `AGENT_API_KEY` | API Key (if using a remote provider) | `no-key-required` |

## Usage

Run the agent via `uv run`. The recommended way is to install it onto your path:

```sh
uv build
uv tool install --force --editable .
```

The tool should be available via `agents`.

### Refactor Code
```bash
agents -f src-tauri/src/main.rs refactor "Optimize error handling in the database module"
```

### Implement a Feature
```bash
agents -f src/App.tsx implement "Add a dark mode toggle that persists in Tauri store"
```

### Auto-Write Changes
Add the `--write` flag to automatically apply the AI's reviewed code to your file.
```bash
agents -f src/components/Button.tsx --write refactor "Make this component accessible (ARIA)"
```

## Roadmap

- Create generic use cases following [](https://github.com/garrytan/gstack/tree/main).

## Contributing

Contributions are welcome. Feel free to open an issue or PR.
