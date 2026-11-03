"""Course 2's enterprise track helpers: names, SQL that prints itself, landing handed-over deliveries, finding
course 1's pipeline, and the job.

Runs on a Databricks workspace with Unity Catalog, in the schema course 1 built (settings.py names it the same way).
Course 2 never imports course 1's code or runs its generator: course 1's 02_pipeline leaves the pipeline, its tables
and a handoff folder of deliveries with a fingerprinted manifest; these helpers find the pipeline by name and land a
delivery only when its fingerprint matches. Everything Databricks-specific is imported inside the function that
needs it, so the delivery helpers also run (and are tested) off Databricks.
"""
import hashlib
import json
import os
import re
import shutil
import textwrap
import time
from pathlib import Path

import settings

TRACK = Path(__file__).resolve().parent              # this folder: enterprise/ in course 2's Git folder
VALIDATE_NOTEBOOK = "tasks/validate_quality"         # the job's second task, relative to TRACK
LANDING_FOLDER = "hero_offenders"                    # course 1's pipeline reads every file in here
HANDOFF_FOLDER = "handoff/deliveries"                # where course 1's 02_pipeline staged the next deliveries
TERMINAL_UPDATE_STATES = {"COMPLETED", "FAILED", "CANCELED"}


# ---- Names -----------------------------------------------------------------------------------------
def _spark():
    """The notebook's Spark session."""
    from pyspark.sql import SparkSession
    return SparkSession.getActiveSession() or SparkSession.builder.getOrCreate()


def user_email() -> str:
    """Who is running the notebook."""
    return _spark().sql("SELECT current_user()").first()[0]


def user_slug() -> str:
    """The user name part of the email, safe in object names (the same rule course 1 uses)."""
    return re.sub(r"[^a-z0-9]+", "_", user_email().split("@")[0].lower()).strip("_")


def names() -> dict:
    """Every name the track uses, built from settings.py. The schema, volume and pipeline names follow course 1's
    rules, so they point at what course 1 built."""
    slug = user_slug()
    catalog = settings.ENTERPRISE_CATALOG
    schema = settings.ENTERPRISE_SCHEMA.format(user=slug)
    fq = f"{catalog}.{schema}"
    volume = f"/Volumes/{catalog}/{schema}/{settings.ENTERPRISE_VOLUME}"
    return {
        "catalog": catalog, "schema": schema, "fq": fq,
        "volume_name": f"{fq}.{settings.ENTERPRISE_VOLUME}", "volume": volume,
        "landing": f"{volume}/{LANDING_FOLDER}", "rejected": f"{volume}/rejected",
        "handoff": f"{volume}/{HANDOFF_FOLDER}",
        "pipeline": f"lnl_hero_offenders_{slug}", "job": f"lnl_hero_offenders_daily_{slug}",
        # A group nobody is in, so race and religion stay masked until a real group is configured
        "restricted_group": settings.RESTRICTED_GROUP or "lnl-restricted-group-not-configured",
    }


def track_paths() -> dict:
    """This folder as a file path (/Workspace/...) and as a workspace object path (/Users/...)."""
    fs = str(TRACK)
    ws = fs[len("/Workspace"):] if fs.startswith("/Workspace/") else fs
    return {"fs": fs, "ws": ws}


def prepare(step: int, title: str) -> dict:
    """Run at the top of every course 2 enterprise notebook: checks this is Databricks and the settings are filled
    in, prints who and where, and returns the names."""
    if "DATABRICKS_RUNTIME_VERSION" not in os.environ and not Path("/Workspace").is_dir():   # course 1's test too
        raise RuntimeError("The enterprise track runs on an enterprise Databricks workspace (Unity Catalog).")
    if step > 0 and not settings.ENTERPRISE_CATALOG:
        raise RuntimeError("Set ENTERPRISE_CATALOG in enterprise/settings.py first (the catalog course 1 used). "
                           "00_preflight shows what you can use.")
    n = names() if settings.ENTERPRISE_CATALOG else {}
    print(f"Course 2, enterprise track {step}: {title}")
    print(f"  Runtime     : {os.environ.get('DATABRICKS_RUNTIME_VERSION', 'serverless')}")
    print(f"  You         : {user_email()}")
    if n:
        print(f"  Schema      : {n['fq']}")
        print(f"  Landing     : {n['landing']}")
    print("  Mock data only. Never point these notebooks at real offender data without the data owner's approval.")
    return n


def sql(statement: str, quiet: bool = False):
    """Run one SQL statement, printing it first, so every step is SQL you can read and reuse."""
    text = textwrap.dedent(statement).strip()
    if not quiet:
        print(text + ";\n")
    return _spark().sql(text)


def set_tags(statement: str):
    """Run one SET TAGS statement. If the account already defines one of these keys as a governed tag, you need
    ASSIGN on it and one of its allowed values; the course carries on without the tag instead of stopping."""
    try:
        return sql(statement, quiet=True)
    except Exception as exc:
        print(f"⚠️  Tag not set ({str(exc).splitlines()[0][:140]}). If this key is a governed tag in your "
              "account, it needs ASSIGN permission and an allowed value. The rest of the notebook works without it.")


def check(label: str, ok, detail: str = "") -> bool:
    """One line of a checklist: ✅ passed, ⚠️ needs attention."""
    print(f"{'✅' if ok else '⚠️ '} {label}{': ' + detail if detail else ''}")
    return bool(ok)


# ---- Deliveries course 1 handed over -----------------------------------------------------------------
def handed_over(n: dict) -> dict:
    """The manifest course 1's 02_pipeline wrote next to the deliveries it staged: each file's rows and SHA-256."""
    path = Path(n["handoff"]) / "manifest.json"
    if not path.is_file():
        raise ValueError(f"No handed-over deliveries at {path.parent}: run course 1's 02_pipeline to the end "
                         "(section 5 stages them).")
    return json.loads(path.read_text())


def land_delivery(n: dict, file_name: str) -> str:
    """Land one handed-over delivery: check it's in course 1's manifest and its bytes match the fingerprint, then copy
    it into the landing folder the pipeline reads. A delivery that isn't listed, or that changed, is refused and
    nothing lands. Returns the landed path."""
    files = handed_over(n)["files"]
    if file_name not in files:
        raise ValueError(f"{file_name} wasn't handed over (course 1 staged {', '.join(sorted(files))}).")
    source = Path(n["handoff"]) / file_name
    if hashlib.sha256(source.read_bytes()).hexdigest() != files[file_name]["sha256"]:
        raise ValueError(f"{file_name} doesn't match the fingerprint course 1 recorded: not landing it.")
    target = Path(n["landing"]) / file_name
    if target.exists():
        print(f"Already landed: {target}")
        return str(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    print(f"Landed {file_name} ({files[file_name]['rows']:,} records, fingerprint checked): {target}")
    return str(target)


def move_to_rejected(n: dict, file_name: str) -> str:
    """Take a delivery out of the landing folder, keeping it for the data owner."""
    source, rejected = Path(n["landing"]) / file_name, Path(n["rejected"])
    rejected.mkdir(parents=True, exist_ok=True)
    shutil.move(str(source), str(rejected / file_name))     # copy + delete when a plain rename isn't supported
    print(f"Moved {file_name} to {rejected}")
    return str(rejected / file_name)


# ---- Course 1's pipeline -------------------------------------------------------------------------------
def _workspace():
    """A Databricks SDK client, signed in as you."""
    from databricks.sdk import WorkspaceClient
    return WorkspaceClient()


def find_pipeline(n: dict) -> str:
    """The ID of the pipeline course 1's 02_pipeline created, found by its name. Course 2 runs it but never
    changes how it's defined: that's course 1's."""
    w = _workspace()
    found = [p for p in w.pipelines.list_pipelines(filter=f"name LIKE '{n['pipeline']}'") if p.name == n["pipeline"]]
    if not found:
        raise RuntimeError(f"No pipeline named {n['pipeline']}: run course 1's 02_pipeline first, with the same "
                           "catalog and schema as enterprise/settings.py.")
    print(f"Course 1's pipeline: {n['pipeline']} ({found[0].pipeline_id})")
    return found[0].pipeline_id


def run_pipeline(pipeline_id: str, full_refresh: bool = False, timeout_minutes: int = 40) -> dict:
    """Start one update and wait for it to finish. Returns {'state', 'update_id'}."""
    w = _workspace()
    update_id = w.pipelines.start_update(pipeline_id, full_refresh=full_refresh).update_id
    print(f"Update {update_id} started{' (full refresh)' if full_refresh else ''}...", end=" ", flush=True)
    deadline = time.time() + timeout_minutes * 60
    state = None
    while time.time() < deadline:
        state = w.pipelines.get_update(pipeline_id, update_id).update.state.value
        if state in TERMINAL_UPDATE_STATES:
            break
        time.sleep(15)
    print(state)
    return {"state": state, "update_id": update_id}


# ---- The job ---------------------------------------------------------------------------------------
def _notebook_path(relative: str) -> str:
    """Workspace path of a notebook in this folder, with or without the .ipynb extension, whichever exists."""
    w = _workspace()
    base = f"{track_paths()['ws']}/{relative}"
    for candidate in (base, base + ".ipynb"):
        try:
            w.workspace.get_status(candidate)
            return candidate
        except Exception:
            continue
    raise FileNotFoundError(f"Can't find the notebook {relative} in course 2's enterprise folder.")


def job_settings(n: dict, pipeline_id: str) -> dict:
    """The daily job: refresh course 1's pipeline, then run course 2's quality task; failures go to email and the
    notification destinations named in settings.py. Paused until you turn it on."""
    from databricks.sdk.service import jobs as J
    w = _workspace()
    emails = settings.ALERT_EMAILS or [user_email()]
    destinations = [d for d in w.notification_destinations.list() if d.display_name in settings.ALERT_DESTINATIONS]
    missing = set(settings.ALERT_DESTINATIONS) - {d.display_name for d in destinations}
    if missing:
        print(f"⚠️  Notification destinations not found (ask a workspace admin): {sorted(missing)}")
    validate = J.Task(
        task_key="validate_quality", depends_on=[J.TaskDependency(task_key="refresh_pipeline")],
        notebook_task=J.NotebookTask(notebook_path=_notebook_path(VALIDATE_NOTEBOOK),
                                     base_parameters={"run_id": "{{job.run_id}}", "track_root": track_paths()["fs"]},
                                     source=J.Source.WORKSPACE),
    )
    if not settings.ENTERPRISE_SERVERLESS:
        validate.existing_cluster_id = settings.ENTERPRISE_CLUSTER_ID
    return {
        "name": n["job"],
        "description": "Homelake course 2: refresh course 1's mock-data pipeline, then check data quality.",
        "tasks": [J.Task(task_key="refresh_pipeline", pipeline_task=J.PipelineTask(pipeline_id=pipeline_id)), validate],
        "schedule": J.CronSchedule(quartz_cron_expression="0 50 5 * * ?", timezone_id="America/Chicago",
                                   pause_status=J.PauseStatus.PAUSED),
        "email_notifications": J.JobEmailNotifications(on_failure=emails, no_alert_for_skipped_runs=True),
        "webhook_notifications": J.WebhookNotifications(on_failure=[J.Webhook(id=d.id) for d in destinations])
        if destinations else None,
        "max_concurrent_runs": 1,
        "tags": {"project": "homelake", "data": "mock"},
    }


def ensure_job(n: dict, pipeline_id: str) -> int:
    """Create the job, or replace its settings if it already exists (run history is kept). Returns its ID."""
    from databricks.sdk.service import jobs as J
    w = _workspace()
    job_spec = job_settings(n, pipeline_id)
    existing = [j for j in w.jobs.list(name=n["job"])]
    if existing:
        job_id = existing[0].job_id
        w.jobs.reset(job_id, new_settings=J.JobSettings(**job_spec))
        print(f"Updated job {n['job']} ({job_id})")
    else:
        job_id = w.jobs.create(**job_spec).job_id
        print(f"Created job {n['job']} ({job_id})")
    return job_id


def run_job(job_id: int, timeout_minutes: int = 60):
    """Run the job now and wait. Returns the finished run (check run.state.result_state)."""
    w = _workspace()
    run_id = w.jobs.run_now(job_id).run_id
    print(f"Run {run_id} started...", end=" ", flush=True)
    deadline = time.time() + timeout_minutes * 60
    run = w.jobs.get_run(run_id)
    while time.time() < deadline and run.state.life_cycle_state.value not in ("TERMINATED", "SKIPPED", "INTERNAL_ERROR"):
        time.sleep(20)
        run = w.jobs.get_run(run_id)
    result = run.state.result_state.value if run.state.result_state else run.state.life_cycle_state.value
    print(result)
    for task in run.tasks or []:
        state = task.state.result_state.value if task.state and task.state.result_state else "-"
        print(f"  {task.task_key:18} {state}")
    print(f"  Run page: {run.run_page_url}")
    return run
