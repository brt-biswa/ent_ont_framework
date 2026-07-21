-- =============================================================================
-- Maintenance: TTL cleanup + audit retention.
--
-- Lakebase caches are TTL'd at the row level (expires_at) but Postgres does
-- not evict rows on its own — a scheduled job (jobs/cache_warm_job.py also
-- performs cleanup) should call these functions periodically. Kept as plain
-- SQL functions so they can be invoked from a job, from psql, or from a
-- pg_cron extension if enabled on the Lakebase instance.
-- =============================================================================

CREATE OR REPLACE FUNCTION ontology_state.purge_expired_cache_rows()
RETURNS TABLE(table_name TEXT, rows_deleted BIGINT) AS $$
DECLARE
    deleted_snapshot BIGINT;
    deleted_projection BIGINT;
    deleted_dimension BIGINT;
BEGIN
    DELETE FROM ontology_state.compiled_snapshot WHERE expires_at <= now();
    GET DIAGNOSTICS deleted_snapshot = ROW_COUNT;

    DELETE FROM ontology_state.user_projection_cache WHERE expires_at <= now();
    GET DIAGNOSTICS deleted_projection = ROW_COUNT;

    DELETE FROM ontology_state.dimension_resolution_cache WHERE expires_at <= now();
    GET DIAGNOSTICS deleted_dimension = ROW_COUNT;

    RETURN QUERY
        SELECT 'compiled_snapshot'::TEXT, deleted_snapshot
        UNION ALL SELECT 'user_projection_cache'::TEXT, deleted_projection
        UNION ALL SELECT 'dimension_resolution_cache'::TEXT, deleted_dimension;
END;
$$ LANGUAGE plpgsql;

-- Operational audit rows older than 90 days are pruned from Lakebase — the
-- Delta copy (audit.* in Unity Catalog) is the durable, long-retention record.
CREATE OR REPLACE FUNCTION audit.purge_old_operational_audit(retention_days INT DEFAULT 90)
RETURNS TABLE(table_name TEXT, rows_deleted BIGINT) AS $$
DECLARE
    cutoff TIMESTAMPTZ := now() - (retention_days || ' days')::INTERVAL;
    d BIGINT;
BEGIN
    DELETE FROM audit.ontology_resolution WHERE created_at < cutoff; GET DIAGNOSTICS d = ROW_COUNT;
    RETURN QUERY SELECT 'ontology_resolution'::TEXT, d;

    DELETE FROM audit.semantic_plan WHERE created_at < cutoff; GET DIAGNOSTICS d = ROW_COUNT;
    RETURN QUERY SELECT 'semantic_plan'::TEXT, d;

    DELETE FROM audit.plan_validation WHERE created_at < cutoff; GET DIAGNOSTICS d = ROW_COUNT;
    RETURN QUERY SELECT 'plan_validation'::TEXT, d;

    DELETE FROM audit.dimension_resolution WHERE created_at < cutoff; GET DIAGNOSTICS d = ROW_COUNT;
    RETURN QUERY SELECT 'dimension_resolution'::TEXT, d;

    DELETE FROM audit.sql_generation WHERE created_at < cutoff; GET DIAGNOSTICS d = ROW_COUNT;
    RETURN QUERY SELECT 'sql_generation'::TEXT, d;

    DELETE FROM audit.sql_validation WHERE created_at < cutoff; GET DIAGNOSTICS d = ROW_COUNT;
    RETURN QUERY SELECT 'sql_validation'::TEXT, d;

    DELETE FROM audit.ontology_change WHERE created_at < cutoff; GET DIAGNOSTICS d = ROW_COUNT;
    RETURN QUERY SELECT 'ontology_change'::TEXT, d;

    DELETE FROM audit.mapping_drift WHERE created_at < cutoff; GET DIAGNOSTICS d = ROW_COUNT;
    RETURN QUERY SELECT 'mapping_drift'::TEXT, d;
END;
$$ LANGUAGE plpgsql;
