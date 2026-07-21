"""Reusable Ontology MCP server — PRD Sec. 11. Domain teams' agents connect to
THIS server rather than reimplementing ontology access; it is deployed once
by the platform team as a Databricks App (see apps/ontology_mcp_server/).

Built on the `mcp` Python SDK. Identity for every call comes from the
transport-level request context (extracted via security.obo), never from a
tool argument — a caller cannot claim to be someone else by passing a
different `user_context` in their JSON-RPC payload.
"""
from __future__ import annotations

import logging

from mcp.server import Server
from mcp.server.models import InitializationOptions
import mcp.types as types

from ..security.obo import extract_user_context
from . import tools as tool_impls
from .tools import OntologyToolkit

logger = logging.getLogger(__name__)

TOOL_DEFINITIONS: list[types.Tool] = [
    types.Tool(
        name="resolve_concept",
        description="Resolve one or more business terms to canonical concept IDs via exact + synonym lookup.",
        inputSchema={
            "type": "object",
            "properties": {
                "terms": {"type": "array", "items": {"type": "string"}},
                "domain": {"type": "string"},
            },
            "required": ["terms"],
        },
    ),
    types.Tool(
        name="resolve_metric",
        description="Resolve a business term to certified metric definitions.",
        inputSchema={
            "type": "object",
            "properties": {"term": {"type": "string"}, "domain": {"type": "string"}},
            "required": ["term"],
        },
    ),
    types.Tool(
        name="get_metric_definition",
        description="Fetch the full certified definition for a known metric_id.",
        inputSchema={"type": "object", "properties": {"metric_id": {"type": "string"}}, "required": ["metric_id"]},
    ),
    types.Tool(
        name="get_allowed_dimensions",
        description="List the dimension_ids a given metric_id may be sliced by.",
        inputSchema={"type": "object", "properties": {"metric_id": {"type": "string"}}, "required": ["metric_id"]},
    ),
    types.Tool(
        name="resolve_dimension_value",
        description="Resolve free-text input to governed, authorized canonical dimension values.",
        inputSchema={
            "type": "object",
            "properties": {"dimension_id": {"type": "string"}, "user_text": {"type": "string"}},
            "required": ["dimension_id", "user_text"],
        },
    ),
    types.Tool(
        name="resolve_hierarchy_node",
        description="Look up a single hierarchy node by its canonical_id.",
        inputSchema={
            "type": "object",
            "properties": {"hierarchy_id": {"type": "string"}, "canonical_id": {"type": "string"}},
            "required": ["hierarchy_id", "canonical_id"],
        },
    ),
    types.Tool(
        name="expand_hierarchy",
        description="Expand a hierarchy node into all of its descendants.",
        inputSchema={
            "type": "object",
            "properties": {
                "hierarchy_id": {"type": "string"},
                "canonical_id": {"type": "string"},
                "include_self": {"type": "boolean"},
            },
            "required": ["hierarchy_id", "canonical_id"],
        },
    ),
    types.Tool(
        name="get_approved_join_path",
        description="Return the approved join expression between two concepts, or none if unapproved.",
        inputSchema={
            "type": "object",
            "properties": {"source_concept_id": {"type": "string"}, "target_concept_id": {"type": "string"}},
            "required": ["source_concept_id", "target_concept_id"],
        },
    ),
    types.Tool(
        name="get_business_rule",
        description="Fetch a business rule by rule_id, including its executable reference if any.",
        inputSchema={"type": "object", "properties": {"rule_id": {"type": "string"}}, "required": ["rule_id"]},
    ),
    types.Tool(
        name="get_authoritative_source",
        description="Return the ranked authority/provenance sources backing a concept.",
        inputSchema={"type": "object", "properties": {"concept_id": {"type": "string"}}, "required": ["concept_id"]},
    ),
    types.Tool(
        name="validate_semantic_plan",
        description="Run deterministic validation (certification, compatibility, authorization, limits) on a structured plan.",
        inputSchema={"type": "object", "properties": {"plan": {"type": "object"}}, "required": ["plan"]},
    ),
    types.Tool(
        name="explain_access_scope",
        description="Explain whether the caller is authorized to see a concept, and why.",
        inputSchema={"type": "object", "properties": {"concept_id": {"type": "string"}}, "required": ["concept_id"]},
    ),
]

_DISPATCH = {
    "resolve_concept": tool_impls.resolve_concept,
    "resolve_metric": tool_impls.resolve_metric,
    "get_metric_definition": tool_impls.get_metric_definition,
    "get_allowed_dimensions": tool_impls.get_allowed_dimensions,
    "resolve_dimension_value": tool_impls.resolve_dimension_value,
    "resolve_hierarchy_node": tool_impls.resolve_hierarchy_node,
    "expand_hierarchy": tool_impls.expand_hierarchy,
    "get_approved_join_path": tool_impls.get_approved_join_path,
    "get_business_rule": tool_impls.get_business_rule,
    "get_authoritative_source": tool_impls.get_authoritative_source,
    "validate_semantic_plan": tool_impls.validate_semantic_plan,
    "explain_access_scope": tool_impls.explain_access_scope,
}


def build_server(toolkit: OntologyToolkit | None = None) -> Server:
    toolkit = toolkit or OntologyToolkit.build()
    server = Server("enterprise-ontology-mcp")

    @server.list_tools()
    async def list_tools() -> list[types.Tool]:
        return TOOL_DEFINITIONS

    @server.call_tool()
    async def call_tool(name: str, arguments: dict, request_context=None) -> list[types.TextContent]:
        if name not in _DISPATCH:
            raise ValueError(f"Unknown tool: {name}")

        # Identity comes from the transport-level headers the Databricks App
        # runtime attaches to the request context — never from `arguments`.
        headers = getattr(request_context, "headers", {}) if request_context else {}
        user_context, _obo = extract_user_context(headers)

        handler = _DISPATCH[name]
        result = await handler(toolkit, user_context=user_context, **arguments)

        import json
        return [types.TextContent(type="text", text=json.dumps(result, default=str))]

    return server


async def run_stdio() -> None:
    """Entry point for local development / testing over stdio transport."""
    import mcp.server.stdio

    server = build_server()
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="enterprise-ontology-mcp",
                server_version="0.1.0",
                capabilities=server.get_capabilities(notification_options=None, experimental_capabilities={}),
            ),
        )


if __name__ == "__main__":
    import asyncio
    asyncio.run(run_stdio())
