# Copy to .env and replace the generated key before starting the service.
# Generate one with: python -c 'import secrets; print(secrets.token_urlsafe(32))'
AWM_ADMIN_API_KEY=replace-with-a-random-secret-at-least-24-characters

# Agent tokens are separate from admin tokens. Use a comma-separated list for multiple agents.
# Example: AWM_AGENT_API_KEYS=agent-key-1,agent-key-2
AWM_AGENT_API_KEYS=

# The server binds to loopback on the host by default.
AWM_BIND_ADDRESS=127.0.0.1
AWM_PORT=8765
AWM_VOLUME_NAME=agent-work-memory-data

# Raw event content retention. The worker enforces this automatically.
AWM_RAW_RETENTION_DAYS=30
AWM_RETENTION_INTERVAL_SECONDS=3600

# Local-model defaults for the base Compose deployment. If using the optional
# compose.local-llm.yaml overlay, these are set to the Ollama service there.
AWM_LLM_BASE_URL=http://127.0.0.1:11434/v1
AWM_LLM_MODEL=qwen2.5:14b
AWM_LLM_API_KEY=local
AWM_LLM_TIMEOUT_SECONDS=90
AWM_OLLAMA_MODEL=qwen2.5:14b
OLLAMA_VOLUME_NAME=agent-work-memory-ollama
