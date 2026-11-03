# Course 2 · Enterprise Track: The Pipeline in Operation

Course 1's enterprise track ends with a Lakeflow pipeline in your Unity Catalog schema and the next two deliveries handed over in a handoff folder of your volume. This track takes that pipeline the rest of the way, on the agency's enterprise Databricks workspace: the next delivery, who sees what, a scheduled job that pages someone when the data goes bad, and monitoring that catches what nobody wrote a check for.

**Mock data only.** Everything here runs on the course's fictional hero offender records. See [Before you point this at real tables](#before-you-point-this-at-real-tables).

## Where it starts

Course 2 never imports course 1's code or runs its generator, and it doesn't need course 1 in the same Git folder (Databricks Git folders may not check out submodules). It needs what course 1 left in the workspace:

- **your schema**, with the reference tables and the first delivery (course 1's `01_unity_catalog`),
- **the pipeline** `lnl_hero_offenders_<you>` and its tables (course 1's `02_pipeline`, sections 1-4),
- **the handed-over deliveries**: `handoff/deliveries/` in your volume, with `manifest.json` (course 1's `02_pipeline`, section 5).

Course 2 finds the pipeline by name and lands a delivery only when its SHA-256 matches the manifest. `helpers.py` holds course 2's own helpers; `settings.py` its settings.

## What you'll build

| Notebook | What you learn | What it creates | Time |
|---|---|---|---|
| `00_preflight` | Whether course 1 left what this track needs, and what to ask an admin for | nothing (read-only checks) | 10 min |
| `02b_incremental` | Incremental processing: the next delivery, and only it, flows through | `batch_002` landed and processed | 15 min |
| `03_governance` | Column masks, row filters, dynamic views, tags, where ABAC fits, lineage | `mask_demo`, two functions, a mapping table, the published view | 30 min |
| `04_job_and_alerts` | Jobs, task dependencies, schedules, notifications, breaking it on purpose and resolving it | the daily job (schedule paused) and `quality_results` | 30 min |
| `05_monitoring` | Data profiling, anomaly detection, system tables, the path into Prometheus, Grafana and PagerDuty | a data profile on silver, then cleanup | 30 min |

`tasks/validate_quality` isn't one you open: it's the job's second task. It checks the pipeline's output against thresholds, appends the results to `quality_results`, and fails the run (which sends the alerts) when a check fails.

## Setup

1. **Get course 2 into the workspace.** In the workspace, go to **Workspace** → your home folder → **Create** → **Git folder**, and paste `https://github.com/pugwala/lakehouse`. The bundle expects it at `/Workspace/Users/<you>/lakehouse`.
2. **Open `enterprise/settings.py`** and fill it in. The catalog, schema and volume must be the ones course 1 used:

   | Setting | What it is |
   |---|---|
   | `ENTERPRISE_CATALOG`, `ENTERPRISE_SCHEMA`, `ENTERPRISE_VOLUME` | The same as course 1's `lnl/config.py` |
   | `ENTERPRISE_SERVERLESS`, `ENTERPRISE_CLUSTER_ID` | Serverless jobs, or the all-purpose cluster for the job's notebook task |
   | `RESTRICTED_GROUP`, `ANALYST_GROUP` | The account group allowed to see race and religion, and the one that gets the published view |
   | `ALERT_EMAILS`, `ALERT_DESTINATIONS` | Who gets failure email (empty means you), and the display names of the notification destinations |

3. **Run `00_preflight`.** Fix anything marked ⚠️ that blocks you, then start `02b_incremental`.

## The bundle (`databricks.yml`)

Notebook 04 creates the job with the Databricks SDK, so you can see each setting. `databricks.yml` declares the same job as a **Declarative Automation Bundle**: a file you review in a pull request and deploy. It looks course 1's pipeline up by name instead of defining it; course 1's own bundle declares the pipeline. It's an untested template, and you should use the notebook or the bundle against a schema, not both.

## Monitoring and alerting

The track follows the team's rule that every solution is monitored and alerts somewhere a person will see it:

- **Checks you write:** pipeline expectations (counted in the event log) and `validate_quality` (results in `quality_results`, failure fails the job).
- **Checks the platform runs:** a data profile on silver, and anomaly detection (freshness and completeness) on the whole schema.
- **Alerts:** job failure → email and the PagerDuty destination now; a webhook into your ticketing system (ServiceNow, Jira, ...) once the inbound side exists.
- **Prometheus and Grafana:** 05_monitoring lays out the options. The [Grafana Databricks exporter](https://github.com/grafana/databricks-prometheus-exporter) runs as a container (Kubernetes or Docker) with a service principal and feeds job, pipeline and warehouse metrics from the system tables into the Prometheus you already run. It's young, so test it before relying on it. Grafana's Databricks data source can query `quality_results` directly, but needs Grafana Enterprise or Cloud Pro.

## Cleaning up

The last section of `05_monitoring` deletes everything both courses' tracks created: the job, course 1's pipeline, the profile and your schema (tables, views, the volume and functions). It does nothing until you set `CONFIRM = True`. The profile's dashboard files in `/Workspace/Users/<you>/lnl_quality` stay; delete that folder by hand if you want it gone.

## Before you point this at real tables

The point of the track is to apply it to a few real tables. When you get there:

1. **Get the data owner's written approval** for the tables, the columns and the purpose, before you read anything.
2. **Work in the agency workspace only.** It's approved for criminal justice information. Free Edition, laptops and every other tool aren't.
3. **Use a restricted schema** that only the approved people can read, and put every output there: pipeline tables, quarantine, exception lists and profile metrics. Profile tables don't inherit masks.
4. **Read the source; never write to it.** Your pipeline reads the system of record and writes to your schema.
5. **Masks on before anyone else gets access.** Race, religion and other protected attributes are restricted, and they're never inferred to fill a gap.
6. **Nothing real goes in Git:** no extracts, no samples, no notebook output with real values. Clear outputs before you commit.
7. **AI tools follow agency AI governance.** Don't paste real records into an assistant that isn't approved for them.

## What's been tested

- The delivery handoff runs for real in `lakehouse/tests/test_enterprise_track.py`: course 1 stages the deliveries into a folder standing in for the volume, and course 2 lands them, refusing any that isn't listed or whose fingerprint changed. The same tests check every notebook's helpers and settings exist and that nothing here imports course 1's code.
- Every Databricks SDK call, field and setting was checked against `databricks-sdk` 0.145, (in course 1, before the split), and the bundle's resources against the bundle schema.
- **Nothing in this track has run on a Databricks workspace yet.** Expect a few rough edges the first time through, and run it yourself before you teach it.
