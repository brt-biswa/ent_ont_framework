"""Enterprise Ontology Framework for Agentic AI.

A Databricks-native, reusable governed meaning layer. See the repository
README for the full architecture; this package is organized as:

  models/        canonical Pydantic data model (mirrors the UC Delta schema)
  repositories/  Unity Catalog + Lakebase data access
  resolution/    concept & synonym resolution, permission-aware context projection
  dimensions/    governed dimension & hierarchy value resolution
  relationships/ approved join-path resolution
  metrics/       certified metric service
  rules/         business rule service
  mappings/      physical asset / document mapping service
  security/      OBO context + RBAC/ABAC enforcement
  planner/       LLM semantic planner + deterministic validator
  compiler/      deterministic query compiler + constrained SQL fallback
  sql_policy/    SQL AST allow/deny-list validator
  mcp/           reusable Ontology MCP server (typed tools)
  cache/         L1 in-memory + L2 Lakebase caching
  audit/         audit-trail writer
  evaluation/    gold-question evaluation harness
  drift/         ontology / mapping / schema drift detection
  api/           REST API (FastAPI)
  jobs/          scheduled job entry points (bootstrap, drift, cache warm, evaluation)
"""

__version__ = "0.1.0"
