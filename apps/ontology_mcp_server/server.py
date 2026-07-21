"""Databricks App entrypoint for the reusable Ontology MCP server. Domain
agents across the enterprise point their MCP client at this single deployed
server instead of each standing up their own ontology access layer.
"""
import asyncio

from enterprise_ontology.mcp.server import run_stdio

if __name__ == "__main__":
    asyncio.run(run_stdio())
