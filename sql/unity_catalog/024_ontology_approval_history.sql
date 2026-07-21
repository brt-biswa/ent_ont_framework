CREATE TABLE IF NOT EXISTS ${catalog}.ontology.approval_history (
    approval_id           STRING NOT NULL,
    change_request_id        STRING NOT NULL,
    stage                        STRING NOT NULL,
    approver                        STRING NOT NULL,
    decision                           STRING NOT NULL COMMENT 'APPROVED|REJECTED|CHANGES_REQUESTED',
    comment                                STRING,
    decided_at                               TIMESTAMP NOT NULL DEFAULT current_timestamp()
)
USING DELTA
TBLPROPERTIES ('delta.enableChangeDataFeed' = 'true', 'delta.columnMapping.mode' = 'name')
COMMENT 'Append-only approval decisions per change request stage — the audit trail for governance.';

ALTER TABLE ${catalog}.ontology.approval_history ADD CONSTRAINT pk_approval_history PRIMARY KEY (approval_id);
ALTER TABLE ${catalog}.ontology.approval_history ADD CONSTRAINT fk_approval_history_cr FOREIGN KEY (change_request_id) REFERENCES ${catalog}.ontology.change_request (change_request_id);
