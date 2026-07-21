"""RBAC/ABAC enforcement helpers — PRD Sec. 9, design principle 10 ("Unity
Catalog remains the final access-control boundary") and 19 ("authorization
failures fail closed").

This module does NOT replace Unity Catalog grants — a concept passing these
checks still executes through UC RBAC/ABAC at query time (row filters,
column masks) via OBO. What this module adds is the ontology-level
discoverability layer described in Sec. 6.1/6.7: can this caller even be
TOLD this concept/metric/dimension exists, before we ever reach the
warehouse.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from ..models import Concept, DimensionDefinition, SecurityScope, UserContext, Discoverability


@dataclass
class AuthorizationDecision:
    is_authorized: bool
    reason: str
    required_group: str | None = None
    violations: list[str] = field(default_factory=list)


def check_concept_access(concept: Concept, user_context: UserContext) -> AuthorizationDecision:
    if concept.discoverability == Discoverability.HIDDEN:
        return AuthorizationDecision(False, "Concept is HIDDEN — fails closed regardless of group membership")

    if concept.discoverability == Discoverability.OPEN:
        return AuthorizationDecision(True, "OPEN discoverability")

    # REQUEST_ACCESS: caller must carry a matching entitlement group. The
    # required group itself lives on ontology.security_scope, not on the
    # concept row — callers with an application-level SecurityScope lookup
    # should prefer check against that; this fallback denies by default.
    return AuthorizationDecision(
        False,
        "REQUEST_ACCESS discoverability with no matching entitlement group found "
        "— fails closed until a SecurityScope grant is resolved",
    )


def check_concept_access_with_scope(
    concept: Concept, scope: SecurityScope | None, user_context: UserContext
) -> AuthorizationDecision:
    if concept.discoverability == Discoverability.HIDDEN:
        return AuthorizationDecision(False, "Concept is HIDDEN")
    if concept.discoverability == Discoverability.OPEN and scope is None:
        return AuthorizationDecision(True, "OPEN discoverability, no additional scope")

    if scope is None:
        return AuthorizationDecision(False, "No SecurityScope resolved for a non-OPEN concept — fails closed")

    if scope.requires_obo and not user_context.obo_token_present:
        return AuthorizationDecision(
            False, "Scope requires OBO but no OBO token is present on this request", scope.required_group
        )

    if scope.required_group and scope.required_group not in user_context.entitlement_group_ids:
        return AuthorizationDecision(
            False, f"Caller lacks required group '{scope.required_group}'", scope.required_group
        )

    return AuthorizationDecision(True, "Entitlement + OBO requirements satisfied", scope.required_group)


def check_dimension_value_access(
    dimension: DimensionDefinition, scope: SecurityScope | None, user_context: UserContext
) -> AuthorizationDecision:
    if dimension.requires_obo and not user_context.obo_token_present:
        return AuthorizationDecision(
            False, "Dimension requires OBO-scoped resolution but no OBO token present on this request"
        )
    if scope is None:
        return AuthorizationDecision(True, "No additional security scope on this dimension")
    if scope.requires_obo and not user_context.obo_token_present:
        return AuthorizationDecision(
            False, "Scope requires OBO but no OBO token is present on this request", scope.required_group
        )
    if scope.required_group and scope.required_group not in user_context.entitlement_group_ids:
        return AuthorizationDecision(
            False, f"Caller lacks required group '{scope.required_group}'", scope.required_group
        )
    return AuthorizationDecision(True, "Entitlement + OBO requirements satisfied", scope.required_group)
