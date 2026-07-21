"""FastAPI dependencies — trusted-header identity extraction, service
singletons. Kept separate from main.py so tests can override individual
dependencies (e.g. swap in a fake UserContext) without booting the whole app.
"""
from __future__ import annotations

from functools import lru_cache

from fastapi import Depends, Request

from ..config import get_settings
from ..models import UserContext
from ..repositories.unity_catalog_repository import UnityCatalogOntologyRepository
from ..repositories.lakebase_repository import LakebaseStateRepository
from ..resolution.concept_resolver import ConceptResolver
from ..resolution.context_projector import ContextProjector
from ..dimensions.dimension_resolver import DimensionResolver
from ..dimensions.hierarchy_resolver import HierarchyResolver
from ..relationships.join_path_resolver import JoinPathResolver
from ..metrics.metric_service import MetricService
from ..planner.semantic_validator import SemanticValidator
from ..cache.l2_lakebase_cache import L2LakebaseCache
from ..security.obo import extract_user_context


@lru_cache
def get_repository() -> UnityCatalogOntologyRepository:
    return UnityCatalogOntologyRepository(get_settings())


@lru_cache
def get_lakebase() -> LakebaseStateRepository:
    return LakebaseStateRepository(get_settings())


def get_concept_resolver(repo: UnityCatalogOntologyRepository = Depends(get_repository)) -> ConceptResolver:
    return ConceptResolver(repo)


def get_context_projector(
    repo: UnityCatalogOntologyRepository = Depends(get_repository),
    lakebase: LakebaseStateRepository = Depends(get_lakebase),
) -> ContextProjector:
    return ContextProjector(repo, lakebase)


def get_dimension_resolver(
    repo: UnityCatalogOntologyRepository = Depends(get_repository),
    lakebase: LakebaseStateRepository = Depends(get_lakebase),
) -> DimensionResolver:
    return DimensionResolver(repo, L2LakebaseCache(lakebase))


def get_hierarchy_resolver(repo: UnityCatalogOntologyRepository = Depends(get_repository)) -> HierarchyResolver:
    return HierarchyResolver(repo)


def get_join_path_resolver(repo: UnityCatalogOntologyRepository = Depends(get_repository)) -> JoinPathResolver:
    return JoinPathResolver(repo)


def get_validator(repo: UnityCatalogOntologyRepository = Depends(get_repository)) -> SemanticValidator:
    return SemanticValidator(MetricService(repo))


def get_user_context(request: Request) -> UserContext:
    """Identity comes from trusted App-runtime-injected headers only (PRD
    Sec. 19) — fails closed with a 401-equivalent PermissionError if absent."""
    settings = get_settings()
    user_context, _obo = extract_user_context(dict(request.headers), environment=settings.environment)
    return user_context
