"""Acceptance test for course 2's world sessions (chunk 11): four notebooks on the expanded world's messy files.

    docker compose --profile core exec -T jupyter pytest -q lakehouse/acceptance/test_world_sessions.py

Each session in lakehouse/sessions/ teaches one cleaning skill that a single flat table couldn't: who is who
(duplicate people), dates that lie, links that break, and finding the names in free text. Every 🧪 exercise ends in a
check from lakehouse/sessions/check.py, graded against the world's answer keys, never against a stored solution.

Each notebook is run twice, top to bottom, in a real kernel:
  - as delivered, with every ___ blank in place: it runs without an error, and every check asks for an answer;
  - with the answers from its own "Answers" section filled in: every check passes (✅), none fails.
So the answers at the bottom really are right, on the world as it is today, and a student who follows them gets there.
"""
import re
from pathlib import Path

import nbformat
import pytest
from nbclient import NotebookClient

SESSIONS = Path(__file__).resolve().parents[1] / "sessions"
NOTEBOOKS = sorted(SESSIONS.glob("world_*.ipynb"))
BLANK_LINE = re.compile(r"^(\s*)(\w+) = ___\b.*$", re.M)
ANSWER = re.compile(r"```python\n(.*?)```", re.S)


def answers(nb) -> dict:
    """{name: code} from the notebook's Answers section: each fenced block assigns one name (its first line)."""
    start = next(i for i, c in enumerate(nb.cells) if c.cell_type == "markdown" and c.source.startswith("## Answers"))
    out = {}
    for cell in nb.cells[start:]:
        if cell.cell_type == "markdown":
            for code in ANSWER.findall(cell.source):
                name = re.match(r"\s*(\w+)\s*=", code).group(1)
                out[name] = code.rstrip("\n")
    return out


def filled(nb):
    """A copy of the notebook with each `name = ___` line replaced by that name's answer."""
    nb = nbformat.reads(nbformat.writes(nb), as_version=4)
    given = answers(nb)
    for cell in nb.cells:
        if cell.cell_type == "code":
            cell.source = BLANK_LINE.sub(lambda m: "\n".join(m.group(1) + line for line in given[m.group(2)].split("\n"))
                                         if m.group(2) in given else m.group(0), cell.source)
    return nb


def run(nb):
    """Run a notebook top to bottom in its own folder; returns every check's printed verdict, in order."""
    NotebookClient(nb, timeout=900, kernel_name="python3", resources={"metadata": {"path": str(SESSIONS)}}).execute()
    said = []
    for cell in nb.cells:
        if cell.cell_type == "code" and "check." in cell.source and "_ex" in cell.source:
            text = "".join(o.get("text", "") for o in cell.get("outputs", []) if o.get("output_type") == "stream")
            said.append(text.strip())
    return said


def test_there_are_four_sessions():
    """World sessions 1 to 4, each a notebook in lakehouse/sessions/."""
    assert [p.name for p in NOTEBOOKS] == ["world_1_who_is_who.ipynb", "world_2_dates_that_lie.ipynb",
                                           "world_3_links_that_break.ipynb", "world_4_finding_names.ipynb"]


@pytest.mark.parametrize("path", NOTEBOOKS, ids=lambda p: p.stem)
def test_every_exercise_has_an_answer_at_the_bottom(path):
    """Each `name = ___` blank has its answer in the Answers section, and there are at least three exercises."""
    nb = nbformat.read(path, as_version=4)
    blanks = {m.group(2) for c in nb.cells if c.cell_type == "code" for m in BLANK_LINE.finditer(c.source)}
    assert len(blanks) >= 3 and blanks <= set(answers(nb)), blanks - set(answers(nb))


@pytest.mark.parametrize("path", NOTEBOOKS, ids=lambda p: p.stem)
def test_as_delivered_it_runs_and_every_check_asks_for_an_answer(path):
    """Blanks in place: no error anywhere, and each check prints its 'Replace ___' prompt."""
    said = run(nbformat.read(path, as_version=4))
    assert said and all("Replace ___" in s for s in said), said


@pytest.mark.parametrize("path", NOTEBOOKS, ids=lambda p: p.stem)
def test_with_the_answers_filled_in_every_check_passes(path):
    """The Answers section's code in place of each blank: every check says ✅, graded against the answer keys."""
    said = run(filled(nbformat.read(path, as_version=4)))
    assert said and all(s.startswith("✅") for s in said), said
