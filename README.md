# Agents

A specialized multi-agent pipeline designed to refactor and implement features (current in **Tauri** applications).

Uses [CrewAI](https://crewai.com), to orchestrates a team of AI agents—Analyst, Architect, Implementer, and Reviewer—to ensure cross-language consistency between your **Rust** backend and **TypeScript/React** frontend.

## Features

- **Tauri-Aware Agents:** Specifically prompted to understand `tauri::command`, `invoke`, and frontend-backend state synchronization.
- **Local-First Design:** Optimized for local LLMs (via Ollama or vLLM) to keep your source code private.
- **Safety First:** Includes a mandatory review step and automatic file backups (`.bak`) when writing changes.
- **Dual Workflows:**
  - `refactor`: Clean up existing logic for performance or safety.
  - `implement`: Generate new features across multiple files.

## Installation

This project uses `uv` for fast, reliable Python package management.

```bash
# Clone the repository
git clone [https://github.com/phooning/agents.git](https://github.com/phooning/agents.git)
cd tauri-agent

# Install dependencies
uv sync
```

## Configuration

Tauri-Agent uses environment variables for easy configuration. You can export these in your shell or use a `.env` file.

| Variable | Description | Default |
| :--- | :--- | :--- |
| `TAURI_AGENT_BASE_URL` | OpenAI-compatible API endpoint | `http://localhost:11434/v1` |
| `TAURI_AGENT_MODEL` | The LLM model name | `qwen2.5-coder:32b` |
| `TAURI_AGENT_API_KEY` | API Key (if using a remote provider) | `no-key-required` |

## Usage

Run the agent via `uv run`:

### Refactor Code
```bash
uv run agent -f src-tauri/src/main.rs refactor "Optimize error handling in the database module"
```

### Implement a Feature
```bash
uv run agent -f src/App.tsx implement "Add a dark mode toggle that persists in Tauri store"
```

### Auto-Write Changes
Add the `--write` flag to automatically apply the AI's reviewed code to your file.
```bash
uv run agent -f src/components/Button.tsx --write refactor "Make this component accessible (ARIA)"
```

## Roadmap

- Add **Reviewer** role.
- Create generic use cases following https://github.com/garrytan/gstack/tree/main.

## Contributing

Contributions are welcome. Feel free to open an issue or PR.
