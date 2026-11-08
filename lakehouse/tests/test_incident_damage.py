"""The incident_damage view names the fight each damage row came from (2026-11-07).
    pytest -q lakehouse/tests/test_incident_damage.py     # no stack needed: CI runs this

wrolfgar: add incident_id and the incident type to incident_damage, so damage can be traced to one fight and split by
the kind of fight. The damage cube already carries incident_id and joins world_incidents on it (many damage rows to
one fight), so the view takes incident_id from world_damage and incident_type through that join.
acceptance/test_world_products.py checks the numbers against the lake.
"""
from pathlib import Path

import yaml

LAKEHOUSE = Path(__file__).resolve().parents[1]
WORLD = yaml.safe_load((LAKEHOUSE / "cube" / "model" / "world.yml").read_text())
CUBES = {c["name"]: c for c in WORLD["cubes"]}
VIEWS = {v["name"]: v for v in WORLD["views"]}


def includes(view, path):
    """The members a view takes from one join path (empty when the view has no such path)."""
    return next((set(p["includes"]) for p in VIEWS[view]["cubes"] if p["join_path"] == path), set())


def test_damage_cube_has_its_fight_as_a_dimension():
    """world_damage offers incident_id, the fight the damage came from, as a number."""
    dims = {d["name"]: d for d in CUBES["world_damage"]["dimensions"]}
    assert dims["incident_id"]["sql"] == "incident_id" and dims["incident_id"]["type"] == "number"


def test_incident_damage_offers_the_fight_and_its_kind():
    """incident_damage takes incident_id from the damage row and incident_type through the join to the fight."""
    assert "incident_id" in includes("incident_damage", "world_damage")
    assert "incident_type" in includes("incident_damage", "world_damage.world_incidents")
    joins = {j["name"]: j for j in CUBES["world_damage"]["joins"]}
    assert joins["world_incidents"]["relationship"] == "many_to_one"


def test_incident_damage_says_it_reads_the_fights():
    """The view's meta.reads names fct_incident, which incident_type now comes from (lineage and OM read it)."""
    assert "world_gold.fct_incident" in VIEWS["incident_damage"]["meta"]["reads"]
