"""Course 2 in its own repo (Priority 8, 2026-11-03): course 1 arrives as a pinned submodule, never as folders of its own.

    pytest lakehouse/tests/test_course1_pin.py     # inside the jupyter container (or the CI sandbox)

Course 2 is this repo (pugwala/lakehouse). Course 1, sessions 1-7 with lnl, the generator, the notebooks and the
Facilitator Guide, is the git submodule course1/, pinned at homelake's tag course1-v1.3. The tests check that:
  - nothing of course 1 sits beside lakehouse/: it lives only in course1/, which .gitmodules takes from homelake;
  - everything that runs course 1's code finds it in course1/: the handoff's generator, notebook_smoke's notebooks,
    the Jupyter image's requirements and wheels, and the Python path Compose and CI set;
  - course 2's own runtime (lake.py) imports nothing from course 1.
The pin itself (the submodule's commit is the tag's) needs git, so it is checked on a checkout:
lakehouse/acceptance/test_course1_tag.py.
"""
import configparser
import re
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from lakehouse import course1_addon as addon, lake  # noqa: E402
sys.path.insert(0, str(REPO / "course1"))
from lnl import publish  # noqa: E402

COURSE1_PARTS = ["lnl", "generator", "notebooks", "FACILITATOR_GUIDE.md", "requirements.txt", "wheels"]


def test_course_1_lives_only_in_its_submodule():
    """lnl, the generator, the notebooks, the guide, the requirements and the wheels are in course1/, not at the root."""
    assert addon.COURSE1_ROOT == REPO / "course1"
    for part in COURSE1_PARTS:
        assert not (REPO / part).exists(), f"{part} sits beside lakehouse/: course 1 belongs in course1/"
        assert (addon.COURSE1_ROOT / part).exists(), f"course1/{part} is missing: is the submodule checked out?"


def test_gitmodules_takes_course_1_from_homelake_at_its_tag():
    """.gitmodules declares course1/ from pugwala/homelake; the add-on names the tag it is pinned at."""
    modules = configparser.ConfigParser()
    modules.read(REPO / ".gitmodules")
    assert modules['submodule "course1"']["path"] == "course1"
    assert modules['submodule "course1"']["url"] == "https://github.com/pugwala/homelake.git"
    assert addon.COURSE1_TAG == "course1-v1.3"


def test_everything_that_runs_course_1_finds_it_in_course1():
    """The handoff's publish step is course1/'s own (lnl.publish, running its generator); notebook_smoke runs course1/'s seven sessions plus the bridge notebook;
    the Jupyter image installs course1/'s requirements and wheels; Compose and CI put course1/ on the Python path."""
    assert Path(publish.__file__) == addon.COURSE1_ROOT / "lnl" / "publish.py"
    assert publish.GENERATOR == addon.COURSE1_ROOT / "generator" / "gen_hero_offenders.py"
    assert publish.GENERATOR.is_file()
    notebooks = addon.notebooks()
    assert [p.name for p in notebooks[:7]] == sorted(p.name for p in (addon.COURSE1_ROOT / "notebooks").glob("0*.ipynb"))
    assert len(notebooks) == 8 and all(p.is_file() for p in notebooks)
    assert all(p.parent == addon.COURSE1_ROOT / "notebooks" for p in notebooks[:7])
    assert notebooks[7] == REPO / addon.PIECES["notebooks"][0]
    dockerfile = (REPO / "lakehouse" / "jupyter" / "Dockerfile").read_text()
    assert "COPY course1/requirements.txt " in dockerfile and "COPY course1/wheels/ " in dockerfile
    compose = yaml.safe_load((REPO / "lakehouse" / "compose.yaml").read_text())
    assert compose["x-lake-env"]["PYTHONPATH"].split(":") == ["/home/jovyan/course", "/home/jovyan/course/course1"]
    assert 'PYTHONPATH="$REPO:$REPO/course1"' in (REPO / "lakehouse" / "ci" / "checks.sh").read_text()


def test_course_2s_own_runtime_imports_nothing_from_course_1(monkeypatch, tmp_path):
    """lake.py names no course 1 module, and without LAKE_CATALOG its plain-file lake is in LNL_DATA_DIR."""
    assert not re.search(r"^\s*(from|import)\s+(lnl|generator)\b", (REPO / "lakehouse" / "lake.py").read_text(), re.M)
    monkeypatch.delenv("LAKE_CATALOG", raising=False)
    monkeypatch.setenv("LNL_DATA_DIR", str(tmp_path / "data"))
    assert lake.catalog() == str(tmp_path / "data" / "lake.duckdb")
    assert (tmp_path / "data").is_dir()
