"""An agent can find the costliest fights and who fought in them (2026-11-07).
    pytest -q lakehouse/tests/test_fight_lookup.py     # no stack needed: CI runs this

wrolfgar asked to close the gaps an agent hit on "top 5 fights by damage, and their heroes and villains":
  - query_metric takes order ("desc" or "asc") on the measure, instead of relying on Cube's unstated default;
  - fight_participants offers incident_id, so a fight's people come back by common name from governed data;
  - search_incident_reports filters by incident_id, for the reports written about one fight.
These check the model files and the tools' parameters without a stack (mcp/server.py is read, not imported);
acceptance/test_mcp.py and acceptance/test_mcp_reports.py check the answers against the lake.
"""
import ast
from pathlib import Path

import yaml

LAKEHOUSE = Path(__file__).resolve().parents[1]
WORLD = yaml.safe_load((LAKEHOUSE / "cube" / "model" / "world.yml").read_text())
CUBES = {c["name"]: c for c in WORLD["cubes"]}
VIEWS = {v["name"]: v for v in WORLD["views"]}
SERVER = ast.parse((LAKEHOUSE / "mcp" / "server.py").read_text())


def tool_args(name):
    """The parameter names of a top-level function in mcp/server.py."""
    fn = next(n for n in SERVER.body if isinstance(n, ast.FunctionDef) and n.name == name)
    return [a.arg for a in fn.args.args]


def model_fields(name):
    """The annotated field names of a Pydantic model class in mcp/server.py."""
    cls = next(n for n in SERVER.body if isinstance(n, ast.ClassDef) and n.name == name)
    return [s.target.id for s in cls.body if isinstance(s, ast.AnnAssign)]


def test_fight_participants_offers_the_fight():
    """world_participation has incident_id as a number, and fight_participants takes it from there."""
    dims = {d["name"]: d for d in CUBES["world_participation"]["dimensions"]}
    assert dims["incident_id"]["sql"] == "incident_id" and dims["incident_id"]["type"] == "number"
    part = next(p for p in VIEWS["fight_participants"]["cubes"] if p["join_path"] == "world_participation")
    assert "incident_id" in part["includes"]


def test_query_metric_takes_an_order():
    """query_metric has an order parameter, and says what happens without one."""
    assert "order" in tool_args("query_metric")
    fn = next(n for n in SERVER.body if isinstance(n, ast.FunctionDef) and n.name == "query_metric")
    doc = ast.get_docstring(fn)
    assert "order" in doc and "desc" in doc and "asc" in doc


def test_search_incident_reports_takes_a_fight():
    """search_incident_reports filters by incident_id, and its answer says which fight was asked for."""
    assert "incident_id" in tool_args("search_incident_reports")
    assert "incident_id" in model_fields("ReportSearch")
