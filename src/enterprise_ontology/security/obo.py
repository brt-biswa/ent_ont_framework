"""On-Behalf-Of (OBO) token handling — PRD Sec. 9.

Hard rule: OBO tokens are NEVER persisted to memory caches, Lakebase, Delta,
traces or logs (PRD Sec. 9, last line; Sec. 19; Sec. 25). `OboTokenHandle`
exists specifically so the raw token value can never accidentally leak into
a Pydantic model that later gets `.model_dump()`-ed into a cache row or an
audit event — it is deliberately NOT a Pydantic model and does not implement
`__repr__`/`__str__` with the token value.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..models import UserContext


@dataclass(frozen=True)
class OboTokenHandle:
    """Opaque holder for a per-request OBO token. Pass this object around
    (e.g. into a Databricks SQL connector call that executes AS the user);
    never extract `.value` except at the point of use, and never put it on
    a model, in a log line, or in a cache key."""

    _value: str

    def __repr__(self) -> str:  # defense in depth against accidental logging
        return "OboTokenHandle(***redacted***)"

    __str__ = __repr__

    def reveal(self) -> str:
        """Only call this immediately before passing to the downstream
        Databricks API call that needs it."""
        return self._value


def extract_user_context(headers: dict[str, str], environment: str = "dev") -> tuple[UserContext, OboTokenHandle | None]:
    """Identity must come from trusted authentication context, never a
    client-supplied payload (PRD Sec. 19). In a Databricks App, the platform
    injects `X-Forwarded-Email` / `X-Forwarded-Access-Token` after verifying
    the caller — this function trusts those headers because the App runtime
    itself terminates auth; it must NEVER trust an `X-User-Id`-style header
    supplied directly by a caller of a public endpoint.
    """
    principal_id = headers.get("X-Forwarded-Email") or headers.get("X-Forwarded-User", "")
    if not principal_id:
        raise PermissionError("No trusted identity header present — failing closed (design principle 19)")

    group_header = headers.get("X-Forwarded-Groups", "")
    groups = [g.strip() for g in group_header.split(",") if g.strip()]

    obo_raw = headers.get("X-Forwarded-Access-Token")
    obo = OboTokenHandle(obo_raw) if obo_raw else None

    user_context = UserContext(
        principal_id=principal_id,
        entitlement_group_ids=groups,
        obo_token_present=obo is not None,
        environment=environment,
    )
    return user_context, obo
