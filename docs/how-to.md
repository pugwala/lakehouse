> Snapshot of the live Claude Doc (https://claude.ai/artifact/TzBHFecVGL9oyzYKAZP9Ar), kept for safe keeping. Network addresses are redacted. The Claude Doc is the current copy.

# How to Use the Home Lakehouse

Updated Nov 4, 2026 · @wrolfgar

## Start here

The home lakehouse is one Debian VM: about 16.7 million rows of mock data in DuckLake, governed and served by eleven sites on one Tailscale name. Course 1 hands over its cleansed records; course 2, this lakehouse, lands them, builds the expanded world around them, and serves both through Cube. The architecture drawing (v3.3) is in the [Plan](https://claude.ai/artifact/Js8ovfd7HE7BJ5Sj6TS3Sj).

**Reaching it.** Every site is at `<tailnet-host>`, from any device on the tailnet, with a real certificate. Nothing is open to the internet.

| Site | Path | Login | What it's for |
| --- | --- | --- | --- |
| Jupyter | `/jupyter/` | token `JUPYTER_TOKEN` | Notebooks, `%sql`, the world sessions |
| Dagster | `/dagster/` | basic auth `DAGSTER_UI_USER` (set by `scripts/set-dagster-ui-password.sh`) | Jobs, schedules, runs, asset lineage |
| Superset | `/superset/` | `admin` / `SUPERSET_ADMIN_PASSWORD` | Dashboards and SQL Lab over Cube |
| OpenMetadata | `/openmetadata/` | `admin@open-metadata.org` / `OM_ADMIN_PASSWORD` | Glossary, tags, lineage, products, contracts |
| Fuseki | `/fuseki/` | reads open; writes as `writer` / `FUSEKI_WRITER_PASSWORD` | SPARQL over the glossary, rulebook and catalog |
| MCP server | `/mcp` | bearer `MCP_TOKEN` | Twelve read-only tools for an AI agent |
| Grafana | `/grafana/` | `admin` / `GRAFANA_ADMIN_PASSWORD` | The Home Lakehouse dashboard |
| Prometheus, Alertmanager | `/prometheus/`, `/alertmanager/` | the Dagster basic-auth login | Metrics, alerts, silences |
| ntfy | port `8443` | `<owner-user>` / `NTFY_IAN_PASSWORD` | Alerts on your phone (topic `lakehouse-alerts`) |

**Where the secrets live.** Every password is in `~/lakehouse/lakehouse/.env` on the VM, never in the repo. Read one in your own SSH session, so it never lands on a shared screen:

```bash
grep '^JUPYTER_TOKEN=' ~/lakehouse/lakehouse/.env | cut -d= -f2-
```

Never print the whole file, `printenv` in a container, or `docker compose config`: all three show every secret.

**Where things are.**

| Thing | Where |
| --- | --- |
| Course 2's repo (the live stack runs from it) | `~/lakehouse` on the VM; [pugwala/lakehouse](https://github.com/pugwala/lakehouse) |
| Course 1, pinned | the submodule `~/lakehouse/course1` at tag `course1-v1.3` ([pugwala/homelake](https://github.com/pugwala/homelake)) |
| The lake's files | `/lake/data` (Parquet), its catalog in Postgres (`catalog-pg`) |
| The expanded world's build | `/lake/landing/universe/M`: clean Parquet, messy CSVs, answer keys, the mention key |
| Course 1's handoff | `/lake/landing/handoff/course1/v1` |
| Backups | `/lake/catalog-backups` (nightly dumps), the restic repository (local for now) |
| Running anything by hand | `cd ~/lakehouse/lakehouse && docker compose --profile core exec -T jupyter <command>` |

**Mock data only.** Every person, place and record is invented. DuckDB has no grants or masks of its own, so Cube is the only governed path; only engineering attaches to the lake directly, read-only.

## Querying the data

There are three ways in, and they differ in what they let you see. Engineering reads the lake directly, read-only. Everyone else goes through Cube, which masks the restricted columns. Superset and the MCP agent only ever see Cube.

| Path | Who | Sees | Masks |
| --- | --- | --- | --- |
| Jupyter, `%sql` or `lake.lake_ro_connect()` | Engineering | Every schema, bronze to gold, plus time travel | None: `lake_ro` reads everything |
| Cube SQL (`cube:15432`) or REST | Analysts, notebooks | Gold and the products' views | Race, religion and STG show `***` unless the token's groups include `restricted_reader` |
| Superset | Dashboards, SQL Lab | Cube only (its only database) | As Cube |
| MCP agent | AI agents | Cube, plus read-only metadata | As Cube |

**In a notebook, SQL on the lake.** One line connects, read-only:

```sql
%load_ext lakehouse.sql_magic
%%sql
SELECT question_id, as_loaded, cleansed FROM gold.trust_test ORDER BY question_id
```

The same in Python, as a DuckDB connection:

```python
from lakehouse import lake
con = lake.lake_ro_connect()
con.sql("SELECT count(*) FROM lake.world_gold.fct_incident").fetchone()
```

Name tables by schema: `ref`, `bronze`, `silver`, `gold`, `ops`, `mart_custody`, `mart_readiness`, and the world's `world_bronze`, `world_silver`, `world_gold`. Nothing can be written. `08_from_lake.ipynb` is a worked example: the Trust Test's eight questions in SQL over silver.

**Through Cube.** Cube's SQL API speaks the Postgres protocol on the Compose network:

```python
import os, psycopg2
cube = psycopg2.connect(host="cube", port=15432, dbname="cube", user="lake", password=os.environ["CUBE_SQL_PASSWORD"])
cur = cube.cursor()
cur.execute("SELECT custody_level, MEASURE(people_in_custody) FROM custody_population WHERE is_latest_month_end = true GROUP BY 1")
cur.fetchall()
```

The views to query are the data products' (`custody_population`, `custody_offenses`, `custody_admissions`, `field_incidents`, `fight_participants`, `incident_damage`, `court_outcomes`), plus `period_readiness`, `offender_records`, `dq_scorecard`, `world_exceptions` and `incident_reports`. Each view's `meta.reads` says which lake tables it reads. After editing a model file, restart Cube: `docker compose --profile core restart cube`.

**Superset.** Three dashboards, each built and checked by `superset/dashboards.py`:

- **Trust Test** (`/superset/dashboard/trust-test/`): course 1's eight questions, before and after cleansing.
- **Custody** (`/superset/dashboard/custody/`): people in custody each month-end, by level and offense category.
- **Fights, Damage and Courts** (`/superset/dashboard/world/`): the expanded world's three products.

In SQL Lab, use Cube's SQL: `SELECT MEASURE(record_count) FROM offender_records`.

## The MCP agent

An AI agent asks the lakehouse questions through twelve read-only tools instead of writing SQL. It sees Cube's governed model and the catalog's metadata, never a raw row. Restricted columns stay masked, and no raw incident-report text reaches it.

**Connecting Claude Code.** On a machine on the tailnet, add the server without the token ever showing on screen:

```bash
claude mcp add --transport http --scope user lakehouse <tailnet-host> \
  --header "Authorization: Bearer $(ssh lakehouse 'grep ^MCP_TOKEN= ~/lakehouse/lakehouse/.env | cut -d= -f2-')"
```

Then ask in plain words: "how many people are in custody by custody level, and is October final?" The agent picks the tools.

**The twelve tools, each with a real answer from November 4, 2026:**

| Tool | Ask it | It answered |
| --- | --- | --- |
| `list_metrics` | What can I measure? | 36 metrics across 13 views; `countDistinct` marks a count of people, never to be added across groups |
| `query_metric` | `people_in_custody` by `custody_level` | G2 29,006 · G3 26,037 · G1 13,871 · G4 11,557 · ...; October 31 is provisional, waiting on Classification |
| `define_term` | `SID` | SID Number: "one SID for life, the same on every record that person has"; synonyms SID, person ID; identifies Person |
| `business_rules` | about `fight` | "A charge follows its fight, and its outcome follows the charge", enforced by a dbt test |
| `data_product_info` | `court outcomes` | Its question, tables, views and contract; October provisional, waiting on the Courts liaison; fresh, 39 hours old |
| `data_quality` | area `world` | 1,167,509 values flagged in world silver, most in `damage` (422,501); no quality alert firing |
| `find_by_tags` | `Governance.CJIS` and `PIIType.FreeText`, match all | 5 tables: the course's raw and cleansed records, and the incident reports in bronze, silver and redacted gold |
| `describe_table` | `fct_charge` | `world_gold.fct_charge`, Gold, 12 columns, `person_key` and `offender_number` personal; delivered by court-outcomes, read by the `court_outcomes` view; monthly contract |
| `lineage` | `people_in_custody` | Offered by 2 views reading 4 tables, 12 tables upstream (`gold.fct_offender_record`, the readiness inputs, the reference crosswalks); source: course 1's cleansing |
| `lineage` | `world_silver.charge` | 3 tables downstream; a change reaches the `court_outcomes` view and the court-outcomes product |
| `pipeline_status` | job `daily_lake` | Runs at 05:00 Central; last success 17:10 CST; the 16:58 run failed (a test guard, fixed) |
| `platform_health` | (no arguments) | healthy: 10 sites and 7 targets up, no alerts, Watchdog beating; `/lake` 4.8% used, memory 71% free, certificate 80 days, backups 17 hours old |
| `search_incident_reports` | `bridge`, witness statements | 2,017 reports; the newest: "I saw the whole street fight at National City Bridge 6987. There was this villain, \[ALIAS\]..." |

**Good questions to try.**

- "Which tables hold birth dates, and which data products use them?" (`find_by_tags`, then `describe_table`)
- "If world\_silver.incident changed, what would break?" (`lineage`)
- "Did last night's load work, and is anything alerting?" (`pipeline_status`, `platform_health`)
- "How many fights in Gotham City this year, and are those numbers final?" (`query_metric` on `field_incidents`, which returns its readiness)

**What it can't do.** It can't run SQL, write anything, see a raw name or reach a restricted value. It also can't start or stop a job. Every tool reads; the server holds no lake credentials and no admin login. The tool descriptions are in `lakehouse/mcp/server.py`, and the full reference is `lakehouse/README.md`, under "MCP".

## What the data means

Meaning lives in two places that agree: OpenMetadata for people, and Fuseki for queries. `om_sync.py` and `om_to_rdf` keep them in step every morning. Nothing in either is typed by hand except a steward's own additions, which are kept.

**OpenMetadata** (`/openmetadata/`) holds the catalog:

| What | How much | Comes from |
| --- | --- | --- |
| Lake tables, with columns, types and descriptions | 76 | The lake itself, plus dbt's descriptions |
| Glossary terms, with synonyms, typed relations and the columns and metrics each maps to | 28 | `glossary/glossary.yml` |
| Tag families: Governance, PIIType, Source, Layer, Refresh, Sensitivity, PII, Lakehouse | 8 | The tagger (`tagging/`), dbt's `meta.sensitivity`, the glossary |
| Lineage edges, table to table | 120 | dbt's manifest, marked `DbtLineage` |
| Domains, data products and data contracts | 3 domains, 5 products, 7 contracts | `products/*.yml` and dbt's enforced contracts |

**Lineage.** Open a table and choose the Lineage tab to see what it's built from and what's built from it. Every edge marked `DbtLineage` comes from dbt and is rebuilt each run. An edge you draw by hand is marked `Manual` and is never touched.

**The tags-to-masks loop.** Which columns Cube masks is decided here:

1. Tag a column `Sensitivity.Restricted` in OpenMetadata.
2. Run `scripts/bootstrap.sh`, or `cube/sync_masks.py` and then restart Cube.
3. Review `git diff lakehouse/cube/model/` and commit it. `bootstrap.sh --check` fails until the model matches.

**Tags arrive on their own.** As data lands, the tagger tags every table and column:

- **Governance:** CJIS, and PII when a column holds personal data.
- **The kind of personal data:** `PIIType.BirthDate`, `PIIType.FreeText`, ...
- **Where a table came from:** `Source.*`, followed through lineage into gold.
- **Its layer and refresh:** `Layer.*`, `Refresh.*`.

The tagger's record is in `ops.table_tags` and `ops.column_tags`; the rules are in `tagging/rules.yml`.

**Fuseki** (`/fuseki/`) serves the same meaning as RDF, at `<tailnet-host>`. Reads need no login. It holds four graphs:

- **openmetadata** (2,384 triples): the glossary as SKOS, the tables and the tags.
- **rulebook** (77 triples): the 12 business rules, each with its terms and what enforces it.
- **readiness** (38 triples): the data products as DCAT, and the business inputs each waits on.
- **The deductions' results:** for example, which identifiers are pseudonymous.

```sparql
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
SELECT ?term ?synonym WHERE { ?t skos:prefLabel ?term . OPTIONAL { ?t skos:altLabel ?synonym } } ORDER BY ?term
```

The [ontology guide](https://claude.ai/artifact/QZzDB9Lp8k94cXoU7smD7S) has the worked recipes: terms, relations, the rulebook, which rules hold today, and the SHACL shapes the daily run checks.

## Data products and readiness

A month's number is **final** only once every business unit it depends on has closed that month. Until then it's **provisional**, and every view, dashboard and agent answer says so. Five data products, in three domains, each declared in one file in `lakehouse/products/`:

| Product | Domain | Cube views | Waits on | Refreshed |
| --- | --- | --- | --- | --- |
| custody-population | Custody Operations | `custody_population` | Records, Classification | daily 05:00 |
| custody-offenses | Custody Operations | `custody_offenses`, `custody_admissions` | Records, Courts liaison | daily 05:00 |
| field-incidents | Field Operations | `field_incidents`, `fight_participants` | Field Operations | monthly 05:30 |
| incident-damage | Field Operations | `incident_damage` | Field Operations, Insurance | monthly 05:30 |
| court-outcomes | Justice | `court_outcomes` | Courts liaison | monthly 05:30 |

Each descriptor drives everything else: OpenMetadata's domain, product and contract, the DCAT entry in Fuseki, its Cube views, its freshness alert and its Superset status table. `data_product_info` (MCP) answers "what is this, and can I trust this month?" in one call.

**The business inputs** each say who closes a month, in which system and within how many days:

| Input | Unit | System | Closes within |
| --- | --- | --- | --- |
| records | Records | Offender management | 5 days |
| classification | Classification | Case management | 10 days |
| courts | Courts liaison | Court case feed | 7 days |
| field-reports | Field Operations | Incident reporting | 3 days |
| insurance-claims | Insurance | Claims system | 20 days |

**Seeing it.** `period_readiness` (a Cube view, and `mart_readiness.period_readiness` in the lake) lists every product and month-end, final or provisional, with who it still waits on. From the VM:

```bash
cd ~/lakehouse/lakehouse
docker compose --profile core exec -T jupyter python lakehouse/readiness/closes.py status
```

**Recording a close.** The units are fictional, so the daily run plays them (`closes.py simulate`). To report one by hand:

```bash
docker compose --profile core exec -T jupyter python lakehouse/readiness/closes.py report classification 2026-10-31 --by "Classification"
```

Closes are append-only and the latest counts, so reporting an earlier month-end reopens a month, and the history stays. A unit later than its promise raises the `BusinessInputLate` alert.

**Adding a product or an input** is a file, not code. Write `products/inputs/<name>.yml` or `products/<name>.yml` (copy a neighbour), list its `depends_on`, then run `scripts/bootstrap.sh`. `lakehouse/README.md`, under "Data products", walks through it.

## The expanded world

Course 1's 100,000 records are one flat list. The expanded world builds everything around them: 16,734,616 rows in 16 tables at scale M, from 1996 to today. Today's 86,879 villains are in it, unchanged, and every conviction links back to their offender record.

| Area | Tables (rows at M) |
| --- | --- |
| People and what they can do | person 440,000 · power 400 · person\_power 263,916 · team 300 · team\_member 60,000 |
| Places | location 20,000 (cities, districts, custody units) |
| Fights | incident 1,200,000 · participant 6,000,000 · power\_use 4,000,000 · damage 1,800,000 |
| Courts | charge 900,000 · disposition 900,000 |
| Missions | mission 150,000 · mission\_member 600,000 · mission\_incident 200,000 |
| What people wrote | incident\_report 200,000 |

**Three versions of every table.** The generator writes the clean truth as Parquet. It also writes a messy CSV copy, the way a source system would hand it over, with 8,434,937 deliberate defects. The **answer key** records every defect exactly. All three are in `/lake/landing/universe/M/`. The lake loads only the messy copy:

- `world_bronze` holds it as written;
- `world_silver` types and checks it, flagging every problem and never dropping a row;
- `world_gold` builds the dimensions and facts, with enforced contracts.

**Built by Dagster.** `world_refresh` rebuilds the world and its dimensions on the 1st at 04:30. `world_monthly_job` builds the big facts one month at a time, the next hour. A full backfill of all 370 months takes about 2 minutes. At scale L (65.6M rows) it was benchmarked in a scratch lake and fits the VM; the build's memory is the limit, not the lake.

**The world sessions.** Four course 2 notebooks in `lakehouse/sessions/` teach the cleaning skills a flat table can't. Open them in Jupyter:

| Session | Skill | With the answers |
| --- | --- | --- |
| 1 Who is who | Find the people entered twice | 95.2% found at 99.3% precision |
| 2 Dates that lie | Read every date format, then catch charges filed before their fight | Every readable date read right; 99.0% of the false ones found |
| 3 Links that break | Orphan links, and links to duplicates | All 23,852 orphans counted; 95.5% of the duplicate links re-pointed |
| 4 Finding the names | SIDs, phones, birth dates and names in 200,000 reports | SIDs and phones 100%; names 91.1% at 96.9% precision |

Each exercise is checked against the answer keys, never against a stored solution. `lakehouse/sessions/README.md` has the facilitator's numbers.

**The incident reports.** They name people on purpose: names, aliases, SIDs, birth dates and witnesses' phone numbers. A **mention key** says where each of the 1,893,406 details sits.

- The raw text stays in bronze and silver, for engineering only.
- `world_gold.incident_report_redacted` replaces every marked detail with `[PERSON NAME]`, `[ALIAS]`, `[SID]`, `[BIRTH DATE]` or `[PHONE]`.
- Cube's `incident_reports` view, and the MCP server's `search_incident_reports`, read only that redacted copy.
- It keeps its personal-data tag: redaction by a finder always misses something.

## Running and watching it

It runs itself. Dagster runs the jobs on schedule, Prometheus watches everything, and only something that needs you reaches your phone. A healthy lakehouse fires one alert, Watchdog, on purpose: if its heartbeat (repeated every four hours, to a quiet topic) stops arriving, alerting itself is down.

**The jobs** (Dagster, `/dagster/`; or ask the MCP agent's `pipeline_status`):

| Job | When (Central) | What it does |
| --- | --- | --- |
| `daily_lake` | Every day 05:00 | Load, parity check, dbt, tags, OpenMetadata, Fuseki, health |
| `world_refresh` | 1st of the month 04:30 | Rebuild the expanded world, its bronze and its dimensions |
| `world_monthly_job` | 1st of the month 05:30 | The world's big facts for the month just closed, with the answer-key tests |
| `lake_housekeeping` | Sundays 03:30 | Keep 30 days of DuckLake history; merge small files |
| `notebook_smoke` | Sundays 06:00 | Run course 1's seven notebooks and the bridge notebook |
| `monitoring_selftest` | By hand | Fails on request, to test that alerts arrive |

**`daily_lake`, in order:**

1. Land course 1's pinned handoff as `ref`, `bronze` and `silver`.
2. Check the 19 Facilitator Guide numbers. This blocking step also runs every offline test, and stops gold if one fails.
3. Build gold and the marts with dbt, every test included.
4. Tag every table and column.
5. Sync OpenMetadata (tables, tags, lineage, products), then Fuseki.
6. Check the business rules, push the quality numbers, refresh readiness.

**Watching.** Grafana's Home Lakehouse dashboard shows the platform, the pipeline and the data. Prometheus holds 27 alert rules. Each alert has a runbook in `lakehouse/runbooks/` (`<AlertName>.md`), linked from the alert itself. Critical means act now; warning means look today.

**Alerts on your phone.** Alertmanager sends to ntfy on the tailnet. Topic `lakehouse-alerts` is the phone; the heartbeat and the self-test go to quiet topics of their own. Each notice says what fired, why, and links its runbook. A "Resolved" notice follows when it clears.

**Backups.**

| What | When | Where |
| --- | --- | --- |
| Catalog dump (`catalog-backup`) | Nightly 02:00, 14 days kept | `/lake/catalog-backups` |
| Off-machine backup (`offsite-backup`, restic) | Nightly 02:30, with a restore drill monthly | A local folder for now; TrueNAS when you raise it |
| Full restore drill | By hand: `bash lakehouse/backup/restore_drill.sh` | Restores the latest snapshot and its catalog dump into a scratch database, runs the 19 parity checks on the restored lake, and cleans up |

All of it is checked by alerts: a stale or failed backup, or a drill older than 35 days, pages you.

## Changing it safely

Every change goes through the same three gates: the setup script, the tests, and CI on GitHub. Nothing reaches the public repo without a scrub.

**Setup and upgrades: `scripts/bootstrap.sh`.** It builds the images, starts the services and syncs OpenMetadata, Fuseki, Cube's masks and Superset. It also stages the notebooks' model. Run it after a pull; `--check` changes nothing and fails if anything has drifted.

```bash
bash ~/lakehouse/lakehouse/scripts/bootstrap.sh          # set up or upgrade
bash ~/lakehouse/lakehouse/scripts/bootstrap.sh --check  # is everything in step?
```

**The tests, as of November 4, 2026:**

| Suite | How many | Needs the stack | Run it |
| --- | --- | --- | --- |
| `ci/checks.sh` | 17 checks | No | `bash lakehouse/ci/checks.sh`; GitHub runs it on every push |
| Offline tests (`lakehouse/tests`) | 235 | No | `pytest lakehouse/tests` in the Jupyter container |
| Acceptance (`lakehouse/acceptance`) | 431 | Yes | `pytest lakehouse/acceptance` in the Jupyter container, about 7 minutes |
| Bootstrap (`bats`) | 71 | No | `bats lakehouse/tests/bootstrap.bats` |

`daily_lake`'s parity step runs every offline test before it builds gold, so a failing test stops the load. Run all of `lakehouse/tests` before launching `daily_lake` by hand.

**How changes are made.**

1. **Test first.** Write the failing test, see it fail, then write the code.
2. **Prove the test.** Break the code on purpose, one mutation at a time, and check a test catches each one.
3. **Docstrings.** Every function gets one.
4. **Commit.** Commits are made as `pugwala` with GitHub's no-reply email. `tools/tieback_check.sh` keeps any real organization out (turn on its hook with `git config core.hooksPath .githooks`). No Tailscale names, addresses or secrets ever go into the repo.

**Docs in the repo.** The Claude Docs (this one, the Plan, the Handoff, the Work Log, the ontology guide and the course boundary) are the live copies. Scrubbed Markdown snapshots of them sit in `pugwala/lakehouse`'s `docs/`, refreshed whenever the docs change, with names and network addresses replaced.

**Architecture versions.** The architecture is versioned major.minor and dated: **v3.3, as of November 4, 2026**. The version is in the drawing's corner, `docs/architecture.png` and git tag `arch-v3.3`.

- **A new component, layer or path** makes v3.4.
- **A change in what the lakehouse is** makes v4.0.
- **Fixes, tests and documents** don't change it.
