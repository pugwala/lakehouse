"""Acceptance test for Priority 8: course 1 is pinned at its tag in this checkout.

    pytest lakehouse/acceptance/test_course1_tag.py     # on a git checkout (needs git; no running stack)

lakehouse/tests/test_course1_pin.py checks that course 1 lives only in the submodule course1/ and that everything
finds it there. This checks the pin itself, which needs git (the CI sandbox is a plain copy): the commit this repo
records for course1/ is the commit of homelake's tag course1-v1.0 (course1_addon.COURSE1_TAG), and the checked-out
submodule is at that commit, with nothing changed in it.
"""
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from lakehouse import course1_addon as addon  # noqa: E402


def git(*args: str, cwd: Path = REPO) -> str:
    """Run git in a folder and return its output, stripped."""
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True).stdout.strip()


def test_course_1_is_pinned_at_its_tag():
    """The recorded submodule commit is the tag's commit, the checkout is at it, and nothing in it is changed."""
    mode, recorded, _ = git("ls-files", "-s", "course1").split(maxsplit=2)
    assert mode == "160000", "course1/ is not a submodule"
    tagged = git("rev-parse", f"{addon.COURSE1_TAG}^{{commit}}", cwd=addon.COURSE1_ROOT)
    assert recorded == tagged, f"course1/ is pinned at {recorded[:7]}, but {addon.COURSE1_TAG} is {tagged[:7]}"
    assert git("rev-parse", "HEAD", cwd=addon.COURSE1_ROOT) == tagged
    assert git("status", "--porcelain", cwd=addon.COURSE1_ROOT) == ""
