import os

from dotenv import load_dotenv, find_dotenv

from fastmcp import FastMCP



# Load environment variables from .env file if exists
if find_dotenv() != "":
    load_dotenv(find_dotenv())

RECRUITEE_COMPANY_ID = os.getenv("RECRUITEE_COMPANY_ID")
RECRUITEE_API_TOKEN = os.getenv("RECRUITEE_API_TOKEN")

# Initialize the MCP server
mcp = FastMCP(
    name="Recruitee Server",
    instructions="A server for Recruitee API",
)