"""Acceptance test for homelake, Ian's own lab copy of the course repo: no Lunch & Learn branding, and every
link to the repo points at homelake.

    docker run --rm -u "$(id -u)" -v ~/homelake:/repo -w /repo --entrypoint pytest lnl-jupyter:local -q -p no:cacheprovider lakehouse/acceptance/test_homelake.py

Functional names stay as they are, because things that exist depend on them: the VM folder
~/lunch-and-learn-data-cleansing (the live stack runs from it), the Databricks volume lunch_and_learn, the lnl
package, and the cleanup notebook's search for old copies of the old repo. docs/student-handout.pdf is binary and
is not checked here.
"""
import re
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
BRANDING = re.compile(r"lunch\s*(?:&|&amp;|and)\s*learn|lunch-and-learn(?!-data-cleansing)", re.IGNORECASE)
OLD_REPO_LINK = re.compile(r"github\.com/pugwala/lunch-and-learn", re.IGNORECASE)


SELF = Path(__file__).resolve().relative_to(REPO).as_posix()   # this file has to name what it forbids


def texts():
    """{path: text} for every file git tracks, PDFs and this test itself left out."""
    names = subprocess.run(["git", "-c", "safe.directory=*", "-C", str(REPO), "ls-files"], check=True,
                           capture_output=True, text=True).stdout.split("\n")
    return {n: (REPO / n).read_text(errors="ignore") for n in names if n and not n.endswith(".pdf") and n != SELF}


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
