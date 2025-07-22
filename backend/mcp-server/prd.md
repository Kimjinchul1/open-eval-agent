# 실행 프로세스

uv init mcp-server
cd mcp-server
uv venv
source .venv/bin/activate
uv add "mcp[cli]" httpx

uv run python mcp_server.py


# config.json 작성법
{
  "mcpServers": {
    "ai-evaluation": {
      "command": "uv",
      "args": [
        "--directory",
        "/home/kimhc/open_deep_research/backend/mcp-server",
        "run",
        "app.py"
      ]
    }
  }
}