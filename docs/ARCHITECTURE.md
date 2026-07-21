# Architecture

This document walks the runtime path a single agent request takes through
the framework, and maps every PRD section to the code that implements it.

## Runtime sequence (PRD Sec. 12)

```
User request
    ↓
Request classifier                          (agent-side, out of scope for this framework)
    ↓
Potential concept extraction                 resolution/concept_resolver.py
    ↓
Permission-aware ontology retrieval           resolution/context_projector.py
    ↓  (checks L1 cache/cache/l1_memory_cache.py, then L2 Lakebase/cache/l2_lakebase_cache.py,
    ↓   then Unity Catalog via repositories/unity_catalog_repository.py; drops any concept
    ↓   currently blocked by CRITICAL drift via repositories/lakebase_repository.py)
    ↓
Dimension-value and hierarchy resolution      dimensions/dimension_resolver.py, dimensions/hierarchy_resolver.py
    ↓
Structured semantic planning                  planner/semantic_planner.py  (LLM call, structured output only)
    ↓
Deterministic validation                      planner/semantic_validator.py
    ↓
Query or tool compilation                     compiler/deterministic_compiler.py
    ↓                                          (falls back to compiler/llm_sql_generator.py only when
    ↓                                           the deterministic path can't express the plan)
    ↓
SQL policy gateway (AST validation)           sql_policy/ast_validator.py
    ↓
Execution                                     OBO via security/obo.py + Unity Catalog RBAC/ABAC
    ↓
Audit                                         audit/audit_writer.py -> Lakebase (fast) + Delta (durable)
```

Every one of those steps is available either as a direct Python import
(`from enterprise_ontology.resolution import ConceptResolver`) or as an MCP
tool / REST endpoint — domain teams never reimplement this sequence.

## Two equivalent entry points

- **Ontology MCP server** (`mcp/`, deployed as `apps/ontology_mcp_server`) —
  the 12 typed tools from PRD Sec. 11. Preferred for agent frameworks that
  are already MCP-native.
- **REST API** (`api/`, deployed as `apps/ontology_api`) — the endpoint list
  from PRD Sec. 20. Preferred for simpler HTTP-calling agents or non-Python
  callers.

Both call the exact same service layer (`resolution/`, `dimensions/`,
`planner/`, `compiler/`, `sql_policy/`) — there is no logic duplicated
between them.

## Storage: two systems, two jobs

| | Unity Catalog (`ontology.*`, `audit.*`) | Lakebase (`ontology_state.*`, `audit.*`) |
|---|---|---|
| Role | System of record for governed meaning | Application/operational database |
| Written by | Governance workflow only (change requests) | Every request, at runtime |
| Read pattern | Batch/DDL bootstrap, drift scans | Hot-path reads on every call |
| Durability | Immutable, long retention | TTL'd caches, pruned operational audit |
| DDL | `sql/unity_catalog/` | `sql/lakebase/` |

Concretely: a domain steward's change request lands in
`ontology.change_request` (Delta, permanent). Once approved and activated,
the compiled projection a specific user is allowed to see for a specific
question is cached in `ontology_state.user_projection_cache` (Lakebase,
TTL'd, reconstructable). If Lakebase were wiped tomorrow, nothing would be
lost — every row in it is either a cache of Unity Catalog data or a fast
mirror of a Unity Catalog table.

## Governance & lifecycle (PRD Sec. 22)

```
DRAFT -> DOMAIN_REVIEW -> DATA_REVIEW -> SECURITY_REVIEW -> APPROVED -> ACTIVE -> DEPRECATED -> RETIRED
```

`templates/new_domain_scaffold.py` only ever inserts `DRAFT` rows plus a
`SUBMITTED` change request per concept. No code path in this framework moves
a definition to `ACTIVE` automatically — that is a human decision recorded
in `ontology.approval_history`, surfaced in `apps/ontology_admin_ui`.

## Fail-closed by design

Every authorization check in `security/authz.py` defaults to **deny** when
it can't prove access is allowed — an unresolvable `SecurityScope`, a
missing OBO token where one is required, or `discoverability=HIDDEN` are all
hard denials, never "probably fine." The SQL policy gateway
(`sql_policy/ast_validator.py`) applies the same posture: a SQL parse
failure is a rejection, not a pass-through.

## What this framework deliberately does NOT do

Per PRD Sec. 4 ("out of scope for the first release") and Sec. 32
("anti-patterns"):

- It does not replace Unity Catalog RBAC/ABAC — it adds an ontology-level
  discoverability layer on top and always executes through UC in the end.
- It does not expose arbitrary SQL, arbitrary schema browsing, or
  credentials through the MCP server or API.
- It does not activate inferred ontology changes automatically.
- It does not build one enterprise-wide agent — `ontology.agent_mapping`
  scopes each agent to a bounded set of concepts/metrics.
