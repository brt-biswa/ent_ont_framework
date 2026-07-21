"""Databricks App entrypoint. Thin re-export so `uvicorn app:app` (per
app.yaml) finds the FastAPI instance built in the shared framework package —
the app itself has no business logic; it all lives in
enterprise_ontology.api.main so it stays unit-testable outside a deployed App.
"""
from enterprise_ontology.api.main import app  # noqa: F401
