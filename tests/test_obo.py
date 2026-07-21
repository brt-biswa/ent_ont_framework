"""Tests for security/obo.py — tokens must never leak into repr/str/logs."""
import pytest

from enterprise_ontology.security.obo import OboTokenHandle, extract_user_context


def test_obo_handle_never_reveals_token_in_repr():
    handle = OboTokenHandle("super-secret-token-value")
    assert "super-secret-token-value" not in repr(handle)
    assert "super-secret-token-value" not in str(handle)
    assert handle.reveal() == "super-secret-token-value"


def test_extract_user_context_requires_trusted_header():
    with pytest.raises(PermissionError):
        extract_user_context({})  # no X-Forwarded-Email -> fail closed


def test_extract_user_context_parses_groups_and_obo():
    headers = {
        "X-Forwarded-Email": "jane.doe@yourco.com",
        "X-Forwarded-Groups": "finance-analysts, finance-readers",
        "X-Forwarded-Access-Token": "abc123",
    }
    user_context, obo = extract_user_context(headers, environment="test")
    assert user_context.principal_id == "jane.doe@yourco.com"
    assert user_context.entitlement_group_ids == ["finance-analysts", "finance-readers"]
    assert user_context.obo_token_present is True
    assert obo is not None
    assert obo.reveal() == "abc123"


def test_client_supplied_user_id_header_is_ignored():
    """A caller cannot impersonate someone else via an untrusted header —
    only the platform-injected X-Forwarded-* headers are trusted."""
    headers = {"X-Forwarded-Email": "real.user@yourco.com", "X-User-Id": "attacker@evil.com"}
    user_context, _ = extract_user_context(headers)
    assert user_context.principal_id == "real.user@yourco.com"
