# Home Lakehouse: course 2

A complete data platform on one home-lab VM, built around fictional superhero records: a DuckDB lakehouse
(DuckLake on Postgres, Parquet on disk), dbt, Dagster, Cube, Superset, OpenMetadata, an ontology in Apache Jena
Fuseki, an MCP server for AI agents, monitoring and alerting, data products with readiness, automatic governance
tags, and an expanded world of about 16.7 million rows (65.6 million at scale L).

> ⚠️ **Mock data only.** Every person, place and record here is invented.

## Two courses, two repos

| Course | What it teaches | Repo |
| --- | --- | --- |
| Course 1 | Data cleansing: sessions 1 to 7, pandas and PySpark, ending with "Meaning Over Words" | [pugwala/homelake](https://github.com/pugwala/homelake) |
| Course 2 | The functional architecture around clean data: this repo | pugwala/lakehouse |

Course 2 starts where course 1 ends. Course 1 is the git submodule `course1/`, pinned at the tag `course1-v1.4`.
Course 1 publishes its cleansed output once, checked against its 19 Facilitator Guide numbers, and course 2 lands
that pinned, fingerprinted handoff (`lakehouse/handoff/`). Course 2's own code never imports course 1's.

```bash
git clone --recurse-submodules https://github.com/pugwala/lakehouse.git ~/lakehouse
bash ~/lakehouse/lakehouse/scripts/bootstrap.sh
```

**Architecture v3.3, as of 2026-11-04** ([the drawing](docs/architecture.png), git tag `arch-v3.3`), versioned major.minor
like course 1's tags; [the Plan](docs/lakehouse-plan.md#architecture-versions) lists every version.

## Where to start

- [`lakehouse/README.md`](lakehouse/README.md): what's here, setup, the daily run, every tool, and the test status.
- [`lakehouse/sessions/`](lakehouse/sessions/README.md): course 2's four world sessions, cleaning skills on the
  expanded world's messy files (duplicate people, dates, broken links, names in free text), checked against its
  answer keys.
- [`enterprise/`](enterprise/README.md): the same ideas on an enterprise Databricks workspace. Course 1's track ends with a pipeline and two handed-over deliveries; this one takes it on: the next delivery, governance, a scheduled job that alerts, and monitoring, with its own helpers.
- [`docs/how-to.md`](docs/how-to.md): how to use the whole lakehouse, start here.
- [`docs/`](docs/README.md): snapshots of the lab's working documents (the how-to, the plan, the handoff, the work log,
  the ontology guide and the course boundary).
- `lakehouse/ci/checks.sh`: every check that needs no secrets and no running stack; GitHub runs it on every push.

## Rules this repo keeps

- Commits are made as `pugwala`, with the GitHub no-reply email.
- `tools/tieback_check.sh` keeps any real organization out of the repo. Turn its hook on once per clone:
  `git config core.hooksPath .githooks`.
- No network addresses, host names or secrets: `.env` is never committed, and the docs are scrubbed before they're
  added.
