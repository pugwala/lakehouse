"""The world sessions' checker, the parts that need no world: verdicts, blanks and the precision/recall grader.

    pytest -q lakehouse/tests/test_sessions_check.py

Every exercise in lakehouse/sessions/*.ipynb calls lakehouse/sessions/check.py. A number is checked against what the
answer keys say; a result (rows you found) is graded by precision (how many of yours are right) and recall (how many
of the right ones you found). These tests pin the grading itself on small made-up sets; test_world_sessions.py runs the
notebooks on the real world.
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from lakehouse.sessions import check  # noqa: E402


def said(capsys):
    """What the last check printed."""
    return capsys.readouterr().out


def test_a_blank_asks_for_an_answer_and_never_fails(capsys):
    """___ left in place: the check asks for an answer instead of judging it."""
    check.verdict(check.___, 7, "hint")
    assert "Replace ___" in said(capsys)
    check.grade(check.___, {(1, 2)}, 0.9, 0.9, "duplicates", "hint")
    assert "Replace ___" in said(capsys)


def test_a_right_number_passes_and_a_wrong_one_gets_the_hint(capsys):
    """The right number says ✅ with the number; a wrong one says ❌, what was given, and the hint."""
    check.verdict(1760, 1760, "count them")
    assert said(capsys).startswith("✅")
    check.verdict(1761, 1760, "count them")
    out = said(capsys)
    assert out.startswith("❌") and "1761" in out and "count them" in out


def test_score_counts_right_answers_precision_and_recall():
    """4 found, 3 of them right, of 6 true: precision 0.75, recall 0.5."""
    right, precision, recall = check.score({1, 2, 3, 9}, {1, 2, 3, 4, 5, 6})
    assert (right, precision, recall) == (3, 0.75, 0.5)
    assert check.score(set(), {1}) == (0, 0.0, 0.0)


def test_grade_passes_only_when_both_bars_are_met(capsys):
    """✅ needs precision and recall at or above their bars; either short gives ❌ and the numbers."""
    truth = {(i, i + 1) for i in range(100)}
    check.grade(set(list(truth)[:95]), truth, 0.99, 0.95, "pairs", "hint")
    assert said(capsys).startswith("✅")
    check.grade(set(list(truth)[:94]), truth, 0.99, 0.95, "pairs", "hint")
    out = said(capsys)
    assert out.startswith("❌") and "94.0%" in out and "hint" in out
    check.grade(truth | {(500, 501), (502, 503)}, truth, 0.99, 0.95, "pairs", "hint")
    assert said(capsys).startswith("❌")   # precision 100/102 = 98.0%, under 99%


def test_rows_can_be_handed_in_as_a_dataframe_or_any_collection():
    """A DataFrame's named columns, in order, become tuples; a list of tuples or of single values works too."""
    df = pd.DataFrame({"original_id": [5, 6], "dup_id": [1, 2], "extra": [0, 0]})
    assert check.as_set(df, ["dup_id", "original_id"]) == {(1, 5), (2, 6)}
    assert check.as_set([(1, 5), (2, 6)], ["dup_id", "original_id"]) == {(1, 5), (2, 6)}
    assert check.as_set(pd.Series([3, 4, 4]), ["charge_id"]) == {3, 4}
    assert check.as_set([3, 4], ["charge_id"]) == {3, 4}


def test_a_missing_column_says_which(capsys):
    """A DataFrame without a needed column gets told which, instead of a stack trace."""
    check.grade_rows(pd.DataFrame({"dup_id": [1]}), {(1, 5)}, ["dup_id", "original_id"], 0.9, 0.9, "duplicates", "h")
    out = said(capsys)
    assert out.startswith("❌") and "original_id" in out
