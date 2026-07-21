-- =============================================================================
-- ontology_state.change_workflow
--
-- Low-latency workflow queue mirroring ontology.change_request (Unity
-- Catalog, system of record). The admin UI (apps/ontology_admin_ui) polls
-- this table to render reviewer inboxes without round-tripping the SQL
-- warehouse on every page load. Stage values follow the same state machine
-- as ChangeRequestStage (models/enums.py) and ontology.change_request.stage.
-- =============================================================================

CREATE TABLE IF NOT EXISTS ontology_state.change_workflow (
    change_request_id     TEXT PRIMARY KEY,
    stage                    TEXT NOT NULL CHECK (stage IN (
                                'SUBMITTED', 'DOMAIN_REVIEW', 'DATA_REVIEW',
                                'SECURITY_REVIEW', 'APPROVED', 'REJECTED', 'IMPLEMENTED'
                             )),
    assignee_group            TEXT,
    priority                    SMALLINT NOT NULL DEFAULT 3 CHECK (priority BETWEEN 1 AND 5),
    updated_at                  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_change_workflow_stage
    ON ontology_state.change_workflow (stage, updated_at);

CREATE INDEX IF NOT EXISTS ix_change_workflow_assignee
    ON ontology_state.change_workflow (assignee_group)
    WHERE stage NOT IN ('APPROVED', 'REJECTED', 'IMPLEMENTED');

COMMENT ON TABLE ontology_state.change_workflow IS
  'Reviewer-inbox mirror of ontology.change_request.stage for fast admin-UI '
  'reads. Unity Catalog ontology.change_request + ontology.approval_history '
  'remain the audited system of record.';
