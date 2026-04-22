import os

BASE_URL = os.getenv("AGENT_BASE_URL", "http://localhost:11434/v1")
MODEL = os.getenv("AGENT_MODEL", "Qwen3.6-35B-A3B")
API_KEY = os.getenv("AGENT_API_KEY", "no-key-required")
LLM_PROVIDER = os.getenv("AGENT_LLM_PROVIDER", "ollama")
