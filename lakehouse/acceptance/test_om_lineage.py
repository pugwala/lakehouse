"""Acceptance test for lineage in OpenMetadata: om_sync.py publishes dbt's table-to-table lineage.

    docker compose --profile core exec -T jupyter pytest -q lakehouse/acceptance/test_om_lineage.py

dbt knows what every model is built from (the manifest's parent_map). om_sync.py makes OpenMetadata hold the same
thing, one edge per parent, marked as dbt lineage, so the catalog's lineage view shows it and the MCP server's lineage
tool can read it as the read-only mcp-reader. An edge dbt no longer has is removed. The expected edges come from the
manifest itself, never from OpenMetadata.
"""
import json
import subprocess
from pathlib import Path

import pytest

from lakehouse import lake
from test_om_sync import OM, get, om  # noqa: F401  (om is a fixture)

LAKEHOUSE = Path(__file__).resolve().parents[1]
MANIFEST = LAKEHOUSE / "dbt" / "target" / "manifest.json"
FQN = "lakehouse.lake."
SYNC = ["python", str(LAKEHOUSE / "openmetadata" / "om_sync.py")]


def lake_tables():
    """Every schema.table in the lake, views included (world_silver.exceptions and mart_readiness.period_readiness
    are views dbt builds)."""
    con = lake.lake_ro_connect()
    try:
        return {f"{s}.{t}" for s, t in con.execute(
            "SELECT table_schema, table_name FROM information_schema.tables WHERE table_catalog = 'lake' "
            "AND table_schema NOT IN ('information_schema', 'pg_catalog')").fetchall()}
    finally:
        con.close()


def dbt_edges():
    """{(parent, child)} from the manifest: every model's direct parents (models, seeds, snapshots, sources), named as
    in the lake, where both ends are lake tables."""
    m = json.loads(MANIFEST.read_text())
    names = {uid: f"{n['schema']}.{n['alias']}" for uid, n in m["nodes"].items()
             if n.get("resource_type") in ("model", "seed", "snapshot")}
    names |= {uid: f"{n['schema']}.{n['identifier']}" for uid, n in m["sources"].items()}
    tables = lake_tables()
    return {(names[p], names[c]) for c, parents in m["parent_map"].items() if c in names
            for p in parents if p in names and names[p] in tables and names[c] in tables and names[p] != names[c]}


def om_upstream(om, table):
    """{(parent, table)} for the upstream edges OpenMetadata holds into one table, and the edges themselves."""
    got = get(om, f"lineage/table/name/{FQN}{table}", upstreamDepth=1, downstreamDepth=0)
    fqn = {n["id"]: n["fullyQualifiedName"].removeprefix(FQN) for n in got["nodes"]} | {got["entity"]["id"]: table}
    return {(fqn[e["fromEntity"]], fqn[e["toEntity"]]) for e in got["upstreamEdges"]}, got["upstreamEdges"]


@pytest.fixture(scope="module")
def expected():
    """dbt's edges, and the tables that have any parent."""
    edges = dbt_edges()
    return edges, sorted({c for _, c in edges})


def test_dbt_has_lineage_to_publish(expected):
    """The manifest gives over a hundred edges (120 on 2026-11-04), the world's silver-to-gold among them, and the
    views: every world silver table feeds world_silver.exceptions."""
    edges, children = expected
    assert len(edges) >= 110
    assert ("world_silver.incident_report", "world_silver.exceptions") in edges
    assert ("world_silver.incident_report", "world_gold.incident_report_redacted") in edges
    assert ("world_silver.incident", "world_gold.fct_incident") in edges


def test_every_built_table_has_exactly_its_dbt_parents(om, expected):
    """Each table dbt builds has, in OpenMetadata, one upstream edge per dbt parent and no other."""
    edges, children = expected
    wrong = {}
    for table in children:
        have, _ = om_upstream(om, table)
        want = {e for e in edges if e[1] == table}
        if have != want:
            wrong[table] = {"missing": sorted(want - have), "extra": sorted(have - want)}
    assert not wrong, wrong


def test_tables_nothing_builds_have_no_upstream(om, expected):
    """A table dbt doesn't build (bronze the loader writes, ops, ref) has no upstream edge: nothing is invented."""
    edges, children = expected
    for table in sorted(lake_tables() - set(children)):
        have, _ = om_upstream(om, table)
        assert not have, (table, have)


def test_edges_say_they_come_from_dbt(om, expected):
    """Every edge om_sync.py writes is marked DbtLineage, so a steward's hand-drawn edge is told apart."""
    _, children = expected
    _, raw = om_upstream(om, "world_gold.fct_incident")
    assert raw and all((e.get("lineageDetails") or {}).get("source") == "DbtLineage" for e in raw)


def test_an_edge_dbt_does_not_have_is_removed(om, expected):
    """A dbt edge OpenMetadata holds that dbt no longer has (planted here) is gone after a sync."""
    edges, _ = expected
    a = get(om, f"tables/name/{FQN}gold.dim_unit")
    b = get(om, f"tables/name/{FQN}world_gold.fct_incident")
    assert ("gold.dim_unit", "world_gold.fct_incident") not in edges
    r = om.put(f"{OM}/lineage", timeout=30, json={"edge": {
        "fromEntity": {"id": a["id"], "type": "table"}, "toEntity": {"id": b["id"], "type": "table"},
        "lineageDetails": {"source": "DbtLineage", "description": "planted by test_om_lineage.py"}}})
    r.raise_for_status()
    assert ("gold.dim_unit", "world_gold.fct_incident") in om_upstream(om, "world_gold.fct_incident")[0]
    subprocess.run(SYNC, check=True, capture_output=True, text=True)
    assert ("gold.dim_unit", "world_gold.fct_incident") not in om_upstream(om, "world_gold.fct_incident")[0]


def test_lineage_is_in_step_after_a_sync():
    """--check finds no lineage difference once the sync has run."""
    r = subprocess.run(SYNC + ["--check"], capture_output=True, text=True)
    assert "lineage" not in r.stdout, r.stdout


def test_an_edge_a_steward_drew_survives_a_sync(om):
    """An edge drawn by hand in OpenMetadata (marked Manual) isn't dbt's to remove: it's still there after a sync."""
    a = get(om, f"tables/name/{FQN}gold.dim_offense")
    b = get(om, f"tables/name/{FQN}world_gold.fct_mission")
    edge = ("gold.dim_offense", "world_gold.fct_mission")
    om.put(f"{OM}/lineage", timeout=30, json={"edge": {
        "fromEntity": {"id": a["id"], "type": "table"}, "toEntity": {"id": b["id"], "type": "table"},
        "lineageDetails": {"source": "Manual", "description": "drawn by hand, planted by test_om_lineage.py"}}}
           ).raise_for_status()
    try:
        subprocess.run(SYNC, check=True, capture_output=True, text=True)
        assert edge in om_upstream(om, "world_gold.fct_mission")[0]
    finally:
        om.delete(f"{OM}/lineage/table/{a['id']}/table/{b['id']}", timeout=30).raise_for_status()
    assert edge not in om_upstream(om, "world_gold.fct_mission")[0]
