> Snapshot of the live Claude Doc (https://claude.ai/artifact/R1688c4LU7fYfwiQGJQDij), kept for safe keeping. Network addresses are redacted. The Claude Doc is the current copy.

# Course 1 / Course 2 Boundary

Updated Nov 2, 2026 · @wrolfgar

## The decision

Course 1 ends with session 7, "Text II: Meaning Over Words". Everything beyond what those seven sessions need is course 2. wrolfgar decided this on 2026-11-02.

Course 1 teaches cleansing: the seven sessions, plus simple pipelines and the Unity Catalog basics the sessions use. Course 2 teaches the target architecture: deep pipelines, governance, operations, the semantic layer and data products. It starts from course 1's cleansed output.

One rule keeps the two apart: **whoever owns the lesson owns the generator**. Course 1 owns the hero offender generator and its mess. Course 2 owns the expanded world. They connect through a pinned, versioned file, never through shared code or live tables.

## What course 1 owns

Course 1 keeps the seven sessions, the code they run, and the first part of the enterprise track: Unity Catalog and a simple pipeline that runs the same cleansing rules.

| Piece | What it is | Note |
| --- | --- | --- |
| `notebooks/01`–`07` | The seven sessions, Meet the Mess to Meaning Over Words | Unchanged |
| `lnl/` | The cleansing code, in pandas and in Spark (`spark_pipeline.py`) | Same 19 numbers either way |
| `generator/` | The hero offender generator and its mess | Course 1 owns it; course 2 never imports it |
| `enterprise/00_preflight` | Checks what the workspace allows | Keep only the checks for 01 and 02; the job, alert and system-table checks move with 04 and 05 |
| `enterprise/01_unity_catalog` | Catalogs, schemas, volumes, tables, comments, tags, grants | The Unity basics the sessions use |
| `enterprise/02_pipeline`, sections 1–4 | A declarative pipeline, bronze to gold, expectations (warn, drop, fail), the quarantine table | The simple pipeline: course 1's rules, enforced |
| `enterprise/pipeline/hero_offenders.py` | The pipeline code | Goes with 02 |
| `extras/` | The supply-orders type-conversion notebook and its mock data | A bonus exercise after session 4; it needs nothing beyond it |

Course 1 also publishes its cleansed output for course 2 (see The handoff).

## What course 2 owns

Course 2 gets the rest of the enterprise track and the whole lakehouse.

| Piece | What it is |
| --- | --- |
| `enterprise/02_pipeline`, section 5 | Incremental loads (the next delivery), plus schema drift and the event log in depth |
| `enterprise/03_governance` | Column masks, row filters, dynamic views, governed tags, ABAC, lineage |
| `enterprise/04_job_and_alerts` and `tasks/validate_quality` | A scheduled job, task dependencies, alerts, breaking it and fixing it |
| `enterprise/05_monitoring` | Data profiling, anomaly detection, system tables, Prometheus and Grafana |
| `enterprise/databricks.yml` | The bundle that deploys the pipeline and job from a file |
| `lakehouse/` | The home lakehouse: DuckLake, dbt, Dagster, Cube, Superset, OpenMetadata, Fuseki, MCP, monitoring |
| `lakehouse/universe` | The expanded world's generator and its mess (fights, damage, courts, people) |

Sessions 6 and 7's text work stays in course 1. Course 2's free text (`incident_report`) is new, for the world.

## The handoff

Course 2 starts from a frozen, versioned copy of course 1's cleansed output. Course 2 doesn't re-clean the core 100,000 records; that would repeat course 1.

**What it holds.** These tables come from course 1's sessions 2–4 (`lnl.pipeline`), the same tables `lake.py` builds today:

- `silver.hero_offenders`: the cleansed records, keyed by `offender_number`
- `silver.hero_offenders_exceptions`: every value a rule flagged, one row each
- `silver.conduct_notes_answer_key`: the answer key for the text sessions
- the reference data the rules use (crosswalks, null tokens)

**How it travels.**

1. Course 1 builds the output and checks it against the 19 Facilitator Guide numbers. If any number is off, nothing is published.
2. Course 1 publishes it at a tagged version, with a SHA-256 fingerprint for each file.
3. Course 2 lands it like any other upstream delivery, records the version and checks the fingerprints.
4. Course 2's dbt builds its own gold (`dim_person` and the rest), and `universe` builds the world, from that copy, never from live tables.

**The contract** (Priority 3). For each table: its columns, types and keys, what counts as null, and the 19 numbers as acceptance checks. Course 2 says plainly that the core arrives clean from upstream, while the expanded world is cleansed in dbt.

What changes today: course 1's pandas pipeline leaves course 2's daily run. It runs on course 1's side, once per release.

## Today's couplings

Six ties connect course 2 to course 1 today; priorities 2, 3, 4 and 8 remove them. The dependency already runs one way only: course 1 never imports the lakehouse, and its files match `main`.

| Coupling today | Where | Removed by |
| --- | --- | --- |
| The world is built from live course tables (`silver.hero_offenders`, `gold.dim_person`) | `universe/core.py` | Priority 2: build from the pinned copy |
| `universe` imports the course generator for its word lists and fingerprint | `universe/core.py` | Priority 2: course 2 pins its own word lists |
| The course's mess kinds are copied by hand | `universe/mess.py` | Priority 2: becomes course 2's own documented spec |
| The core is cleansed by course 1's pandas pipeline in course 2's daily run | `lake.py` | Priority 3: the handoff contract |
| Course 1's material runs in course 2's platform: Trust Test, the 19-number parity gate, `notebook_smoke` | Dagster, Cube, Superset | Priority 4: an optional add-on |
| Course 2 lives on a branch of the course repo (`duckdb-lakehouse`) | the repo | Priority 8: its own repo (wrolfgar's call) |

## Course 2 topics noted

**Automatic governance tags at ingestion.** When a data source is ingested, course 2 should show how to attach governance tags automatically (CJIS, PII and so on). It should also add other metadata tags that make data easier for end users to search, parse and organize. wrolfgar raised this on 2026-11-02.

Today it's all manual. Each sensitive column is marked by hand in dbt (`meta.sensitivity`: restricted or personal). `om_sync.py` pushes those marks to OpenMetadata as tags, and the tags decide which Cube columns are masked. The controls downstream are automatic; the tagging at the start is not.

Ways to teach it:

- default tags set once for a source and inherited by every column (a source registered as CJIS, for example)
- PII found automatically from patterns and profiling (OpenMetadata's auto-classification)
- tags that follow lineage from bronze to silver to gold
- tag families that help people find data: source system, domain, retention, refresh

It continues where `enterprise/03_governance` section 6 (governed tags and ABAC) leaves off.

## Answers to the open questions

wrolfgar asked Claude to decide these on 2026-11-02; any of them can be reversed.

- [x] **`02_pipeline`: split at section 5.** Sections 1–4 stay in course 1; incremental loads and schema drift go to course 2. A pipeline that enforces course 1's own rules is the "simple pipeline"; handling the next delivery is operations.
- [x] **`00_preflight`: trim it** to the checks 01 and 02 need. The job, alert and system-table checks move with 04 and 05.
- [x] **`extras/`: course 1, as a bonus exercise.** It practises session 4's type conversion on a new file and needs no architecture. This reverses the first call (course 2); say so if you want it back.
- [x] **Move the course 2 notebooks later**, with Priority 8 (course 2's own repo). Nothing on `main` changes until then: course 1's files stay as they are, and this document is the record.
- [x] **Automatic tagging goes right before `incident_report`**, as Priority 4b. Free text is where automatic PII detection matters most, and tags set at ingestion should exist before that text arrives.
