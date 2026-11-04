"""Acceptance test for the MCP server's describe_table and lineage: what a lake table is, and where it comes from.

    docker compose --profile core exec -T jupyter pytest -q lakehouse/acceptance/test_mcp_catalog.py

describe_table reads one table from OpenMetadata (as mcp-reader): its columns in order with their types, descriptions
and tags, which are restricted or personal, its layer, the data products that deliver it, its data contract, and the
Cube views that read it. lineage walks OpenMetadata's lineage (om_sync.py publishes dbt's) up and down from a table,
or from a metric's views, and says which views and data products depend on it. Every expected answer here comes from
somewhere else: the lake, dbt's manifest, the Cube model files, the product descriptors, glossary.yml.
"""
import json
import re
from pathlib import Path

import pytest
import yaml

from lakehouse import lake
from lakehouse.tagging import tags as tagger
from test_mcp import LAKEHOUSE, call
from test_om_lineage import dbt_edges
from test_om_sync import restricted_columns

PRODUCTS = [yaml.safe_load(p.read_text()) for p in sorted((LAKEHOUSE / "products").glob("*.yml"))]
CUBE_FILES = [p for folder in ("model", "course1") for p in sorted((LAKEHOUSE / "cube" / folder).glob("*.yml"))]


def ok(tool, **arguments) -> dict:
    """A tool's result, after checking the call succeeded."""
    is_error, result, text = call(tool, **arguments)
    assert not is_error, text
    return result


def refused(tool, **arguments) -> str:
    """A tool's error text, after checking the call was refused."""
    is_error, _, text = call(tool, **arguments)
    assert is_error, f"{tool} {arguments} should have been refused"
    return text


def lake_rows(sql, *params):
    """A read-only query's rows on the lake."""
    con = lake.lake_ro_connect()
    try:
        return con.execute(sql, list(params)).fetchall()
    finally:
        con.close()


def lake_tables():
    """Every schema.table in the lake, views included."""
    return {f"{s}.{t}" for s, t in lake_rows(
        "SELECT table_schema, table_name FROM information_schema.tables WHERE table_catalog = 'lake' "
        "AND table_schema NOT IN ('information_schema', 'pg_catalog')")}


def cube_reads():
    """{public cube or view: the lake tables its meta.reads lists}, from the model files."""
    out = {}
    for path in CUBE_FILES:
        doc = yaml.safe_load(path.read_text()) or {}
        for item in (doc.get("cubes") or []) + (doc.get("views") or []):
            reads = (item.get("meta") or {}).get("reads")
            if reads is not None:
                out[item["name"]] = set(reads)
    return out


@pytest.fixture(scope="module")
def ancestors():
    """{table: every lake table it's built from, directly or not}, from dbt's manifest (the tagger's own walk)."""
    tables = lake_tables()
    up = tagger.upstream(json.loads((LAKEHOUSE / "dbt" / "target" / "manifest.json").read_text()))
    return {t: {a for a in up.get(t, set()) if a in tables and a != t} for t in tables}


def descendants(ancestors, table):
    """Every lake table built from table, directly or not."""
    return {t for t, ups in ancestors.items() if table in ups}


# --- describe_table --------------------------------------------------------------------------------------------

def test_describe_table_lists_the_columns_in_the_lakes_order():
    """world_gold.fct_charge: the same columns, in the same order, as the lake has them."""
    got = ok("describe_table", table="world_gold.fct_charge")
    want = [r[0] for r in lake_rows("SELECT column_name FROM information_schema.columns WHERE table_catalog = 'lake' "
                                    "AND table_schema = 'world_gold' AND table_name = 'fct_charge' "
                                    "ORDER BY ordinal_position")]
    assert got["table"] == "world_gold.fct_charge" and [c["name"] for c in got["columns"]] == want
    assert got["column_count"] == len(want) and all(c["type"] for c in got["columns"])


def test_describe_table_marks_the_restricted_columns():
    """gold.fct_offender_record: restricted are exactly the columns dbt marks restricted (Cube masks them)."""
    got = ok("describe_table", table="gold.fct_offender_record")
    assert {c["name"] for c in got["columns"] if c["restricted"]} == restricted_columns()


def test_describe_table_marks_the_personal_columns_the_tagger_found():
    """world_silver.person: personal are exactly the columns the tagger gave a PIIType tag (ops.column_tags)."""
    got = ok("describe_table", table="world_silver.person")
    want = {r[0] for r in lake_rows("SELECT column_name FROM lake.ops.column_tags WHERE table_schema = 'world_silver' "
                                    "AND table_name = 'person' AND tag LIKE 'PIIType.%'")}
    assert want and {c["name"] for c in got["columns"] if c["personal"]} == want


def test_describe_table_gives_the_layer_and_the_table_tags():
    """The layer and the table's own tags are the tagger's (ops.table_tags)."""
    got = ok("describe_table", table="world_gold.fct_incident")
    tags = {r[0] for r in lake_rows("SELECT tag FROM lake.ops.table_tags WHERE table_schema = 'world_gold' "
                                    "AND table_name = 'fct_incident'")}
    assert got["layer"] == "Gold" and tags <= set(got["tags"])


def test_describe_table_links_columns_to_glossary_terms():
    """offender_number in gold.fct_offender_record speaks the glossary's Offender Number."""
    got = ok("describe_table", table="gold.fct_offender_record")
    col = next(c for c in got["columns"] if c["name"] == "offender_number")
    assert "Offender Number" in col["terms"]


def test_describe_table_says_which_products_deliver_it_and_its_contract():
    """A product's table names that product (from its descriptor) and the contract OpenMetadata holds for it."""
    got = ok("describe_table", table="world_gold.fct_charge")
    assert got["products"] == sorted(p["name"] for p in PRODUCTS if "world_gold.fct_charge" in p["tables"])
    assert got["contract"] and got["contract"]["table"] == "world_gold.fct_charge"
    plain = ok("describe_table", table="world_silver.person")
    assert plain["products"] == [] and plain["contract"] is None


def test_describe_table_names_the_cube_views_that_read_it():
    """The views (and public cubes) listed are exactly those whose meta.reads names the table."""
    for table in ("world_gold.fct_incident", "world_gold.incident_report_redacted", "world_silver.person"):
        got = ok("describe_table", table=table)
        assert got["cube_views"] == sorted(n for n, reads in cube_reads().items() if table in reads), table


def test_describe_table_takes_a_bare_name_when_only_one_schema_has_it():
    """fct_charge alone is world_gold.fct_charge; case doesn't matter."""
    assert ok("describe_table", table="FCT_Charge")["table"] == "world_gold.fct_charge"


def test_describe_table_refuses_an_ambiguous_or_unknown_name():
    """incident is in bronze and silver: both are named. A typo gets close matches."""
    text = refused("describe_table", table="incident")
    assert "world_bronze.incident" in text and "world_silver.incident" in text
    assert "world_gold.fct_charge" in refused("describe_table", table="world_gold.fct_chargez")


def test_describe_table_never_returns_a_value():
    """Metadata only: no rows, no sample values. A name from the lake never appears in the answer."""
    name = lake_rows("SELECT last_name FROM lake.world_silver.person WHERE length(last_name) > 6 LIMIT 1")[0][0]
    assert name not in json.dumps(ok("describe_table", table="world_silver.person"))


# --- lineage -------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("table", ["world_gold.fct_charge", "mart_custody.custody_snapshot_monthly",
                                   "world_gold.incident_report_redacted"])
def test_lineage_upstream_is_everything_dbt_builds_it_from(ancestors, table):
    """Every table it's built from, directly or not, as dbt's manifest has it; direct parents at depth 1."""
    got = ok("lineage", name=table)
    assert got["kind"] == "table" and got["table"] == table
    assert {s["table"] for s in got["upstream"]} == ancestors[table]
    direct = {s["table"] for s in got["upstream"] if s["depth"] == 1}
    assert direct == {p for p, c in dbt_edges() if c == table}


def test_lineage_downstream_is_everything_built_from_it(ancestors):
    """world_silver.incident feeds the world's gold, its exceptions view and more: exactly dbt's descendants."""
    got = ok("lineage", name="world_silver.incident")
    assert {s["table"] for s in got["downstream"]} == descendants(ancestors, "world_silver.incident")
    assert "world_gold.fct_incident" in {s["table"] for s in got["downstream"] if s["depth"] == 1}


def test_lineage_names_the_views_and_products_that_depend_on_it(ancestors):
    """What breaks if world_silver.charge changes: the views reading it or anything built from it, and the products
    delivering any of those."""
    table = "world_silver.charge"
    affected = {table} | descendants(ancestors, table)
    got = ok("lineage", name=table)
    assert got["cube_views"] == sorted(n for n, reads in cube_reads().items() if reads & affected)
    assert got["products"] == sorted(p["name"] for p in PRODUCTS if set(p["tables"]) & affected)
    assert "court_outcomes" in got["cube_views"] and "court-outcomes" in got["products"]


def test_lineage_says_where_the_data_comes_from():
    """sources: the table's Source tags, which the tagger carries down every lineage path (ops.table_tags)."""
    got = ok("lineage", name="world_gold.fct_charge")
    want = sorted(r[0] for r in lake_rows("SELECT tag FROM lake.ops.table_tags WHERE table_schema = 'world_gold' "
                                          "AND table_name = 'fct_charge' AND tag LIKE 'Source.%'"))
    assert want and got["sources"] == want


def test_lineage_of_a_metric_goes_through_its_views(ancestors):
    """people_in_custody: the views offering it, the tables they read, and everything those are built from."""
    got = ok("lineage", name="people_in_custody")
    assert got["kind"] == "metric" and set(got["metric_views"]) == {"custody_population", "custody_offenses"}
    reads = set().union(*(cube_reads()[v] for v in got["metric_views"]))
    assert set(got["reads"]) == reads
    assert {s["table"] for s in got["upstream"]} == reads | set().union(*(ancestors[t] for t in reads))
    assert got["downstream"] == []


def test_lineage_refuses_an_unknown_name():
    """Neither a table nor a metric: the answer says how to find one."""
    text = refused("lineage", name="no_such_thing_anywhere")
    assert "list_metrics" in text and "find_by_tags" in text


def test_lineage_never_invents_a_path():
    """A table dbt doesn't build (the loader's bronze) has nothing upstream."""
    got = ok("lineage", name="bronze.hero_offenders_raw")
    assert got["upstream"] == [] and got["downstream"]
    assert re.fullmatch(r"\w+\.\w+", got["downstream"][0]["table"])
