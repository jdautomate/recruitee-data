### Clients

For testing the server, you can use any MCP client that supports the selected transport method.

For example, for `stdio` and `streamable-http`, you can use apps like **Claude Desktop**.

However, if you want to test the server using open-source clients, you can use the following:

- [mcp-cli](https://github.com/chrishayuk/mcp-cli) – Perfect for testing `stdio` transport. Doesn’t support `streamable-http` or `SSE` directly.
- [mcp-sse](https://github.com/sidharthrajaram/mcp-sse) – Supports `SSE` transport, but CLI isn’t fully functional yet.

---

### Server

There are 3 transport methods available:

- **stdio** – Standard input/output.
- **streamable-http** – HTTP transport with streaming support. Ideal for deployment. Becoming more popular in the MCP community and gaining client support.
- **SSE (Server-Sent Events)** – Not recommended. Already deprecated in some MCP frameworks. Additionally, only a limited number of clients support this method.

---

### Using Locally with `stdio` Transport

Example client configuration:

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

Run the `mcp-cli` client like this:

```bash
mcp-cli chat --server recruitee --config-file /path/to/mcp-cli/server_config.json
```

Check if tools are available by typing `/tools` in the console.

---

### Using Remotely with `streamable-http` Transport

Example client configuration:

```json
{
  "mcpServers": {
    "recruitee": {
      "transport": "streamable-http",
      "url": "https://url.to.server/mcp"
    }
  }
}
```

This configuration works with **Claude Desktop** (paid subscription only).

For the **free tier**, use this workaround:

```json
{
  "mcpServers": {
    "recruitee": {
      "command": "npx",
      "args": [
        "mcp-remote",
        "https://url.to.server/mcp/"
      ]
    }
  }
}
```

---

### Using Remotely with `SSE` Transport (Not Recommended)

Example client configuration:

```json
{
  "mcpServers": {
    "recruitee": {
      "command": "npx",
      "args": [
        "mcp-remote",
        "https://url.to.server/sse"
      ]
    }
  }
}
```

This configuration may work with any MCP client, but note that the client does **not** use SSE directly.

---

### Deploy Server to Fly.io

You can deploy the server to any cloud provider. In this example, we use **Fly.io**.

Update your Dockerfile to use either `SSE` or `streamable-http` transport.  
Set your secrets in a `.env` file and then run:

```bash
flyctl auth login
make deploy
```
