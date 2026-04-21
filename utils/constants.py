import os

BASE_URL = os.getenv("TAURI_AGENT_BASE_URL", "http://localhost:11434/v1")
MODEL = os.getenv("TAURI_AGENT_MODEL", "Qwen3.6-35B-A3B")
API_KEY = os.getenv("TAURI_AGENT_API_KEY", "no-key-required")
