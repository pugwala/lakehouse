"""Heroes and villains by their common names (2026-11-07): SQL and the AI agent can say SUPERMAN or JOKER, not a SID.
    pytest -q lakehouse/tests/test_common_names.py     # no stack needed: CI runs this

Ian: queries that answer only with SIDs are meaningless for teaching. A hero's or villain's alias is their common
name, public like a stage name; their real name, birth date and SID stay restricted. world_gold.dim_person carries it
as common_name (tests/test_world_lake.py checks the rows), and these tests check the model files around it:
  - Cube's world_people cube reads it from world_gold.dim_person, and the views about people (fight_participants,
    court_outcomes) offer it, so query_metric can group or filter by it; no view offers a real name or birth date;
  - the glossary defines Common Name on that column, with a business rule saying it is public and real names are not.
"""
from pathlib import Path

import yaml

LAKEHOUSE = Path(__file__).resolve().parents[1]
WORLD = yaml.safe_load((LAKEHOUSE / "cube" / "model" / "world.yml").read_text())
GLOSSARY = yaml.safe_load((LAKEHOUSE / "glossary" / "glossary.yml").read_text())
CUBES = {c["name"]: c for c in WORLD["cubes"]}
VIEWS = {v["name"]: v for v in WORLD["views"]}
PRIVATE = {"last_name", "first_name", "alias", "birth_date", "sid_number"}


def view_members(view):
    """Every member name a view includes, across its join paths."""
    return {m for part in VIEWS[view]["cubes"] for m in part["includes"]}


def test_world_people_reads_common_name_from_dim_person():
    """One cube for the world's people, on world_gold.dim_person, with common_name and role as dimensions."""
    people = CUBES["world_people"]
    assert people["sql_table"] == "lake.world_gold.dim_person"
    dims = {d["name"]: d for d in people["dimensions"]}
    assert dims["common_name"]["sql"] == "common_name" and dims["common_name"]["type"] == "string"
    assert "person_role" in dims
    assert not set(dims) & PRIVATE


def test_participants_and_charges_join_their_people():
    """Fights and charges reach world_people through person_key, many rows to one person."""
    for cube in ["world_participation", "world_charges"]:
        joins = {j["name"]: j for j in CUBES[cube]["joins"]}
        assert joins["world_people"]["relationship"] == "many_to_one", cube
        assert "person_key" in joins["world_people"]["sql"], cube


def test_people_views_offer_the_common_name_and_nothing_private():
    """fight_participants and court_outcomes can be grouped by common_name; no world view offers a private column."""
    for view in ["fight_participants", "court_outcomes"]:
        assert "common_name" in view_members(view), view
        paths = [part["join_path"] for part in VIEWS[view]["cubes"]]
        assert any(p.endswith("world_people") for p in paths), view
    for view in VIEWS:
        assert not view_members(view) & PRIVATE, view


def test_the_glossary_defines_common_name_and_says_it_is_public():
    """define_term can explain Common Name, and the rulebook says why it is public when real names are not."""
    terms = {t["name"]: t for t in GLOSSARY["terms"]}
    term = terms["Common Name"]
    assert "world_gold.dim_person.common_name" in term["columns"]
    assert {"alias", "hero name", "villain name"} <= set(term["synonyms"])
    rules = {r["name"]: r for r in GLOSSARY["rules"]}
    rule = rules["A common name is public, a real name is not"]
    assert "Common Name" in rule["about"]
    assert "test:test_common_names_live.py::test_the_agent_reads_reports_with_aliases_kept" in rule["enforced_by"]
