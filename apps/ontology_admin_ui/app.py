"""Governance admin UI — PRD Sec. 22 (change-request workflow), Sec. 23
(drift dashboard), Epic 8 ("governance and administration"). Reads through
the framework's own repositories, never raw SQL against Unity Catalog/
Lakebase from this file — the point of the framework is that this app is
just another consumer of it, same as any domain team's agent.

Deployed once by the platform team; reviewers across every domain use this
one instance rather than each domain building its own approval tooling.
"""
from __future__ import annotations

import asyncio

import pandas as pd
import streamlit as st

from enterprise_ontology.config import get_settings
from enterprise_ontology.repositories.unity_catalog_repository import UnityCatalogOntologyRepository
from enterprise_ontology.repositories.lakebase_repository import LakebaseStateRepository

st.set_page_config(page_title="Enterprise Ontology — Governance", layout="wide")


@st.cache_resource
def _repo() -> UnityCatalogOntologyRepository:
    return UnityCatalogOntologyRepository(get_settings())


@st.cache_resource
def _lakebase() -> LakebaseStateRepository:
    lb = LakebaseStateRepository(get_settings())
    asyncio.run(lb.connect())
    return lb


def _run(coro):
    return asyncio.run(coro)


st.title("Enterprise Ontology Framework — Governance")

tab_inbox, tab_drift, tab_domains, tab_versions = st.tabs(
    ["Reviewer Inbox", "Drift Dashboard", "Domain Registry", "Ontology Versions"]
)

with tab_inbox:
    st.subheader("Pending change requests")
    st.caption(
        "Mirrors ontology.change_request via the fast Lakebase change_workflow "
        "table (design principle 12: every change requires review and approval)."
    )
    pending = _run(_lakebase().list_pending_change_workflow())
    if pending:
        df = pd.DataFrame(pending)
        st.dataframe(df, use_container_width=True)
        selected = st.selectbox("Select a change request to act on", [""] + [p["change_request_id"] for p in pending])
        if selected:
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("Advance to next stage"):
                    st.info("Wire this button to POST /api/v1/ontology/change-requests/{id}/advance "
                            "on the ontology_api app, or a direct approval_history insert with the "
                            "reviewing group's identity — left as an integration point.")
            with col2:
                if st.button("Reject"):
                    st.info("Wire to the same endpoint with decision=REJECTED.")
            with col3:
                st.write("")
    else:
        st.info("No pending change requests.")

with tab_drift:
    st.subheader("Blocking drift (concepts currently unavailable to agents)")
    blocking = _run(_lakebase().get_blocking_concepts())
    if blocking:
        st.error(f"{len(blocking)} concept(s) currently blocked by CRITICAL drift:")
        st.write(blocking)
    else:
        st.success("No concepts are currently blocked by critical drift.")
    st.caption(
        "Full drift history: ontology.drift_event (Unity Catalog). This view reads the fast "
        "ontology_state.drift_status mirror updated by the hourly drift-detection job."
    )

with tab_domains:
    st.subheader("Onboarded domains")
    rows = _repo()._query("SELECT * FROM domain_registry ORDER BY domain")  # noqa: SLF001
    if rows:
        st.dataframe(pd.DataFrame(rows), use_container_width=True)
    else:
        st.info(
            "No domains onboarded yet. Run `python templates/new_domain_scaffold.py "
            "--domain <name> --owner <team>` to onboard the first one."
        )

with tab_versions:
    st.subheader("Ontology version history")
    active = _run(_lakebase().get_active_version())
    if active:
        st.metric("Active version", active["label"])
    rows = _repo()._query("SELECT * FROM version ORDER BY created_at DESC")  # noqa: SLF001
    if rows:
        st.dataframe(pd.DataFrame(rows), use_container_width=True)
