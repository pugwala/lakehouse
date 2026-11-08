"""Acceptance test: the agent finds the costliest fights and who fought in them (2026-11-07).
    docker compose --profile core exec -T jupyter pytest -q lakehouse/acceptance/test_mcp_fights.py

"Top 5 fights by damage, and their heroes and villains" in three calls, each checked against the lake:
query_metric on damage_cost_usd grouped by incident_id with order="desc" (incident_damage has incident_id since
7f90e80); query_metric on fight_participants filtered to one incident_id, by common name and person_role; and
search_incident_reports filtered to that incident_id, for what was written about it.
"""
import pytest

from lakehouse import lake
from test_mcp import call


def lake_rows(sql, *params):
    """All rows of a read-only query on the lake."""
    con = lake.lake_ro_connect()
    try:
        return con.execute(sql, list(params)).fetchall()
    finally:
        con.close()


def ok(tool, **arguments) -> dict:
    """A tool's structured result, after checking the call succeeded."""
    is_error, result, text = call(tool, **arguments)
    assert not is_error, text
    return result


@pytest.fixture(scope="module")
def top_fight():
    """The incident_id of the fight with the most damage, as the lake sums it."""
    return lake_rows("SELECT incident_id FROM world_gold.fct_damage GROUP BY 1 ORDER BY sum(cost_usd) DESC, 1 LIMIT 1")[0][0]


def test_query_metric_orders_by_the_measure_both_ways():
    """order="desc" gives the costliest five fights and order="asc" the cheapest three, as the lake orders them."""
    top = ok("query_metric", metric="damage_cost_usd", group_by=["incident_id"], order="desc", limit=5)["rows"]
    want = lake_rows("SELECT incident_id, sum(cost_usd) FROM world_gold.fct_damage GROUP BY 1 ORDER BY 2 DESC, 1 LIMIT 5")
    assert [(int(r["incident_id"]), int(r["damage_cost_usd"])) for r in top] == [(i, int(c)) for i, c in want]
    low = ok("query_metric", metric="damage_cost_usd", group_by=["incident_id"], order="asc", limit=3)["rows"]
    cheapest = lake_rows("SELECT sum(cost_usd) FROM world_gold.fct_damage GROUP BY incident_id ORDER BY 1 LIMIT 3")
    assert [int(r["damage_cost_usd"]) for r in low] == [int(c) for (c,) in cheapest]


def test_query_metric_refuses_an_order_it_cant_use():
    """Anything but asc or desc is refused before Cube is asked, saying what each one means (Cube's own refusal
    names them too, but not which way they sort)."""
    is_error, _, text = call("query_metric", metric="damage_cost_usd", group_by=["incident_id"], order="sideways")
    assert is_error and "'sideways'" in text and "largest first" in text and "smallest first" in text


def test_a_fights_people_come_back_by_common_name(top_fight):
    """fight_participants filtered to one fight: its people by common name and role, counted as the lake does."""
    got = ok("query_metric", metric="people_involved", group_by=["common_name", "person_role"],
             filters=[{"dimension": "incident_id", "operator": "equals", "values": [str(top_fight)]}])["rows"]
    want = lake_rows("SELECT p.common_name, p.role, count(DISTINCT f.person_key) FROM world_gold.fct_participation f "
                     "JOIN world_gold.dim_person p USING (person_key) WHERE f.incident_id = ? GROUP BY 1, 2", top_fight)
    assert want, "the costliest fight should have people in it"
    assert sorted((r["common_name"] or "", r["person_role"], int(r["people_involved"])) for r in got) == \
        sorted((n or "", role, int(c)) for n, role, c in want)   # civilians have no common name


def test_reports_about_one_fight():
    """search_incident_reports with only incident_id: every report about that fight, and nothing else. Most fights
    have no report (200,000 reports, 1.2M fights), so this takes the costliest fight that has some."""
    fight, want = lake_rows("WITH cost AS (SELECT incident_id, sum(cost_usd) AS usd FROM world_gold.fct_damage GROUP BY 1), "
                            "said AS (SELECT incident_id, count(*) AS n FROM world_gold.incident_report_redacted GROUP BY 1) "
                            "SELECT incident_id, n FROM cost JOIN said USING (incident_id) ORDER BY usd DESC, 1 LIMIT 1")[0]
    result = ok("search_incident_reports", incident_id=fight, limit=50)
    assert result["incident_id"] == fight and result["matches"] == want
    assert len(result["reports"]) == min(want, 50) and all(r["incident_id"] == fight for r in result["reports"])
