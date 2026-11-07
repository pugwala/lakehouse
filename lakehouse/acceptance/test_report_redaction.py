"""Acceptance test for world_gold.incident_report_redacted: the incident reports with every personal detail replaced.

    docker compose --profile core exec -T jupyter pytest -q lakehouse/acceptance/test_report_redaction.py

The reports name people on purpose (Priority 5): names, aliases, SIDs, birth dates and witnesses' phone numbers, for
the text sessions to find. The MCP server's search_incident_reports must never hand the personal ones to an agent, so
it reads this gold table through Cube instead: each personal detail the mention key marks becomes [PERSON NAME], [SID],
[BIRTH DATE] or [PHONE], and every other character is kept. Aliases stay as written: a hero's or villain's common name
is public, like a stage name (2026-11-07). The checks below rebuild the redaction in Python from
silver and the mention key, and look for anything that still reads like a SID or a phone number.
"""
import random
import re

import pytest

from lakehouse import lake

MENTIONS = "/lake/landing/universe/M/mention_key/incident_report/*.parquet"
LABELS = {"person_name": "[PERSON NAME]", "sid": "[SID]", "birth_date": "[BIRTH DATE]", "phone": "[PHONE]"}
SAMPLE = 3000


@pytest.fixture(scope="module")
def con():
    """A read-only connection to the lake."""
    c = lake.lake_ro_connect()
    yield c
    c.close()


def redact(narrative, mentions):
    """The narrative with each personal (start, end, kind) span replaced by its label, and each alias kept as
    written: the rule, written plainly."""
    out, at = [], 0
    for start, end, kind in sorted(mentions):
        out += [narrative[at:start], narrative[start:end] if kind == "alias" else LABELS[kind]]
        at = end
    return "".join(out) + narrative[at:]


def test_every_silver_report_is_there_once(con):
    """Same reports as silver, one row each, with the fight, kind, filing time and month carried over."""
    silver = con.execute("SELECT count(*) FROM lake.world_silver.incident_report").fetchone()[0]
    gold, ids = con.execute("SELECT count(*), count(DISTINCT incident_report_id) "
                            "FROM lake.world_gold.incident_report_redacted").fetchone()
    assert gold == ids == silver == 200_000
    differs = con.execute("""
        SELECT count(*) FROM lake.world_silver.incident_report s
        JOIN lake.world_gold.incident_report_redacted g USING (incident_report_id)
        WHERE (s.incident_id, s.report_kind, s.filed_at, s.incident_month)
              IS DISTINCT FROM (g.incident_id, g.report_kind, g.filed_at, g.incident_month)""").fetchone()[0]
    assert differs == 0


def test_no_author_and_no_raw_text_column(con):
    """The table has no author (a person) and no narrative but the redacted one."""
    cols = {r[0] for r in con.execute("DESCRIBE lake.world_gold.incident_report_redacted").fetchall()}
    assert cols == {"incident_report_id", "incident_id", "report_kind", "filed_at", "incident_month", "narrative"}


def test_a_sample_matches_the_rule_character_for_character(con):
    """3,000 random reports with mentions, rebuilt in Python from silver and the mention key, match exactly."""
    ids = [r[0] for r in con.execute(f"SELECT DISTINCT incident_report_id FROM read_parquet('{MENTIONS}')").fetchall()]
    picked = random.Random(20261104).sample(ids, SAMPLE)
    con.execute("CREATE TEMP TABLE picked AS SELECT unnest(?) AS incident_report_id", [picked])
    silver = dict(con.execute("SELECT incident_report_id, narrative FROM lake.world_silver.incident_report "
                              "WHERE incident_report_id IN (SELECT incident_report_id FROM picked)").fetchall())
    gold = dict(con.execute("SELECT incident_report_id, narrative FROM lake.world_gold.incident_report_redacted "
                            "WHERE incident_report_id IN (SELECT incident_report_id FROM picked)").fetchall())
    spans = {}
    for rid, start, end, kind in con.execute(
            f"SELECT incident_report_id, start_pos, end_pos, kind FROM read_parquet('{MENTIONS}') "
            "WHERE incident_report_id IN (SELECT incident_report_id FROM picked)").fetchall():
        spans.setdefault(rid, []).append((start, end, kind))
    wrong = [rid for rid in picked if gold[rid] != redact(silver[rid], spans[rid])]
    assert not wrong, f"{len(wrong)} reports differ, e.g. {wrong[:3]}"


def test_reports_without_mentions_are_unchanged(con):
    """A report the key marks nothing personal in (a desk report, "SEE ATTACHED", one naming only aliases, an empty
    one) reads exactly as in silver."""
    differs = con.execute(f"""
        SELECT count(*) FROM lake.world_silver.incident_report s
        JOIN lake.world_gold.incident_report_redacted g USING (incident_report_id)
        WHERE s.incident_report_id NOT IN (SELECT incident_report_id FROM read_parquet('{MENTIONS}') WHERE kind <> 'alias')
          AND s.narrative IS DISTINCT FROM g.narrative""").fetchone()[0]
    assert differs == 0


def test_one_label_per_personal_mention(con):
    """Across every report, the labels number exactly the personal mentions: 816,360 at M (1,893,406 mentions, less
    1,077,046 aliases, which stay as written). No report says [ALIAS] any more."""
    labels = con.execute(
        "SELECT sum(len(regexp_extract_all(narrative, '\\[(PERSON NAME|SID|BIRTH DATE|PHONE)\\]'))) "
        "FROM lake.world_gold.incident_report_redacted").fetchone()[0]
    mentions = con.execute(f"SELECT count(*) FROM read_parquet('{MENTIONS}') WHERE kind <> 'alias'").fetchone()[0]
    assert labels == mentions == 816_360
    assert con.execute("SELECT count(*) FROM lake.world_gold.incident_report_redacted "
                       "WHERE contains(narrative, '[ALIAS]')").fetchone()[0] == 0


@pytest.mark.parametrize("what, pattern", [("a SID", r"SID[ #:]*\d"), ("a 555-01xx phone", r"555[-. ]?01\d\d")])
def test_nothing_still_reads_like_a_sid_or_a_phone(con, what, pattern):
    """No redacted narrative still holds a SID or one of the world's fictional phone numbers."""
    left = con.execute("SELECT count(*) FROM lake.world_gold.incident_report_redacted "
                       "WHERE regexp_matches(narrative, ?)", [pattern]).fetchone()[0]
    assert left == 0, f"{left} narratives still hold {what}"
    assert re.search(pattern, "SID 6172550 and 980.555.0141")   # the pattern itself finds the real formats
