-- Convenience wrapper for psql: \i 999_run_all.sql
-- (the bootstrap_lakebase job applies the same files programmatically in order)
\i 001_create_database_schema.sql
\i 002_active_version.sql
\i 003_compiled_snapshot.sql
\i 004_user_projection_cache.sql
\i 005_dimension_resolution_cache.sql
\i 006_change_workflow.sql
\i 007_drift_status.sql
\i 008_audit_tables.sql
\i 009_maintenance.sql
