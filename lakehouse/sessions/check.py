"""Exercise checkers for course 2's world sessions. Each prints a friendly verdict; nothing here stops a notebook.

A number is checked against what the world's answer keys say. A result, the rows you found, is graded by precision
(how many of yours are right) and recall (how many of the right ones you found), against the keys too: the key is
the world's own record of every defect it was given (answer_key/<table>, mention_key/incident_report), so the checks
never compare you with a stored solution. The keys are read here and nowhere in the notebooks.

    from lakehouse.sessions import check
    from lakehouse.sessions.check import ___
    con = check.world()          # DuckDB, with a view messy_<table> over each messy CSV folder

Mock data only.
"""
import os
from functools import lru_cache
from pathlib import Path

import duckdb
import pandas as pd

WORLD = Path(os.environ.get("WORLD_ROOT", "/lake/landing/universe/M"))


class _Blank:
    """The ___ placeholder in exercises. Replace it with your answer."""

    def __repr__(self):
        """Shown as ___."""
        return "___"


___ = _Blank()
ASK = "✏️  Replace ___ with your answer, then run the cell again."


# ---- Verdicts ------------------------------------------------------------------------------------------------
def verdict(answer, expected, hint, label=""):
    """✅ when answer equals expected (numbers within 0.01), else ❌ with what was given and a hint."""
    if isinstance(answer, _Blank):
        print(ASK)
        return
    ok = answer == expected
    if isinstance(expected, float) and not isinstance(answer, (str, bool)):
        try:
            ok = abs(float(answer) - expected) < 0.01
        except (TypeError, ValueError):
            ok = False
    if ok:
        print(f"✅ Correct{': ' + label if label else ''} ({expected:,})")
    else:
        print(f"❌ Not quite. You have {answer!r}. Hint: {hint}")


def score(found, truth):
    """(right, precision, recall) of a found set against the true set: right = found and true."""
    right = len(found & truth)
    return right, (right / len(found) if found else 0.0), (right / len(truth) if truth else 0.0)


def grade(found, truth, min_precision, min_recall, what, hint):
    """✅ when precision and recall both reach their bars; either way, say how many were right, found and missed."""
    if isinstance(found, _Blank):
        print(ASK)
        return
    right, precision, recall = score(found, truth)
    line = (f"{right:,} of your {len(found):,} {what} are right (precision {precision:.1%}), and you found "
            f"{recall:.1%} of the {len(truth):,} there are")
    if precision >= min_precision and recall >= min_recall:
        print(f"✅ {line}.")
    else:
        print(f"❌ {line}. The bar is precision {min_precision:.0%} and recall {min_recall:.0%}. Hint: {hint}")


def as_set(rows, columns):
    """The rows handed in, as a set: tuples of the named columns (a single value when there's one column). Takes a
    DataFrame, a Series, or any collection of tuples or values. A DataFrame missing a column raises KeyError."""
    if isinstance(rows, pd.DataFrame):
        rows = rows[columns].itertuples(index=False, name=None)
    elif isinstance(rows, pd.Series):
        rows = rows.tolist()
    out = set()
    for r in rows:
        r = tuple(int(x) if hasattr(x, "__index__") else x for x in (r if isinstance(r, tuple) else (r,)))
        out.add(r if len(columns) > 1 else r[0])
    return out


def grade_rows(rows, truth, columns, min_precision, min_recall, what, hint):
    """grade() for rows handed in as a DataFrame or collection, naming a missing column instead of failing."""
    if isinstance(rows, _Blank):
        print(ASK)
        return
    try:
        found = as_set(rows, columns)
    except KeyError:
        print(f"❌ Your result needs the columns {', '.join(columns)}; it has {', '.join(map(str, rows.columns))}.")
        return
    grade(found, truth, min_precision, min_recall, what, hint)


# ---- The world ---------------------------------------------------------------------------------------------
def world():
    """A DuckDB connection with a view messy_<table> over each table's messy CSV folder, every column as text, as a
    source system delivered it. The clean tables and the answer keys aren't there: they're what you're graded on."""
    con = duckdb.connect()
    for folder in sorted((WORLD / "messy").iterdir()):
        con.execute(f"CREATE VIEW messy_{folder.name} AS SELECT * FROM read_csv('{folder}/*.csv', all_varchar = true, "
                    "header = true, quote = '\"', escape = '\"')")
    return con


@lru_cache(maxsize=None)
def _key(table):
    """One table's answer key: id, column_name, kind, as_written, truth (the checker's own connection)."""
    return duckdb.connect().execute(f"SELECT * FROM read_parquet('{WORLD}/answer_key/{table}/*.parquet')").df()


def _keyed(table, column, kinds):
    """The answer-key rows for one column and some kinds."""
    k = _key(table)
    return k[(k.column_name == column) & k.kind.isin(kinds)]


@lru_cache(maxsize=None)
def _mentions():
    """The mention key: one row per personal detail in a narrative, where it is (start_pos, end_pos) and its kind."""
    return duckdb.connect().execute(
        f"SELECT incident_report_id, start_pos, end_pos, kind FROM read_parquet('{WORLD}/mention_key/incident_report/*.parquet')").df()


# ---- World session 1 · Who is who ------------------------------------------------------------------------------
def _duplicates():
    """{(duplicate's id, original's id)} for every person entered twice."""
    k = _key("person")
    k = k[k.kind == "duplicate_person"]
    return {(int(i), int(t)) for i, t in zip(k.id, k.truth)}


def w1_ex1(answer):
    """How many people does matching on SID alone show as entered twice?"""
    dups = {d for d, _ in _duplicates()}
    with_sid = duckdb.connect().execute(
        f"SELECT count(*) FROM read_csv('{WORLD}/messy/person/*.csv', all_varchar = true) "
        "WHERE CAST(person_id AS BIGINT) IN (SELECT unnest(?)) AND sid_number IS NOT NULL", [sorted(dups)]).fetchone()[0]
    verdict(answer, with_sid, "count the rows whose SID already belongs to a row with a lower person_id")


def w1_ex2(answer):
    """How many last names are a stand-in for "don't know" (a token or only spaces), not a name?"""
    verdict(answer, len(_keyed("person", "last_name", ["unknown", "null_token"])),
            "count last_name values that, with spaces and tabs trimmed and in capitals, are '', N/A, UNKNOWN, UNK, ?, NULL or NONE")


def w1_ex3(duplicates):
    """Every person entered twice, as (dup_id, original_id): graded against the key."""
    grade_rows(duplicates, _duplicates(), ["dup_id", "original_id"], 0.99, 0.90, "duplicates",
               "match on SID when there is one; otherwise on cleaned last name, first name and birth date; the "
               "lowest person_id in each match is the original")


# ---- World session 2 · Dates that lie --------------------------------------------------------------------------
def w2_ex1(answer):
    """How many charges' filing dates can't be read at all (a token where the date should be)?"""
    verdict(answer, len(_keyed("charge", "filed_on", ["unknown"])),
            "count filed_on values your read_date() leaves empty (UNK, UNKNOWN, ?, 00/00/0000, ...)")


@lru_cache(maxsize=None)
def _filed_as_written():
    """{(charge_id, date)} for every filing date as it was written, read right: the true date, except where the key
    says a wrong but readable date was written (out_of_order: that date) or none can be read (unknown: left out)."""
    con = duckdb.connect()
    truth = con.execute(f"SELECT charge_id, filed_on FROM read_parquet('{WORLD}/charge/*.parquet')").df()
    k = _keyed("charge", "filed_on", ["unknown", "out_of_order"])
    lost = set(k[k.kind == "unknown"].id.astype(int))
    wrong = {int(i): pd.Timestamp(w).date() for i, w in zip(k[k.kind == "out_of_order"].id, k[k.kind == "out_of_order"].as_written)}
    return {(int(i), wrong.get(int(i), d)) for i, d in zip(truth.charge_id, pd.to_datetime(truth.filed_on).dt.date)
            if int(i) not in lost}


def w2_ex2(dates):
    """Every readable filing date, read right, as (charge_id, filed_on): graded against what was written."""
    if isinstance(dates, pd.DataFrame) and "filed_on" in dates:
        dates = dates.dropna(subset=["filed_on"]).assign(filed_on=pd.to_datetime(dates.filed_on).dt.date)
    grade_rows(dates, _filed_as_written(), ["charge_id", "filed_on"], 0.999, 0.999, "dates",
               "profile the shapes first; a two-digit year at or below 26 is 20xx, above it 19xx")


def w2_ex3(charge_ids):
    """Every charge filed before its fight started, as charge_id: graded against the key."""
    k = _keyed("charge", "filed_on", ["out_of_order"])
    grade_rows(charge_ids, set(k.id.astype(int)), ["charge_id"], 0.99, 0.95, "charges",
               "read both dates (the fight's started_at has its own formats, 12-hour times among them), then "
               "keep the charges whose filed_on is before the fight's date")


# ---- World session 3 · Links that break ------------------------------------------------------------------------
def w3_ex1(answer):
    """How many participants point at a fight that isn't there?"""
    verdict(answer, len(_keyed("participant", "incident_id", ["orphan"])),
            "an anti-join: participants whose incident_id isn't any incident's incident_id")


def w3_ex2(answer):
    """How many participants point at a person who isn't there?"""
    verdict(answer, len(_keyed("participant", "person_id", ["orphan"])),
            "the same anti-join, on person_id against messy_person")


def w3_ex3(repointed):
    """Every participant whose person_id names a duplicate, pointed at the original, as (participant_id,
    person_id): graded against the key."""
    k = _keyed("participant", "person_id", ["duplicate_ref"])
    grade_rows(repointed, {(int(i), int(t)) for i, t in zip(k.id, k.truth)}, ["participant_id", "person_id"],
               0.99, 0.85, "re-pointed links",
               "join participants to your duplicates on person_id = dup_id, and take the original_id")


# ---- World session 4 · Finding the names -----------------------------------------------------------------------
def _spans(kind):
    """{(incident_report_id, start, end)} for one kind of personal detail in the mention key."""
    m = _mentions()
    m = m[m.kind == kind]
    return {(int(i), int(s), int(e)) for i, s, e in zip(m.incident_report_id, m.start_pos, m.end_pos)}


SPAN = ["incident_report_id", "start", "end"]


def w4_ex1(found):
    """Every SID in the reports, as (incident_report_id, start, end)."""
    grade_rows(found, _spans("sid"), SPAN, 0.99, 0.99, "SIDs",
               "seven spellings: SID 1234567, SID# , SID no. , SID NO. , SID: , sid: and S.I.D. ; the span covers "
               "the label and the number")


def w4_ex2(found):
    """Every phone number in the reports."""
    grade_rows(found, _spans("phone"), SPAN, 0.99, 0.99, "phone numbers",
               "three formats: 201-555-0100, 201.555.0100 and (201) 555-0100")


def w4_ex3(found):
    """Every birth date in the reports (the date only, after DOB)."""
    grade_rows(found, _spans("birth_date"), SPAN, 0.99, 0.90, "birth dates",
               "a birth date follows 'DOB '; capture only the date (group 1), in any of its formats")


def w4_ex4(found):
    """Every person's name in the reports."""
    grade_rows(found, _spans("person_name"), SPAN, 0.95, 0.85, "names",
               "find a name by the words before it (identified as, my name is, records check:, bystander, "
               "victim, or in brackets), then every other place that same name appears in the report")
