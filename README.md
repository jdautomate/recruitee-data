### Testing MCP server locally - stdio
For testing responses you can use https://github.com/chrishayuk/mcp-cli repository.
Example client configuration for local testing:
```json
{
  "mcpServers": {
    "recruitee": {
      "command": "/path/to/.venv/bin/python",
      "args": ["/path/to/recruitee-mcp-server/app/server.py", "--transport", "stdio"]
    }
  }
}
```
### Testing deployed MCP server - sse
For sse testing you can use https://github.com/sidharthrajaram/mcp-sse repository.
Run the server using docker:
```bash
docker run -p 8000:8000 --name mcp-recruitee-server mcp-recruitee-server
```
Then run the client:
```
uv run client.py http://0.0.0.0:8000/sse
```
