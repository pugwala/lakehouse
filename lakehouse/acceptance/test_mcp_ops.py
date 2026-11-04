"""Acceptance test for the MCP server's pipeline_status and platform_health: is the lakehouse running, and is it well.

    docker compose --profile core exec -T jupyter pytest -q lakehouse/acceptance/test_mcp_ops.py

pipeline_status reads Dagster's GraphQL API with queries only (the server sends no mutation, so it can't launch or stop
anything): every job, its schedule and next run, its latest run and last success, the steps that failed. platform_health
reads Prometheus: the scrape targets and sites, the alerts firing (Watchdog aside), and the VM's vitals and backups.
Answers are checked against Dagster and Prometheus asked directly, and against the VM itself. One test fails
monitoring_selftest on purpose: its alert goes to the selftest topic, never to the phone.
"""
import os
import time
from datetime import datetime

from test_alerting import firing
from test_daily_run import graphql
from test_mcp import LAKEHOUSE, call, prometheus_now
from test_pipeline_metrics import launch

JOBS = {"daily_lake", "lake_housekeeping", "monitoring_selftest", "notebook_smoke", "world_monthly_job",
        "world_refresh"}


def ok(tool, **arguments) -> dict:
    """A tool's result, after checking the call succeeded."""
    is_error, result, text = call(tool, **arguments)
    assert not is_error, text
    return result


def epoch(iso):
    """Seconds since 1970 from an ISO 8601 time with its offset."""
    return datetime.fromisoformat(iso).timestamp()


def runs(job, limit):
    """A job's latest runs from Dagster, newest first: (run id, status)."""
    got = graphql(f'{{ runsOrError(filter: {{pipelineName: "{job}"}}, limit: {limit}) '
                  '{ ... on Runs { results { runId status } } } }')
    return [(r["runId"], r["status"]) for r in got["runsOrError"]["results"]]


# --- pipeline_status --------------------------------------------------------------------------------------------

def test_pipeline_status_lists_every_job_with_its_schedule():
    """Every job (not Dagster's internal __ASSET_JOB), with the cron, zone and state Dagster holds and a next run."""
    got = ok("pipeline_status")
    assert {j["name"] for j in got["jobs"]} == JOBS
    sched = graphql("{ repositoriesOrError { ... on RepositoryConnection { nodes { schedules { pipelineName "
                    "cronSchedule executionTimezone scheduleState { status } } } } } }")
    want = {s["pipelineName"]: s for s in sched["repositoriesOrError"]["nodes"][0]["schedules"]}
    for j in got["jobs"]:
        if j["name"] in want:
            s, w = j["schedule"], want[j["name"]]
            assert (s["cron"], s["timezone"], s["state"]) == (w["cronSchedule"], w["executionTimezone"],
                                                              w["scheduleState"]["status"]), j["name"]
            assert epoch(s["next_run"]) > time.time()
        else:
            assert j["schedule"] is None, j["name"]
    assert all(j["description"] for j in got["jobs"])


def test_pipeline_status_gives_each_jobs_latest_run():
    """The latest run of each job is Dagster's latest, with its status."""
    got = {j["name"]: j for j in ok("pipeline_status")["jobs"]}
    for job in ("daily_lake", "monitoring_selftest"):
        run_id, status = runs(job, 1)[0]
        assert (got[job]["latest_run"]["run_id"], got[job]["latest_run"]["status"]) == (run_id, status)


def test_pipeline_status_last_success_agrees_with_prometheus():
    """daily_lake's last success is the time the run sensor pushed to Prometheus (within a minute)."""
    got = next(j for j in ok("pipeline_status")["jobs"] if j["name"] == "daily_lake")
    pushed = float(prometheus_now('lakehouse_job_last_success_timestamp_seconds{pipeline="daily_lake"}')[0]["value"][1])
    assert abs(epoch(got["last_success"]) - pushed) < 60


def test_pipeline_status_for_one_job_lists_its_recent_runs():
    """job and runs: that job only, its runs newest first, as many as asked."""
    got = ok("pipeline_status", job="monitoring_selftest", runs=3)
    assert [j["name"] for j in got["jobs"]] == ["monitoring_selftest"]
    assert [(r["run_id"], r["status"]) for r in got["jobs"][0]["runs"]] == runs("monitoring_selftest", 3)


def test_pipeline_status_refuses_an_unknown_job():
    """An unknown job lists the real ones."""
    is_error, _, text = call("pipeline_status", job="nightly_everything")
    assert is_error and all(j in text for j in JOBS)


def test_the_server_never_changes_dagster():
    """The server's GraphQL is queries only: no mutation, so no launching, stopping or wiping anything."""
    source = (LAKEHOUSE / "mcp" / "server.py").read_text()
    assert "dagster" in source.casefold() and "mutation" not in source.casefold()


# --- platform_health -------------------------------------------------------------------------------------------

def test_platform_health_lists_every_site_and_target_as_prometheus_sees_them():
    """Sites (probed through Caddy) and scrape targets, up or down, exactly as Prometheus has them."""
    got = ok("platform_health")
    sites = {x["metric"]["site"]: x["value"][1] == "1" for x in prometheus_now('probe_success{job="sites"}')}
    targets = {(x["metric"]["job"], x["metric"]["instance"]): x["value"][1] == "1"
               for x in prometheus_now('up{job!="sites"}')}
    assert {s["name"]: s["up"] for s in got["sites"]} == sites and len(sites) >= 10
    assert {(t["job"], t["instance"]): t["up"] for t in got["targets"]} == targets


def test_platform_health_reports_the_vms_disk_and_memory():
    """/lake's use matches the disk itself (within a point); memory available matches the kernel (within 5)."""
    got = ok("platform_health")["vitals"]
    st = os.statvfs("/lake")
    used = 100 * (1 - st.f_bavail / st.f_blocks)
    assert abs(got["disk_used_pct"]["/lake"] - used) < 1
    assert 0 < got["disk_used_pct"]["/"] < 100
    info = dict(line.split(":", 1) for line in open("/proc/meminfo"))
    avail = 100 * int(info["MemAvailable"].split()[0]) / int(info["MemTotal"].split()[0])
    assert abs(got["memory_available_pct"] - avail) < 5


def test_platform_health_reports_backups_and_the_certificate():
    """Backup ages and the certificate's days left are Prometheus's figures."""
    got = ok("platform_health")["vitals"]
    pushed = float(prometheus_now("lakehouse_backup_last_success_timestamp_seconds")[0]["value"][1])
    assert abs(got["catalog_backup_age_hours"] - (time.time() - pushed) / 3600) < 0.1
    assert got["offsite_backup_age_hours"] is not None and got["restore_drill_age_days"] is not None
    assert 0 < got["certificate_days_left"] < 120


def test_a_healthy_lakehouse_reports_healthy():
    """Nothing firing but Watchdog (the always-on heartbeat): healthy, no alerts, and the heartbeat noted."""
    assert firing() == {"Watchdog"}, f"something is firing: {firing()}"
    got = ok("platform_health")
    assert got["status"] == "healthy" and got["alerts"] == [] and got["watchdog"] is True


def test_a_failed_job_shows_in_both_tools_until_it_succeeds():
    """monitoring_selftest set to fail: pipeline_status names the failed step; once JobFailing fires, platform_health
    is critical with the alert and its runbook. A success clears both."""
    assert launch("monitoring_selftest", {"ops": {"selftest": {"config": {"fail": True}}}}) == "FAILURE"
    job = ok("pipeline_status", job="monitoring_selftest", runs=1)["jobs"][0]
    assert job["latest_run"]["status"] == "FAILURE" and job["latest_run"]["failed_steps"] == ["selftest"]
    deadline = time.time() + 240
    while "JobFailing" not in {a["name"] for a in ok("platform_health")["alerts"]}:
        assert time.time() < deadline, "JobFailing never showed in platform_health"
        time.sleep(5)
    got = ok("platform_health")
    alert = next(a for a in got["alerts"] if a["name"] == "JobFailing")
    assert got["status"] == "critical" and alert["severity"] == "critical"
    assert "monitoring_selftest" in alert["summary"] and alert["runbook"].endswith("/runbooks/JobFailing.md")
    assert epoch(alert["since"]) <= time.time()
    assert launch("monitoring_selftest", {"ops": {"selftest": {"config": {"fail": False}}}}) == "SUCCESS"
    job = ok("pipeline_status", job="monitoring_selftest", runs=1)["jobs"][0]
    assert job["latest_run"]["status"] == "SUCCESS" and job["latest_run"]["failed_steps"] == []
    deadline = time.time() + 240
    while ok("platform_health")["alerts"]:
        assert time.time() < deadline, "JobFailing never cleared from platform_health"
        time.sleep(5)
    assert ok("platform_health")["status"] == "healthy"
