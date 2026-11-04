"""The Databricks enterprise track, split at the course boundary (Priority 8 follow-up, 2026-11-03).

    pytest lakehouse/tests/test_enterprise_track.py     # inside the jupyter container (or the CI sandbox)

Course 1 keeps 00_preflight (trimmed to what 01 and 02 need), 01_unity_catalog and 02_pipeline sections 1-4, then hands
over: its notebook 02 stages the next deliveries in a handoff folder of your volume, with a fingerprinted manifest.
Course 2 (enterprise/ in this repo) owns everything after that: its own preflight, 02b (the next delivery,
incremental), 03 governance, 04 the job and alerts, 05 monitoring, the job's quality task and a job-only bundle. It
has its own helpers and settings, finds course 1's pipeline by name, and lands only deliveries course 1 handed over;
it never imports course 1's code or runs its generator (Databricks Git folders may not check out submodules).

None of this runs Databricks: the notebooks are checked as files, and the delivery handoff is run for real on a
temporary folder standing in for the volume.
"""
import ast
import json
import re
import sys
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[2]
COURSE1 = REPO / "course1"
TRACK1 = COURSE1 / "enterprise"
TRACK2 = REPO / "enterprise"
sys.path.insert(0, str(TRACK2))

COURSE2_NOTEBOOKS = ["00_preflight", "02b_incremental", "03_governance", "04_job_and_alerts", "05_monitoring",
                     "tasks/validate_quality"]


def cells(path: Path, kind: str = "code") -> list[str]:
    """The source of each cell of one kind in a notebook."""
    return ["".join(c["source"]) for c in json.loads(path.read_text())["cells"] if c["cell_type"] == kind]


def headings(path: Path) -> list[str]:
    """The notebook's ## headings, in order."""
    return [line for text in cells(path, "markdown") for line in text.splitlines() if line.startswith("## ")]


def functions(path: Path) -> set[str]:
    """Names of the top-level functions a Python file defines."""
    return {n.name for n in ast.parse(path.read_text()).body if isinstance(n, ast.FunctionDef)}


# ---- Course 1: what stays, and the handover ---------------------------------------------------------
def test_course_1_keeps_only_its_three_notebooks_and_the_pipeline():
    """00, 01 and 02 stay with the pipeline code; 03, 04, 05 and the job's task moved to course 2."""
    assert sorted(p.name for p in TRACK1.glob("*.ipynb")) == ["00_preflight.ipynb", "01_unity_catalog.ipynb",
                                                             "02_pipeline.ipynb"]
    assert not (TRACK1 / "tasks").exists()
    assert (TRACK1 / "pipeline" / "hero_offenders.py").is_file()


def test_course_1s_pipeline_notebook_ends_by_handing_over_the_next_deliveries():
    """Sections 1-4 as before, then a section 5 that stages the deliveries for course 2 instead of landing one."""
    nb = TRACK1 / "02_pipeline.ipynb"
    assert [h.split(".")[0] for h in headings(nb)[:5]] == ["## 1", "## 2", "## 3", "## 4", "## 5"]
    assert "hand" in headings(nb)[4].lower()
    code = "\n".join(cells(nb))
    assert "ent.stage_deliveries(N)" in code and "land_batch" not in code


def test_course_1s_preflight_checks_only_what_01_and_02_need():
    """No notification destinations, system tables or the restricted group: those checks moved with 03-05."""
    text = (TRACK1 / "00_preflight.ipynb").read_text()
    for gone in ["notification_destinations", "system.access", "system.lakeflow", "RESTRICTED_GROUP",
                 "ALERT_DESTINATIONS"]:
        assert gone not in text, gone
    assert "ANALYST_GROUP" in text   # 01's grants still use it


def test_course_1s_helpers_hand_over_and_no_longer_run_the_job():
    """lnl.enterprise stages deliveries; the job, the later deliveries and the rejected folder are course 2's."""
    names = functions(COURSE1 / "lnl" / "enterprise.py")
    assert "stage_deliveries" in names
    assert not names & {"land_batch", "move_to_rejected", "job_settings", "ensure_job", "run_job"}
    config = (COURSE1 / "lnl" / "config.py").read_text()
    assert "ANALYST_GROUP" in config and not re.search(r"^(RESTRICTED_GROUP|ALERT_EMAILS|ALERT_DESTINATIONS)\b",
                                                       config, re.M)


def test_course_1s_bundle_declares_only_the_pipeline():
    """The job moved to course 2's bundle."""
    bundle = yaml.safe_load((TRACK1 / "databricks.yml").read_text())
    assert set(bundle["resources"]) == {"pipelines"}


# ---- Course 2: its own track ------------------------------------------------------------------------
def test_course_2_has_its_track():
    """The notebooks, the job's task, its helpers and settings, the bundle and a README."""
    for name in COURSE2_NOTEBOOKS:
        assert (TRACK2 / f"{name}.ipynb").is_file(), name
    for name in ["helpers.py", "settings.py", "databricks.yml", "README.md"]:
        assert (TRACK2 / name).is_file(), name


def test_course_2_never_reaches_into_course_1():
    """No notebook or helper imports lnl or runs course 1's generator; they find their own helpers."""
    reach = re.compile(r"^\s*(from|import)\s+lnl\b|gen_hero_offenders|course1/|lnl/config", re.M)
    for name in COURSE2_NOTEBOOKS:
        for code in cells(TRACK2 / f"{name}.ipynb"):
            assert not reach.search(code), (name, reach.search(code).group(0))
    for name in ["helpers.py", "settings.py"]:
        tree = ast.parse((TRACK2 / name).read_text())
        docstrings = {id(n.body[0].value) for n in ast.walk(tree)
                      if isinstance(n, (ast.Module, ast.FunctionDef)) and n.body and isinstance(n.body[0], ast.Expr)}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                assert not any(a.name.split(".")[0] in ("lnl", "gen_hero_offenders") for a in node.names), name
            if isinstance(node, ast.ImportFrom):
                assert (node.module or "").split(".")[0] not in ("lnl", "gen_hero_offenders"), name
            if isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in docstrings:
                assert not reach.search(node.value), (name, node.value[:80])


def test_every_helper_and_setting_a_notebook_uses_exists():
    """Each ent.X a notebook calls is a function in helpers.py, and each settings.X a value in settings.py."""
    helpers, settings = functions(TRACK2 / "helpers.py"), set(vars(__import__("settings")))
    for name in COURSE2_NOTEBOOKS:
        code = "\n".join(cells(TRACK2 / f"{name}.ipynb"))
        assert "import helpers as ent" in code, name
        for used in set(re.findall(r"\bent\.(\w+)", code)):
            assert used in helpers, (name, used)
        for used in set(re.findall(r"\bsettings\.([A-Z_]+)", code)):
            assert used in settings, (name, used)


def test_course_2s_notebooks_are_stored_clean():
    """Like course 1's notebooks: no outputs and no execution counts in the repo."""
    for name in COURSE2_NOTEBOOKS:
        for cell in json.loads((TRACK2 / f"{name}.ipynb").read_text())["cells"]:
            if cell["cell_type"] == "code":
                assert cell["outputs"] == [] and cell["execution_count"] is None, name


def test_every_cell_of_both_tracks_has_its_own_id():
    """nbformat 4.5 notebooks give every cell an id (newer nbformat refuses one without); a moved cell keeps the id
    it had in course 1, a new cell gets a fresh one, and no notebook repeats one."""
    for path in [*TRACK1.glob("*.ipynb"), *(TRACK2 / f"{n}.ipynb" for n in COURSE2_NOTEBOOKS)]:
        nb = json.loads(path.read_text())
        ids = [c.get("id") for c in nb["cells"]]
        assert (nb["nbformat"], nb["nbformat_minor"]) == (4, 5) and all(ids) and len(set(ids)) == len(ids), path.name


def test_course_2s_bundle_runs_course_1s_pipeline_found_by_name():
    """A job only: refresh course 1's pipeline (its ID looked up by name), then course 2's quality task."""
    bundle = yaml.safe_load((TRACK2 / "databricks.yml").read_text())
    assert set(bundle["resources"]) == {"jobs"}
    assert "pipeline" in bundle["variables"]["pipeline_id"]["lookup"]
    (job,) = bundle["resources"]["jobs"].values()
    tasks = {t["task_key"]: t for t in job["tasks"]}
    assert tasks["refresh_pipeline"]["pipeline_task"]["pipeline_id"] == "${var.pipeline_id}"
    path = tasks["validate_quality"]["notebook_task"]["notebook_path"]
    assert path.endswith(".ipynb") and (TRACK2 / path).is_file(), path


# ---- The delivery handoff, run for real on a folder standing in for the volume ------------------------
@pytest.fixture(scope="module")
def handed_over(tmp_path_factory):
    """Course 1 stages its deliveries into a temporary volume; returns the names course 2 uses for it."""
    volume = tmp_path_factory.mktemp("volume")
    sys.path.insert(0, str(COURSE1))
    from lnl import enterprise as course1
    course1.stage_deliveries({"volume": str(volume)})
    import helpers
    return {"volume": str(volume), "landing": str(volume / "hero_offenders"), "rejected": str(volume / "rejected"),
            "handoff": str(volume / "handoff" / "deliveries")}, helpers


def test_course_1_stages_two_fingerprinted_deliveries(handed_over):
    """batch_002 (1,000 new records) and batch_003 (1,000, three with a broken offender number), each in the
    manifest with its row count and SHA-256."""
    n, _ = handed_over
    manifest = json.loads((Path(n["handoff"]) / "manifest.json").read_text())
    assert sorted(manifest["files"]) == ["batch_002.csv", "batch_003.csv"]
    import pandas as pd
    for name, bad in [("batch_002.csv", 0), ("batch_003.csv", 3)]:
        df = pd.read_csv(Path(n["handoff"]) / name, dtype=str, keep_default_na=False)
        assert len(df) == manifest["files"][name]["rows"] == 1_000
        assert (df["offender_number"].str.len() == 7).sum() == bad
        assert df["offender_number"].str.match(r"^0?3\d{6}$").all(), name   # new incarcerations: 03xxxxxx


def test_course_2_lands_a_handed_over_delivery_and_refuses_a_changed_one(handed_over):
    """land_delivery copies a delivery into the landing folder only when it matches its fingerprint; a delivery
    that isn't in the manifest, or whose bytes changed, is refused and nothing lands."""
    n, helpers = handed_over
    landed = Path(helpers.land_delivery(n, "batch_002.csv"))
    assert landed == Path(n["landing"]) / "batch_002.csv" and landed.read_bytes() == (Path(n["handoff"]) / "batch_002.csv").read_bytes()
    with pytest.raises(ValueError):
        helpers.land_delivery(n, "batch_009.csv")
    with (Path(n["handoff"]) / "batch_003.csv").open("a") as f:
        f.write("tampered\n")
    with pytest.raises(ValueError):
        helpers.land_delivery(n, "batch_003.csv")
    assert not (Path(n["landing"]) / "batch_003.csv").exists()


def test_course_2_moves_a_bad_delivery_to_rejected(handed_over):
    """move_to_rejected takes a landed delivery out of the landing folder and keeps it for the data owner."""
    n, helpers = handed_over
    helpers.move_to_rejected(n, "batch_002.csv")
    assert not (Path(n["landing"]) / "batch_002.csv").exists()
    assert (Path(n["rejected"]) / "batch_002.csv").is_file()


# ---- Opened outside Databricks: say so, and say what to do ---------------------------------------------------------
def test_course_2_says_how_to_run_it_when_opened_locally(monkeypatch):
    """Opened in the lab's local Jupyter, course 2's notebooks stop at once with a message that says where you are,
    how to open the track in Databricks (a Git folder of this repo), that course 1's track comes first, and what runs
    locally instead."""
    import helpers
    monkeypatch.delenv("DATABRICKS_RUNTIME_VERSION", raising=False)
    monkeypatch.setattr(helpers, "_on_databricks", lambda: False)
    with pytest.raises(RuntimeError) as err:
        helpers.prepare(0, "Preflight")
    msg = str(err.value)
    for words in ["not Databricks", "local Jupyter", "Git folder", "https://github.com/pugwala/lakehouse.git",
                  "enterprise/00_preflight", "https://github.com/pugwala/homelake.git", "course 1's notebooks folder"]:
        assert words in msg, words


def test_course_2_knows_databricks_when_it_sees_it(monkeypatch):
    """The runtime's environment variable is enough to count as Databricks."""
    import helpers
    monkeypatch.setenv("DATABRICKS_RUNTIME_VERSION", "17.3")
    assert helpers._on_databricks()
    monkeypatch.delenv("DATABRICKS_RUNTIME_VERSION")
    assert helpers._on_databricks() == Path("/Workspace").is_dir()


def test_course_1_says_how_to_run_it_when_opened_locally(monkeypatch):
    """Course 1's enterprise notebooks do the same, pointing at a Git folder of course 1's own repo and at its
    session notebooks."""
    sys.path.insert(0, str(COURSE1))
    from lnl import enterprise as course1
    monkeypatch.setattr(course1.env, "IS_DATABRICKS", False)
    with pytest.raises(RuntimeError) as err:
        course1.prepare(0, "Preflight")
    msg = str(err.value)
    for words in ["not Databricks", "Git folder", "https://github.com/pugwala/homelake.git", "enterprise/00_preflight",
                  "notebooks/"]:
        assert words in msg, words
