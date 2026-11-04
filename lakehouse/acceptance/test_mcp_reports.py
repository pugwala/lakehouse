"""Acceptance test for the MCP server's search_incident_reports: search what was written about the fights, safely.

    docker compose --profile core exec -T jupyter pytest -q lakehouse/acceptance/test_mcp_reports.py

The tool searches Cube's incident_reports view, which reads world_gold.incident_report_redacted: every name, alias,
SID, birth date and phone number already replaced. Words, a kind of report, a city and a filing-date range narrow it;
the answer is how many reports match and the newest few, with the fight's kind, month and city. Counts are checked
against the lake; the redaction against the mention key, the world's own record of each personal detail.
"""
import pytest

from lakehouse import lake
from test_mcp import call

MENTIONS = "/lake/landing/universe/M/mention_key/incident_report/*.parquet"
KINDS = {"field report", "witness statement", "desk report"}


def ok(**arguments) -> dict:
    """search_incident_reports' result, after checking the call succeeded."""
    is_error, result, text = call("search_incident_reports", **arguments)
    assert not is_error, text
    return result


def refused(**arguments) -> str:
    """The error text, after checking the call was refused."""
    is_error, _, text = call("search_incident_reports", **arguments)
    assert is_error, f"{arguments} should have been refused"
    return text


def lake_one(sql, *params):
    """The first value of a read-only query on the lake."""
    con = lake.lake_ro_connect()
    try:
        return con.execute(sql, list(params)).fetchone()[0]
    finally:
        con.close()


REDACTED = "lake.world_gold.incident_report_redacted"


def test_words_find_every_report_that_has_them():
    """"bridge", in any case: the match count is the lake's, and each report returned contains it."""
    got = ok(text="Bridge")
    assert got["matches"] == lake_one(f"SELECT count(*) FROM {REDACTED} WHERE narrative ILIKE '%bridge%'") > 0
    assert 0 < len(got["reports"]) <= 10
    assert all("bridge" in r["narrative"].casefold() for r in got["reports"])


def test_reports_come_newest_first_with_the_fights_details():
    """Newest filing first; each report says its fight, kind, filing time, the fight's kind and month, and its city."""
    got = ok(text="bridge", limit=20)
    filed = [r["filed_at"] for r in got["reports"]]
    assert filed == sorted(filed, reverse=True) and len(filed) == 20
    r = got["reports"][0]
    assert set(r) == {"incident_report_id", "incident_id", "report_kind", "filed_at", "incident_type",
                      "incident_month", "city", "narrative"}
    assert r["report_kind"] in KINDS


def test_no_personal_detail_comes_back():
    """For every report returned, none of the details the mention key marks in it appears in its narrative."""
    got = ok(text="identified as", limit=50)
    ids = [r["incident_report_id"] for r in got["reports"]]
    con = lake.lake_ro_connect()
    try:
        marked = con.execute(f"SELECT incident_report_id, as_written FROM read_parquet('{MENTIONS}') "
                             "WHERE incident_report_id IN (SELECT unnest(?))", [ids]).fetchall()
    finally:
        con.close()
    assert marked, "the sample has no mentions to check"
    text = {r["incident_report_id"]: r["narrative"] for r in got["reports"]}
    assert not [(i, w) for i, w in marked if w in text[i]]
    assert any("[PERSON NAME]" in t for t in text.values())


def test_a_persons_name_finds_nothing():
    """Searching for someone the reports name returns no report: names were replaced before the search."""
    name = lake_one(f"SELECT as_written FROM read_parquet('{MENTIONS}') WHERE kind = 'person_name' "
                    "AND as_written LIKE '% %' AND length(as_written) > 10 ORDER BY incident_report_id LIMIT 1")
    assert lake_one(f"SELECT count(*) FROM {REDACTED} WHERE narrative ILIKE ?", f"%{name}%") == 0
    assert ok(text=name)["matches"] == 0


def test_kind_city_and_dates_narrow_it_as_the_lake_does():
    """A kind of report, a city and a filing-date range each give the lake's count."""
    assert ok(kind="witness statement")["matches"] == lake_one(
        f"SELECT count(*) FROM {REDACTED} WHERE report_kind = 'witness statement'")
    city = lake_one("SELECT l.name FROM lake.world_gold.fct_incident i JOIN lake.world_gold.dim_location l "
                    "ON l.location_id = i.city_id GROUP BY 1 ORDER BY count(*) DESC LIMIT 1")
    got = ok(city=city, text="heist")
    assert got["matches"] == lake_one(
        f"SELECT count(*) FROM {REDACTED} r JOIN lake.world_gold.fct_incident i USING (incident_id) "
        "JOIN lake.world_gold.dim_location l ON l.location_id = i.city_id "
        "WHERE l.name = ? AND r.narrative ILIKE '%heist%'", city) > 0
    assert all(r["city"] == city for r in got["reports"])
    assert ok(city=city[:-1])["matches"] == 0   # a city is its whole name, not a part of one
    got = ok(date_from="2020-01-01", date_to="2020-12-31")
    assert got["matches"] == lake_one(
        f"SELECT count(*) FROM {REDACTED} WHERE filed_at >= DATE '2020-01-01' AND filed_at < DATE '2021-01-01'")
    assert all(r["filed_at"][:4] == "2020" for r in got["reports"])


def test_limit_is_kept_between_1_and_50():
    """limit asks for that many reports, at most 50."""
    assert len(ok(text="custody", limit=3)["reports"]) == 3
    assert len(ok(text="custody", limit=500)["reports"]) == 50


@pytest.mark.parametrize("arguments, says", [
    ({}, "text"),
    ({"kind": "police report"}, "witness statement"),
    ({"date_from": "last year"}, "YYYY-MM-DD"),
])
def test_it_refuses_what_it_cant_search(arguments, says):
    """No search at all, an unknown kind (the kinds are listed) or a date that isn't one."""
    assert says in refused(**arguments)
