"""Engineering interfaces from PRD Sec. 28 — every concrete implementation
(Unity Catalog today, potentially a graph DB later per Sec. 3 "knowledge graph
is optional") must satisfy these Protocols so callers never depend on storage
technology directly."""
from __future__ import annotations
from typing import Protocol, Any

from ..models import (
    Concept, OntologyContext, UserContext, SemanticPlan, PlanValidationResult,
)


class OntologyRepositoryProtocol(Protocol):
    async def resolve_terms(self, terms: list[str], domain: str | None = None) -> list[Concept]: ...

    async def get_context(
        self, concept_ids: list[str], user_context: UserContext
    ) -> OntologyContext: ...


class DimensionResolverProtocol(Protocol):
    async def resolve(
        self, dimension_id: str, user_text: str, user_context: UserContext
    ) -> dict[str, Any]: ...


class SemanticPlannerProtocol(Protocol):
    async def plan(self, question: str, context: OntologyContext) -> SemanticPlan: ...


class SemanticValidatorProtocol(Protocol):
    async def validate(
        self, plan: SemanticPlan, context: OntologyContext, user_context: UserContext
    ) -> PlanValidationResult: ...


class QueryCompilerProtocol(Protocol):
    async def compile(self, plan: SemanticPlan, context: OntologyContext) -> str: ...


class SQLPolicyGatewayProtocol(Protocol):
    async def validate(self, query: str, user_context: UserContext) -> bool: ...
