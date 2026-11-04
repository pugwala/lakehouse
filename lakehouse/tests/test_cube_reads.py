"""Every public Cube cube and view says which lake tables it reads, in meta.reads, and says it right.

    pytest -q lakehouse/tests/test_cube_reads.py

The MCP server's lineage and describe_table tools learn which lake tables a metric comes from through Cube's own
/meta (the server holds no lake credentials and reads no model files), so each public cube and view lists them in
meta.reads. These tests work the list out from the model itself (a cube's sql_table or sql, a view's join paths) and
check meta.reads matches, so the two can't drift apart. No stack needed: CI runs this.
"""
import re
from pathlib import Path

import pytest
import yaml

CUBE = Path(__file__).resolve().parents[1] / "cube"
FOLDERS = [CUBE / "model", CUBE / "course1"]   # course1/: the course 1 add-on, loaded while LAKEHOUSE_COURSE1 is on
LAKE_TABLE = re.compile(r"\blake\.(\w+)\.(\w+)")


def model():
    """({cube name: cube}, {view name: view}) from every model file (cube/model, and the add-on's cube/course1)."""
    cubes, views = {}, {}
    for path in sorted(p for folder in FOLDERS for p in folder.glob("*.yml")):
        doc = yaml.safe_load(path.read_text()) or {}
        cubes |= {c["name"]: c for c in doc.get("cubes") or []}
        views |= {v["name"]: v for v in doc.get("views") or []}
    return cubes, views


def own_tables(cube):
    """The lake tables a cube reads: its sql_table, or every lake.<schema>.<table> its sql names."""
    return {f"{s}.{t}" for s, t in LAKE_TABLE.findall(cube.get("sql_table") or cube.get("sql") or "")}


def view_tables(view, cubes):
    """The lake tables a view reads: those of every cube on any of its join paths."""
    names = {name for part in view.get("cubes") or [] for name in part["join_path"].split(".")}
    return set().union(*(own_tables(cubes[n]) for n in names))


CUBES, VIEWS = model()
PUBLIC = sorted(n for n, c in CUBES.items() if c.get("public", True) is not False)


def test_the_rule_finds_tables():
    """The rule itself works: a sql_table, a sql with a subquery, and a view across two cubes."""
    a = {"sql_table": "lake.gold.fct_offender_record"}
    b = {"sql": "SELECT * FROM lake.mart_readiness.period_readiness WHERE product = 'x'"}
    assert own_tables(a) == {"gold.fct_offender_record"} and own_tables(b) == {"mart_readiness.period_readiness"}
    assert view_tables({"cubes": [{"join_path": "a"}, {"join_path": "a.b"}]}, {"a": a, "b": b}) == \
        {"gold.fct_offender_record", "mart_readiness.period_readiness"}


@pytest.mark.parametrize("name", PUBLIC)
def test_a_public_cube_lists_what_it_reads(name):
    """A cube agents can see says, in meta.reads, exactly the lake tables it reads."""
    reads = (CUBES[name].get("meta") or {}).get("reads")
    assert reads is not None, f"cube {name} has no meta.reads"
    assert sorted(reads) == sorted(own_tables(CUBES[name])), f"cube {name}: meta.reads is wrong"


@pytest.mark.parametrize("name", sorted(VIEWS))
def test_a_view_lists_what_it_reads(name):
    """A view says, in meta.reads, exactly the lake tables of every cube on its join paths."""
    reads = (VIEWS[name].get("meta") or {}).get("reads")
    assert reads is not None, f"view {name} has no meta.reads"
    assert sorted(reads) == sorted(view_tables(VIEWS[name], CUBES)), f"view {name}: meta.reads is wrong"


def test_incident_reports_is_a_view_over_the_redacted_reports_only():
    """search_incident_reports' view reads the redacted gold table, never silver or bronze's raw narratives."""
    reads = set(VIEWS["incident_reports"]["meta"]["reads"])
    assert "world_gold.incident_report_redacted" in reads
    assert not any(t.startswith(("world_silver.", "world_bronze.")) for t in reads)
