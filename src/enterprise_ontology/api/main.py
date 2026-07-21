"""Ontology REST API — PRD Sec. 20 endpoint list. This is one of two
equally-supported entry points into the framework (the other being the MCP
server in mcp/); domain teams pick whichever fits their agent runtime.

Deployed as a Databricks App (apps/ontology_api/). Every endpoint resolves
UserContext from trusted headers (api/deps.py) and every mutating endpoint
(change-request creation) goes through the governance workflow — there is no
endpoint that lets a caller directly edit ontology.concept or any other
registry table.
"""
from __future__ import annotations

import logging
import uuid

from fastapi import Depends, FastAPI, HTTPException

from ..models import UserContext
from ..resolution.concept_resolver import ConceptResolver
from ..resolution.context_projector import ContextProjector
from ..dimensions.dimension_resolver import DimensionResolver
from ..dimensions.hierarchy_resolver import HierarchyResolver
from ..relationships.join_path_resolver import JoinPathResolver
from ..planner.semantic_validator import SemanticValidator
from ..repositories.unity_catalog_repository import UnityCatalogOntologyRepository
from ..repositories.lakebase_repository import LakebaseStateRepository
from ..audit.audit_writer import AuditWriter
from . import deps
from .schemas import (
    ResolveRequest, ResolveDimensionRequest, ResolveHierarchyRequest,
    JoinPathRequest, ValidatePlanRequest, ChangeRequestCreate,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Enterprise Ontology API",
    description="Governed meaning layer for agentic AI — PRD Sec. 20 endpoints",
    version="0.1.0",
)


@app.on_event("startup")
async def _startup() -> None:
    await deps.get_lakebase().connect()


@app.on_event("shutdown")
async def _shutdown() -> None:
    await deps.get_lakebase().close()


# GET /api/v1/ontology/concepts/{concept_id}
@app.get("/api/v1/ontology/concepts/{concept_id}")
async def get_concept(
    concept_id: str,
    user_context: UserContext = Depends(deps.get_user_context),
    resolver: ConceptResolver = Depends(deps.get_concept_resolver),
):
    result = await resolver.resolve([concept_id])
    if not result.concepts:
        raise HTTPException(status_code=404, detail="Concept not found or not authorized")
    return result.concepts[0].model_dump(mode="json")


# POST /api/v1/ontology/resolve
@app.post("/api/v1/ontology/resolve")
async def resolve(
    body: ResolveRequest,
    user_context: UserContext = Depends(deps.get_user_context),
    resolver: ConceptResolver = Depends(deps.get_concept_resolver),
):
    result = await resolver.resolve(body.terms, domain=body.domain)
    return {
        "concepts": [c.model_dump(mode="json") for c in result.concepts],
        "unresolved_terms": result.unresolved_terms,
        "requires_clarification": result.requires_clarification,
    }


# POST /api/v1/ontology/resolve-dimension
@app.post("/api/v1/ontology/resolve-dimension")
async def resolve_dimension(
    body: ResolveDimensionRequest,
    user_context: UserContext = Depends(deps.get_user_context),
    resolver: DimensionResolver = Depends(deps.get_dimension_resolver),
):
    return await resolver.resolve(body.dimension_id, body.user_text, user_context)


# POST /api/v1/ontology/resolve-hierarchy
@app.post("/api/v1/ontology/resolve-hierarchy")
async def resolve_hierarchy(
    body: ResolveHierarchyRequest,
    user_context: UserContext = Depends(deps.get_user_context),
    resolver: HierarchyResolver = Depends(deps.get_hierarchy_resolver),
):
    nodes = await resolver.expand(body.hierarchy_id, body.canonical_id, include_self=body.include_self)
    return {"nodes": [n.model_dump(mode="json") for n in nodes]}


# POST /api/v1/ontology/get-join-path
@app.post("/api/v1/ontology/get-join-path")
async def get_join_path(
    body: JoinPathRequest,
    user_context: UserContext = Depends(deps.get_user_context),
    resolver: JoinPathResolver = Depends(deps.get_join_path_resolver),
):
    join = await resolver.get_join_path(body.source_concept_id, body.target_concept_id)
    if join is None:
        raise HTTPException(status_code=404, detail="No approved join path between these concepts")
    return {"approved_join_ref": join}


# POST /api/v1/ontology/validate-plan
@app.post("/api/v1/ontology/validate-plan")
async def validate_plan(
    body: ValidatePlanRequest,
    user_context: UserContext = Depends(deps.get_user_context),
    projector: ContextProjector = Depends(deps.get_context_projector),
    validator: SemanticValidator = Depends(deps.get_validator),
):
    all_concept_ids = list({*body.plan.metric_ids, *body.plan.dimension_ids})
    context = await projector.project(all_concept_ids, user_context)
    result = await validator.validate(body.plan, context, user_context)
    return result.model_dump(mode="json")


# GET /api/v1/ontology/metrics/{metric_id}
@app.get("/api/v1/ontology/metrics/{metric_id}")
async def get_metric(
    metric_id: str,
    user_context: UserContext = Depends(deps.get_user_context),
    repo: UnityCatalogOntologyRepository = Depends(deps.get_repository),
):
    from ..metrics.metric_service import MetricService
    metric = await MetricService(repo).get(metric_id)
    if metric is None:
        raise HTTPException(status_code=404, detail="Metric not found or not certified")
    return metric.model_dump(mode="json")


# GET /api/v1/ontology/versions/active
@app.get("/api/v1/ontology/versions/active")
async def get_active_version(lakebase: LakebaseStateRepository = Depends(deps.get_lakebase)):
    version = await lakebase.get_active_version()
    if version is None:
        raise HTTPException(status_code=404, detail="No active ontology version set")
    return version


# POST /api/v1/ontology/change-requests
@app.post("/api/v1/ontology/change-requests", status_code=201)
async def create_change_request(
    body: ChangeRequestCreate,
    user_context: UserContext = Depends(deps.get_user_context),
    repo: UnityCatalogOntologyRepository = Depends(deps.get_repository),
    lakebase: LakebaseStateRepository = Depends(deps.get_lakebase),
):
    """Submits a change request into the governance workflow (design
    principle 12: "new ontology elements require review and approval").
    This endpoint never mutates ontology.concept or any other registry table
    directly — it only enqueues a request for the domain/data/security review
    chain (PRD Sec. 22)."""
    change_request_id = str(uuid.uuid4())
    repo._query(  # noqa: SLF001
        """INSERT INTO change_request
            (change_request_id, concept_id, business_reason, old_definition, new_definition,
             effective_date, migration_plan, stage, submitted_by)
           VALUES (?, ?, ?, ?, ?, ?, ?, 'SUBMITTED', ?)""",
        (change_request_id, body.concept_id, body.business_reason, body.old_definition,
         body.new_definition, body.effective_date, body.migration_plan, user_context.principal_id),
    )
    await lakebase.enqueue_change_workflow(change_request_id, stage="SUBMITTED")

    audit = AuditWriter(lakebase)
    await audit.write(
        "ontology_change",
        trace_id=change_request_id,
        payload={
            "change_request_id": change_request_id,
            "stage": "SUBMITTED",
            "actor": user_context.principal_id,
        },
    )
    return {"change_request_id": change_request_id, "stage": "SUBMITTED"}


# GET /api/v1/ontology/drift
@app.get("/api/v1/ontology/drift")
async def get_drift(lakebase: LakebaseStateRepository = Depends(deps.get_lakebase)):
    blocking = await lakebase.get_blocking_concepts()
    return {"blocking_concept_ids": blocking}


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}
