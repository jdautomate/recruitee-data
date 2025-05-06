### Testing MCP server locally - stdio
For testing responses you can use https://github.com/chrishayuk/mcp-cli repository.
Example client configuration for local testing:
```json
{
  "mcpServers": {
    "recruitee": {
      "command": "/path/to/.venv/bin/python",
      "args": ["/path/to/recruitee-mcp-server/app/app.py", "--transport", "stdio"]
    }
  }
}
```
Then run the client:
```bash
mcp-cli chat --server recruitee --config-file /path/to/mcp-cli/server_config.json
```
Check if tools are available typing `/chat` in console.


### Testing docker MCP server - sse
For sse testing you can use https://github.com/sidharthrajaram/mcp-sse repository.
Run the server using docker:
```bash
make run-local-fresh
```
Then run the client:
```bash
cd mcp-sse
uv run client.py http://0.0.0.0:8000/sse
```


### Deploy server to fly
```bash
flyctl auth login
make deploy
```
Then run the client:
```bash
cd mcp-sse
uv run client.py https://url.to.fly.deployment/sse
```