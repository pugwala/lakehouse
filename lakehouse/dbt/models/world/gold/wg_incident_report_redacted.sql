{{ config(alias='incident_report_redacted', materialized='incremental', incremental_strategy='delete+insert', unique_key='incident_report_id', on_schema_change='fail',
          tags=['world_monthly']) }}
-- The incident reports with every personal detail replaced, for search (the MCP server's search_incident_reports,
-- through Cube). Each span the mention key marks (mention_key/incident_report, var world_root) becomes its kind in
-- capitals: [PERSON NAME], [ALIAS], [SID], [BIRTH DATE] or [PHONE]; every other character is kept. Places count
-- characters from 0, end excluded, and hold in silver because silver keeps the narrative as written. No author column:
-- the author is a person. The lab redacts by the key, the world's own record of where each detail is; a real
-- platform would use a detector, which is what the text sessions teach.
WITH reports AS (
    SELECT incident_report_id, incident_id, report_kind, filed_at, incident_month, narrative
    FROM {{ ref('ws_incident_report') }}
    WHERE {{ w_in_window('incident_month') }}
),
mentions AS (
    SELECT k.incident_report_id, k.start_pos, k.end_pos, k.kind,
           coalesce(lag(k.end_pos) OVER (PARTITION BY k.incident_report_id ORDER BY k.start_pos), 0) AS previous_end
    FROM read_parquet('{{ var("world_root") }}/mention_key/incident_report/*.parquet') k
    WHERE k.incident_report_id IN (SELECT incident_report_id FROM reports)
),
pieces AS (
    -- The text before each mention, then the mention's label ...
    SELECT m.incident_report_id, m.start_pos AS place,
           substring(r.narrative, m.previous_end + 1, m.start_pos - m.previous_end)
           || '[' || upper(replace(m.kind, '_', ' ')) || ']' AS piece
    FROM mentions m
    JOIN reports r USING (incident_report_id)
    UNION ALL
    -- ... and the text after the last one (the whole narrative when there's none).
    SELECT r.incident_report_id, 2147483647 AS place, substring(r.narrative, coalesce(max(m.end_pos), 0) + 1) AS piece
    FROM reports r
    LEFT JOIN mentions m USING (incident_report_id)
    GROUP BY r.incident_report_id, r.narrative
),
redacted AS (
    SELECT incident_report_id, string_agg(piece, '' ORDER BY place) AS narrative
    FROM pieces
    GROUP BY incident_report_id
)
SELECT r.incident_report_id, r.incident_id, r.report_kind, r.filed_at, r.incident_month, x.narrative
FROM reports r
JOIN redacted x USING (incident_report_id)
