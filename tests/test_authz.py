"""Tests for security/authz.py — design principle 19: fail closed."""
from enterprise_ontology.security.authz import check_concept_access, check_concept_access_with_scope
from enterprise_ontology.models import Discoverability, SecurityScope, Sensitivity
import datetime as dt


def test_hidden_concept_always_denied(net_revenue_concept, user_context):
    net_revenue_concept.discoverability = Discoverability.HIDDEN
    decision = check_concept_access(net_revenue_concept, user_context)
    assert not decision.is_authorized


def test_open_concept_always_allowed(net_revenue_concept, user_context):
    net_revenue_concept.discoverability = Discoverability.OPEN
    decision = check_concept_access(net_revenue_concept, user_context)
    assert decision.is_authorized


def test_request_access_without_scope_fails_closed(net_revenue_concept, user_context):
    net_revenue_concept.discoverability = Discoverability.REQUEST_ACCESS
    decision = check_concept_access(net_revenue_concept, user_context)
    assert not decision.is_authorized  # no SecurityScope resolved -> deny, not "probably fine"


def test_scope_with_matching_group_is_authorized(net_revenue_concept, user_context, today):
    scope = SecurityScope(
        scope_id="scope-1", concept_id=net_revenue_concept.concept_id,
        sensitivity=Sensitivity.CONFIDENTIAL, required_group="finance-analysts",
        owner="finance-data-eng@yourco.com", effective_from=today, status="ACTIVE",
    )
    decision = check_concept_access_with_scope(net_revenue_concept, scope, user_context)
    assert decision.is_authorized


def test_scope_with_nonmatching_group_is_denied(net_revenue_concept, user_context, today):
    scope = SecurityScope(
        scope_id="scope-1", concept_id=net_revenue_concept.concept_id,
        sensitivity=Sensitivity.RESTRICTED, required_group="legal-team-only",
        owner="finance-data-eng@yourco.com", effective_from=today, status="ACTIVE",
    )
    decision = check_concept_access_with_scope(net_revenue_concept, scope, user_context)
    assert not decision.is_authorized


def test_obo_required_but_absent_is_denied(net_revenue_concept, user_context, today):
    scope = SecurityScope(
        scope_id="scope-1", concept_id=net_revenue_concept.concept_id,
        sensitivity=Sensitivity.RESTRICTED, requires_obo=True,
        owner="finance-data-eng@yourco.com", effective_from=today, status="ACTIVE",
    )
    assert user_context.obo_token_present is False
    decision = check_concept_access_with_scope(net_revenue_concept, scope, user_context)
    assert not decision.is_authorized
