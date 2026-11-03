"""Acceptance test for the public repos: no Lunch & Learn branding, and no link to the old course repo.

    pytest lakehouse/acceptance/test_branding.py     # on a git checkout (needs git; no running stack)

Course 2 (pugwala/lakehouse) and course 1 (pugwala/homelake, the submodule course1/) are the lab's own repos. This
checks every file git tracks here; course 1's files are checked by the same test in homelake. Functional names
stay as they are, because things that exist depend on them: the VM folder ~/lunch-and-learn-data-cleansing (the
live stack runs from it), the Databricks volume lunch_and_learn and the lnl package.
"""
import re
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
BRANDING = re.compile(r"lunch\s*(?:&|&amp;|and)\s*learn|lunch-and-learn(?!-data-cleansing)", re.IGNORECASE)
OLD_REPO_LINK = re.compile(r"github\.com/pugwala/lunch-and-learn", re.IGNORECASE)


SELF = Path(__file__).resolve().relative_to(REPO).as_posix()   # this file has to name what it forbids


def texts():
    """{path: text} for every file git tracks here, PDFs, this test and the course1/ submodule left out."""
    names = subprocess.run(["git", "-c", "safe.directory=*", "-C", str(REPO), "ls-files"], check=True,
                           capture_output=True, text=True).stdout.split("\n")
    return {n: (REPO / n).read_text(errors="ignore") for n in names
            if n and (REPO / n).is_file() and not n.endswith(".pdf") and n != SELF}   # course1/ is a submodule: a folder


def hits(pattern):
    """Each "path:line" whose text matches pattern."""
    return [f"{path}:{i}" for path, text in texts().items()
            for i, line in enumerate(text.splitlines(), 1) if pattern.search(line)]


def test_no_lunch_and_learn_branding():
    """No title, description, tag or app name calls this the Lunch & Learn course."""
    assert hits(BRANDING) == []


def test_links_point_at_homelake():
    """Every GitHub link to the repo, the alert runbook links included, opens homelake, not the old repo."""
    assert hits(OLD_REPO_LINK) == []
