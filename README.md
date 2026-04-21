# Agents

A generic multi-agent pipeline designed to execute specific engineering tasks.

## Features

Uses [CrewAI](https://crewai.com), to orchestrates a team of AI agents in these tasks:

- Implement
- Refactor
- Review
- Strategize
 
Each task has a chain of four agents. Optimized for local LLMs (Ollama, llama.cpp, OpenAI) to keep your source code private.

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

- Create generic use cases following https://github.com/garrytan/gstack/tree/main.

## Contributing

Contributions are welcome. Feel free to open an issue or PR.
