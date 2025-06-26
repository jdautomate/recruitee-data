import os

from dotenv import load_dotenv, find_dotenv
from fastmcp import FastMCP



_INSTRUCTIONS = """A server for Recruitee API"""

if find_dotenv() != "":
    load_dotenv(find_dotenv())

RECRUITEE_COMPANY_ID = os.getenv("RECRUITEE_COMPANY_ID")
RECRUITEE_API_TOKEN = os.getenv("RECRUITEE_API_TOKEN")
BASE_DEPLOY_URL = os.getenv("BASE_DEPLOY_URL")

# Initialize the MCP server
mcp = FastMCP(
    name="Recruitee Server",
    instructions=_INSTRUCTIONS,
)