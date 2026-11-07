"""Acceptance test: SQL and the AI agent answer about heroes and villains by their common names (2026-11-07).
    docker compose --profile core exec -T jupyter pytest -q lakehouse/acceptance/test_common_names_live.py

A hero's or villain's alias is their common name, public like a stage name: world_gold.dim_person.common_name, which
Cube's fight_participants and court_outcomes views offer as a dimension. The checks ask the running stack the way a
student would: Cube's SQL API (as Superset and notebooks do) and the MCP server's query_metric and
search_incident_reports (as Claude does). People are still counted by distinct person key, never summed, and the
famous names show that several people can share one (copycats among them).
"""
import psycopg2
import pytest

from test_cube import CUBE_SQL, rows
from test_mcp import call

FAMOUS_HEROES = ["SUPERMAN", "WONDER WOMAN", "WOLVERINE"]


@pytest.fixture(scope="module")
def cube():
    """A connection to Cube's Postgres-wire SQL API."""
    conn = psycopg2.connect(**CUBE_SQL, connect_timeout=10)
    conn.autocommit = True
    yield conn
    conn.close()


def test_sql_groups_fights_by_common_name(cube):
    """Cube SQL: the famous heroes are in the fights, each counted as distinct people (copycats share a name)."""
    got = dict(rows(cube, "SELECT common_name, MEASURE(people_involved) FROM fight_participants "
                          f"WHERE common_name IN ({', '.join(repr(n) for n in FAMOUS_HEROES)}) GROUP BY 1"))
    assert set(got) == set(FAMOUS_HEROES), got
    assert all(n >= 1 for n in got.values()), got


def test_sql_ranks_villains_by_fights(cube):
    """The busiest villains by fights come back by common name, not by SID."""
    top = rows(cube, "SELECT common_name, MEASURE(participations) FROM fight_participants "
                     "WHERE person_role = 'villain' AND common_name IS NOT NULL GROUP BY 1 ORDER BY 2 DESC LIMIT 5")
    assert len(top) == 5 and all(isinstance(name, str) and name for name, _ in top), top


def test_sql_shows_charges_by_common_name(cube):
    """Court outcomes can be broken down by the common name of the person charged."""
    got = rows(cube, "SELECT common_name, MEASURE(charges) FROM court_outcomes "
                     "WHERE common_name IS NOT NULL GROUP BY 1 ORDER BY 2 DESC LIMIT 3")
    assert len(got) == 3, got


def test_the_agent_answers_by_common_name():
    """query_metric groups by common_name and filters on it; each row names the hero."""
    err, result, text = call("query_metric", metric="people_involved", group_by=["common_name"],
                             filters=[{"dimension": "common_name", "operator": "equals", "values": FAMOUS_HEROES}])
    assert not err, text
    names = {next(v for k, v in row.items() if k.endswith("common_name")) for row in result["rows"]}
    assert names == set(FAMOUS_HEROES), result["rows"]


def test_the_agent_reads_reports_with_aliases_kept():
    """search_incident_reports shows aliases as written, never [ALIAS], and still hides real names."""
    err, result, text = call("search_incident_reports", text="taken into custody", limit=50)
    assert not err, text
    narratives = [r["narrative"] for r in result["reports"]]
    assert len(narratives) == 50 and not any("[ALIAS]" in n for n in narratives)
    assert any("[PERSON NAME]" in n for n in narratives)          # real names still replaced
    assert any(' aka "' in n for n in narratives)                  # '[PERSON NAME] aka "Amber Heron"': the alias shows
