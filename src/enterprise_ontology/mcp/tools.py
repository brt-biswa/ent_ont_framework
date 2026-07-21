"""Typed Ontology MCP tools — PRD Sec. 11. Each tool is narrow and typed;
none of them expose arbitrary SQL, arbitrary schema browsing, credentials or
unrestricted physical metadata (Sec. 11, last line). This module holds the
tool implementations; mcp/server.py wires them into an MCP server instance.

Every tool takes an explicit UserContext so permission-aware behavior is
never accidental — there is no ambient/global identity anywhere in this
framework (design principle 19: fail closed).
"""
from __future__ import annotations

from dataclasses import dataclass

from ..models import SemanticPlan, UserContext
from ..repositories.unity_catalog_repository import UnityCatalogOntologyRepository
from ..repositories.lakebase_repository import LakebaseStateRepository
from ..resolution.concept_resolver import ConceptResolver
from ..resolution.context_projector import ContextProjector
from ..dimensions.dimension_resolver import DimensionResolver
from ..dimensions.hierarchy_resolver import HierarchyResolver
from ..relationships.join_path_resolver import JoinPathResolver
from ..metrics.metric_service import MetricService
from ..rules.rule_service import RuleService
from ..security.authz import check_concept_access
from ..planner.semantic_validator import SemanticValidator
from ..cache.l2_lakebase_cache import L2LakebaseCache


@dataclass
class OntologyToolkit:
    """Bundles every service a tool needs. Constructed once per process by
    mcp/server.py and passed to each tool function — keeps the tools
    themselves free of manual dependency wiring."""

    repository: UnityCatalogOntologyRepository
    lakebase: LakebaseStateRepository
    concept_resolver: ConceptResolver
    context_projector: ContextProjector
    dimension_resolver: DimensionResolver
    hierarchy_resolver: HierarchyResolver
    join_path_resolver: JoinPathResolver
    metric_service: MetricService
    rule_service: RuleService
    validator: SemanticValidator

    @classmethod
    def build(cls) -> "OntologyToolkit":
        repository = UnityCatalogOntologyRepository()
        lakebase = LakebaseStateRepository()
        l2_cache = L2LakebaseCache(lakebase)
        metric_service = MetricService(repository)
        return cls(
            repository=repository,
            lakebase=lakebase,
            concept_resolver=ConceptResolver(repository),
            context_projector=ContextProjector(repository, lakebase),
            dimension_resolver=DimensionResolver(repository, l2_cache),
            hierarchy_resolver=HierarchyResolver(repository),
            join_path_resolver=JoinPathResolver(repository),
            metric_service=metric_service,
            rule_service=RuleService(repository),
            validator=SemanticValidator(metric_service),
        )


# ---------------------------------------------------------------------
# 1. resolve_concept
# ---------------------------------------------------------------------
async def resolve_concept(
    toolkit: OntologyToolkit, terms: list[str], user_context: UserContext, domain: str | None = None
) -> dict:
    result = await toolkit.concept_resolver.resolve(terms, domain=domain)
    return {
        "concepts": [c.model_dump(mode="json") for c in result.concepts],
        "unresolved_terms": result.unresolved_terms,
        "ambiguous_terms": {
            k: [c.model_dump(mode="json") for c in v] for k, v in result.ambiguous_terms.items()
        },
        "requires_clarification": result.requires_clarification,
    }


# ---------------------------------------------------------------------
# 2. resolve_metric
# ---------------------------------------------------------------------
async def resolve_metric(
    toolkit: OntologyToolkit, term: str, user_context: UserContext, domain: str | None = None
) -> dict:
    metrics = await toolkit.metric_service.resolve_by_term(term, domain=domain)
    return {"metrics": [m.model_dump(mode="json") for m in metrics]}


# ---------------------------------------------------------------------
# 3. get_metric_definition
# ---------------------------------------------------------------------
async def get_metric_definition(toolkit: OntologyToolkit, metric_id: str, user_context: UserContext) -> dict:
    metric = await toolkit.metric_service.get(metric_id)
    if metric is None:
        return {"found": False}
    return {"found": True, "metric": metric.model_dump(mode="json")}


# ---------------------------------------------------------------------
# 4. get_allowed_dimensions
# ---------------------------------------------------------------------
async def get_allowed_dimensions(toolkit: OntologyToolkit, metric_id: str, user_context: UserContext) -> dict:
    metric = await toolkit.metric_service.get(metric_id)
    if metric is None:
        return {"found": False, "allowed_dimension_ids": []}
    return {"found": True, "allowed_dimension_ids": metric.allowed_dimension_ids}


# ---------------------------------------------------------------------
# 5. resolve_dimension_value
# ---------------------------------------------------------------------
async def resolve_dimension_value(
    toolkit: OntologyToolkit, dimension_id: str, user_text: str, user_context: UserContext
) -> dict:
    return await toolkit.dimension_resolver.resolve(dimension_id, user_text, user_context)


# ---------------------------------------------------------------------
# 6. resolve_hierarchy_node
# ---------------------------------------------------------------------
async def resolve_hierarchy_node(
    toolkit: OntologyToolkit, hierarchy_id: str, canonical_id: str, user_context: UserContext
) -> dict:
    node = await toolkit.hierarchy_resolver.resolve_node(hierarchy_id, canonical_id)
    return {"found": node is not None, "node": node.model_dump(mode="json") if node else None}


# ---------------------------------------------------------------------
# 7. expand_hierarchy
# ---------------------------------------------------------------------
async def expand_hierarchy(
    toolkit: OntologyToolkit, hierarchy_id: str, canonical_id: str, user_context: UserContext,
    include_self: bool = True,
) -> dict:
    nodes = await toolkit.hierarchy_resolver.expand(hierarchy_id, canonical_id, include_self=include_self)
    return {"nodes": [n.model_dump(mode="json") for n in nodes]}


# ---------------------------------------------------------------------
# 8. get_approved_join_path
# ---------------------------------------------------------------------
async def get_approved_join_path(
    toolkit: OntologyToolkit, source_concept_id: str, target_concept_id: str, user_context: UserContext
) -> dict:
    join = await toolkit.join_path_resolver.get_join_path(source_concept_id, target_concept_id)
    return {"found": join is not None, "approved_join_ref": join}


# ---------------------------------------------------------------------
# 9. get_business_rule
# ---------------------------------------------------------------------
async def get_business_rule(toolkit: OntologyToolkit, rule_id: str, user_context: UserContext) -> dict:
    rule = await toolkit.rule_service.get_rule(rule_id)
    return {"found": rule is not None, "rule": rule.model_dump(mode="json") if rule else None}


# ---------------------------------------------------------------------
# 10. get_authoritative_source
# ---------------------------------------------------------------------
async def get_authoritative_source(toolkit: OntologyToolkit, concept_id: str, user_context: UserContext) -> dict:
    rows = toolkit.repository._query(  # noqa: SLF001
        "SELECT * FROM authority_source WHERE concept_id = ? AND status = 'ACTIVE' ORDER BY authority_level ASC",
        (concept_id,),
    )
    return {"sources": rows}


# ---------------------------------------------------------------------
# 11. validate_semantic_plan
# ---------------------------------------------------------------------
async def validate_semantic_plan(
    toolkit: OntologyToolkit, plan: dict, user_context: UserContext
) -> dict:
    semantic_plan = SemanticPlan.model_validate(plan)
    all_concept_ids = list({*semantic_plan.metric_ids, *semantic_plan.dimension_ids})
    context = await toolkit.context_projector.project(all_concept_ids, user_context)
    result = await toolkit.validator.validate(semantic_plan, context, user_context)
    return result.model_dump(mode="json")


# ---------------------------------------------------------------------
# 12. explain_access_scope
# ---------------------------------------------------------------------
async def explain_access_scope(toolkit: OntologyToolkit, concept_id: str, user_context: UserContext) -> dict:
    concepts = await toolkit.repository.resolve_terms([concept_id])
    if not concepts:
        rows = toolkit.repository._query(  # noqa: SLF001
            "SELECT * FROM concept WHERE concept_id = ? AND status = 'ACTIVE'", (concept_id,)
        )
        if not rows:
            return {"found": False}
        from ..models import Concept
        concept = Concept.model_validate(rows[0])
    else:
        concept = concepts[0]

    decision = check_concept_access(concept, user_context)
    return {
        "found": True,
        "concept_id": concept.concept_id,
        "sensitivity": concept.sensitivity.value,
        "discoverability": concept.discoverability.value,
        "is_authorized": decision.is_authorized,
        "reason": decision.reason,
    }
