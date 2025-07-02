# Recruitee MCP Server

**Model Context Protocol (MCP) server for Recruitee – advanced search, reporting, and analytics for recruitment data.**

[![Deploy on Fly.io](https://badgen.net/badge/Fly.io/deploy/green)](https://fly.io/apps/recruitee-mcp-server)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 🚀 Overview

The **Model Context Protocol (MCP)** is rapidly becoming the standard for connecting AI agents to external services. This project implements an MCP server for [Recruitee](https://recruitee.com/), enabling advanced, AI-powered search, filtering, and reporting on recruitment data.

Unlike basic CRUD wrappers, this server focuses on the tasks where LLMs and AI agents excel: **summarizing, searching, and filtering**. It exposes a set of tools and prompt templates, making it easy for any MCP-compatible client to interact with Recruitee data in a structured, agent-friendly way.

---

## ✨ Features

* [x] **Advanced Candidate Search & Filtering**  
  Search for candidates by skills, status, talent pool, job, tags, and more. Example:  
  _"Find candidates with Elixir experience who were rejected due to salary expectations."_

* [x] **Recruitment Summary Reports**  
  Generate summaries of recruitment activities, such as time spent in each stage, total process duration, and stage-by-stage breakdowns.

* [x] **Recruitment Statistics**  
  Calculate averages and metrics (e.g., average expected salary for backend roles, average time to hire, contract type stats).

* [x] **General Search**  
  Quickly find candidates, recruitments, or talent pools by name or attribute.

* [x] **Prompt Templates**  
  Exposes prompt templates for LLM-based clients, ensuring consistent and high-quality summaries.

---

## 🛠 Example Queries

- _Find candidates with Elixir experience who were rejected due to salary expectations._
- _Show me their personal details including CV URL._
- _Why was candidate 'X' disqualified and at what stage?_
- _What are the other stages for this offer?_
- _Show candidates whose GDPR certification expires this month._
- _What's time to fill sales assistant offer?_
- _Create a pie chart with sources for AI engineer offer._
- _Create a recruitment report._

---

## 🧑‍💻 Implementation

- **Language:** Python
- **Framework:** [FastMCP](https://github.com/chrishayuk/fastmcp)
- **API:** [Recruitee Careers Site API](https://docs.recruitee.com/reference/intro-to-careers-site-api)
- **Schemas:** All MCP tool schemas are generated from Pydantic models, with rich metadata for LLMs.

The server retrieves and processes data from Recruitee, exposing it via MCP tools. Summaries are composed by the client using provided prompt templates.

---

## 🚦 Transport Methods

- **stdio** – For local development and testing.
- **streamable-http** – For remote, production-grade deployments (recommended).
- **SSE** – Supported but deprecated in some MCP frameworks.

---

## 🧪 Usage
💡 **Tip:** For data visualization, combine this with chart-specific MCP servers like [mcp-server-chart](https://github.com/antvis/mcp-server-chart)

### Local (stdio)

1. **Configure your MCP client:**

    ```json
    {
      "mcpServers": {
        "recruitee": {
          "command": "/path/to/.venv/bin/python",
          "args": ["/path/to/recruitee-mcp-server/src/app.py", "--transport", "stdio"]
        }
      }
    }
    ```

2. **Run with [mcp-cli](https://github.com/chrishayuk/mcp-cli):**

    ```bash
    mcp-cli chat --server recruitee --config-file /path/to/mcp-cli/server_config.json
    ```

### Remote (streamable-http)
1. **Use [mcp-remote](https://github.com/chrishayuk/mcp-remote):**

    ```json
    {
      "mcpServers": {
        "recruitee": {
          "command": "npx",
          "args": [
            "mcp-remote",
            "https://recruitee-mcp-server.fly.dev/mcp/",
            "--header",
            "Authorization: Bearer ${MCP_BEARER_TOKEN}"
          ],
          "env": {
            "MCP_BEARER_TOKEN": "KEY"
          }
        }
      }
    }
    ```


2. **or use directly if client supports bearer token authorization**

    ```json
    {
      "mcpServers": {
        "recruitee": {
          "transport": "streamable-http",
          "url": "https://recruitee-mcp-server.fly.dev/mcp"
        }
      }
    }
    ```

---

## ☁️ Deployment

### Deploy to Fly.io

1. **Set your secrets in `.env`**
2. **Create a volume**
    ```bash
    make create_volume
    ```
3. **Deploy:**

    ```bash
    flyctl auth login
    make deploy
    ```

---

## 📚 Resources

- [Recruitee MCP Server (GitHub)](https://github.com/EmpoweredHouse/recruitee-mcp-server)
- [Recruitee API Docs](https://docs.recruitee.com/reference/intro-to-careers-site-api)
- [Model Context Protocol (MCP)](https://github.com/chrishayuk/model-context-protocol)
- [FastMCP Framework](https://github.com/chrishayuk/fastmcp)
- [MCP Server for Charts](https://github.com/antvis/mcp-server-chart)
---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome!  

---

## 📝 License

This project is [MIT licensed](LICENSE).

---

**Empower your AI agents with advanced recruitment data access and analytics.**

