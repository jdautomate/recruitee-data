import os
import argparse
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize the MCP server
mcp = FastMCP(
    name="Recruitee Server",
    description="A server for Recruitee API",
)

import tools # Import tools to register them with the MCP server

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Run the Recruitee MCP server.")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse"],
        default="sse",
        help="Transport method to use: 'stdio' for standard input/output or 'sse' for Server-Sent Events."
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind the server to (default: 0.0.0.0)."
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind the server to (default: 8000)."
    )
    args = parser.parse_args()

    mcp.host = args.host
    mcp.port = args.port

    if not os.getenv("RECRUITEE_API_TOKEN") or not os.getenv("RECRUITEE_COMPANY_ID"):
        raise ValueError("Please set RECRUITEE_COMPANY_ID and RECRUITEE_API_TOKEN in your environment variables.")

    print(f"Starting Recruitee MCP server with transport: {args.transport}")
    mcp.run(transport=args.transport)

if __name__ == "__main__":
    main()
