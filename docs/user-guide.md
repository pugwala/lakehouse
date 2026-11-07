> Snapshot of the live Claude Doc (https://claude.ai/artifact/WomucUhsPgex2v7dzjJo6h), kept for safe keeping. Network addresses are redacted. The Claude Doc is the current copy.

# Home Lakehouse User Guide

Updated Nov 7, 2026 · @wrolfgar

## Who this is for and how to get in

This guide teaches you to use the whole home lakehouse: find and query its data, ask its AI agent, build data products and models, check that processing and quality gates passed, and add rules, sources, pipelines and dashboards. Everything is mock data: every person, place and record is invented.

Some of it you do in a web page. The rest you do by **writing a small file** in the repo and running one command; the lakehouse builds everything else from that file. The table says which is which.

| You want to | Where | How |
| --- | --- | --- |
| Query data | Jupyter, Superset SQL Lab, Cube | In the browser |
| Ask questions in plain words | The AI agent (MCP) | In Claude Code |
| Find and understand data | OpenMetadata, Fuseki | In the browser |
| Check processing and quality | Dagster, Grafana, the agent | In the browser |
| Build a dashboard | Superset | In the browser, or a file to keep it |
| Build a gold table or data model | dbt and Cube files | A file, then a command |
| Create a data product | `products/` | A file, then a command |
| Enter a business or processing rule | `glossary/`, `ontology/`, dbt | A file, then a command |
| Add a data source or pipeline | `tagging/`, dbt, Dagster | Files, then a command |

**Getting in.** Every site is at `<tailnet-host>`, from any device on the tailnet, with a real certificate. Nothing is open to the internet.

| Site | Path | Log in with |
| --- | --- | --- |
| Jupyter | `/jupyter/` | the token `JUPYTER_TOKEN` |
| Dagster | `/dagster/` | `DAGSTER_UI_USER` and its password |
| Superset | `/superset/` | `admin` / `SUPERSET_ADMIN_PASSWORD` |
| OpenMetadata | `/openmetadata/` | `admin@open-metadata.org` / `OM_ADMIN_PASSWORD` |
| Fuseki | `/fuseki/` | reading is open; writing is `writer` / `FUSEKI_WRITER_PASSWORD` |
| MCP agent | `/mcp` | not a browser page: Claude Code connects with the bearer token `MCP_TOKEN` (see Ask the AI agent below) |
| Grafana | `/grafana/` | `admin` / `GRAFANA_ADMIN_PASSWORD` |
| Prometheus, Alertmanager | `/prometheus/`, `/alertmanager/` | the Dagster login |

Every password is in `~/lakehouse/lakehouse/.env` on the VM, never in the repo. Read one in your own SSH session so it never lands on a shared screen: `grep '^JUPYTER_TOKEN=' ~/lakehouse/lakehouse/.env | cut -d= -f2-`.

**Three ways to the data, and what each one hides.** The lake itself (DuckDB on DuckLake) has no permissions of its own, so the governed path is Cube.

| Path | For | Sees | Restricted columns (race, religion, gang affiliation) |
| --- | --- | --- | --- |
| Jupyter, straight to the lake, read-only | Engineering | Every schema, bronze to gold, plus time travel | Shown |
| Cube (SQL or REST) | Analysts, notebooks, BI tools | Gold and the data products' views | `***` unless your token's groups include `restricted_reader` |
| Superset and the AI agent | Everyone else | Cube only | As Cube |

## Query the complete lakehouse

You can query every table in the lake from a Jupyter notebook in one line, read-only. Query the governed views through Cube's SQL, from a notebook or Superset's SQL Lab.

**What's in the lake.** Name every table by its schema.

| Schema | Holds |
| --- | --- |
| `ref` | The crosswalks (units, race, religion, gang groups, offenses, violence codes) and the documented "unknown" codes |
| `bronze` | Course 1's records as delivered, every column as text |
| `silver` | Course 1's records cleansed and typed, plus `hero_offenders_exceptions` (one row per flagged value) |
| `gold` | `fct_offender_record`, `dim_person`, `dim_unit`, `dim_offense`, `dim_stg_group`, `dq_scorecard`, `trust_test` |
| `mart_custody`, `mart_readiness` | The custody marts and `period_readiness` |
| `world_bronze`, `world_silver` | The expanded world as delivered, then typed and checked with every problem flagged |
| `world_gold` | `fct_incident`, `fct_participation`, `fct_power_use`, `fct_damage`, `fct_charge`, `fct_mission`, `dim_person`, `dim_location`, `dim_power`, `dim_team`, `incident_report_redacted` |
| `ops` | Run records (`load_runs`) and the tagger's `table_tags` and `column_tags` |

### In a notebook, straight to the lake

Open Jupyter, start a notebook, and load the SQL magic once. Then any cell that starts with `%%sql` runs against the lake:

```sql
%load_ext lakehouse.sql_magic
```

```sql
%%sql
SELECT incident_type, count(*) AS fights
FROM world_gold.fct_incident
GROUP BY 1
ORDER BY 2 DESC
```

The same connection in Python, when you want the result as a pandas table:

```python
from lakehouse import lake
con = lake.lake_ro_connect()
con.sql("SELECT dimension, round(100 * sum(passed) / sum(checked), 2) AS pct FROM gold.dq_scorecard GROUP BY 1").df()
```

Nothing can be written: the lake is attached read-only, as `lake_ro`. A query that fails doesn't break the next one. Every load is a DuckLake snapshot, so you can read a table as it was: add `AT (VERSION => n)` after its name, with a snapshot id from `SELECT snapshot_id, snapshot_time FROM lake.snapshots()`. The worked example is `08_from_lake.ipynb`, the Trust Test's eight questions in SQL.

### Through Cube, the governed path

Cube serves gold and the data products' views, with the restricted columns masked. It speaks the Postgres protocol at `cube:15432`, so a notebook connects like this:

```python
import os, psycopg2
cube = psycopg2.connect(host="cube", port=15432, dbname="cube", user="lake", password=os.environ["CUBE_SQL_PASSWORD"])
cur = cube.cursor()
cur.execute("SELECT incident_month, period_status, MEASURE(fights) FROM field_incidents GROUP BY 1, 2 ORDER BY 1 DESC")
cur.fetchall()
```

Cube's SQL has one rule: a measure is written `MEASURE(name)`, and Cube does the counting. That matters for people, who are counted as distinct SIDs: never add up a people count across groups yourself.

The views to query: `custody_population`, `custody_offenses`, `custody_admissions`, `field_incidents`, `fight_participants`, `incident_damage`, `court_outcomes`, `period_readiness`, `offender_records`, `dq_scorecard`, `world_exceptions` and `incident_reports`. A data product's view carries `period_status` (final or provisional) for each month, so group by the month to see it. Each view's `meta.reads` names the lake tables it reads.

### In Superset's SQL Lab

Open `/superset/`, choose **SQL → SQL Lab**, and pick the Cube database (it's the only one). Write the same Cube SQL: `SELECT MEASURE(record_count) FROM offender_records`. Any result can become a chart with **Create chart**.

## Ask the AI agent: the twelve MCP tools

The AI agent answers questions about the lakehouse in plain words, through twelve read-only tools. It sees Cube's governed model and the catalog's metadata, never a raw row: restricted columns stay masked, and no unredacted incident-report text reaches it.

**Connect it.** On a machine on the tailnet, add the server to Claude Code. The token is read over SSH, so it never shows on screen:

```bash
claude mcp add --transport http --scope user lakehouse <tailnet-host> \
  --header "Authorization: Bearer $(ssh lakehouse 'grep ^MCP_TOKEN= ~/lakehouse/lakehouse/.env | cut -d= -f2-')"
```

Opening `/mcp` in a browser shows a page that says *The lakehouse AI agent is running*. That's expected: a browser can't send the token, so the agent refuses it and shows this connect command instead.

Then just ask, for example: *"How many people are in custody by custody level, and is October final?"* The agent picks the tools.

**Heroes and villains by name.** A hero's or villain's alias is their *common name* (SUPERMAN, WOLVERINE). It is public, like a stage name, so answers use it instead of a SID. Their real name, birth date and SID stay restricted. Ask *"Which villains were in the most fights?"* or *"How many charges did WOLVERINE face?"*. In SQL, `fight_participants` and `court_outcomes` have `common_name` and `person_role`:

```sql
SELECT common_name, MEASURE(participations), MEASURE(people_involved)
FROM fight_participants
WHERE person_role = 'villain' AND common_name IS NOT NULL
GROUP BY 1 ORDER BY 2 DESC LIMIT 5
```

Several people can share one common name: copycats, or five Green Lanterns. So count people with `people_involved` or `people_charged`, never by name. Incident reports keep common names as written, so `search_incident_reports` finds a hero by name, while real names still read [PERSON NAME].

**The tools, each with a real answer from November 4, 2026:**

| Tool | What it's for | Ask it | It answered |
| --- | --- | --- | --- |
| `list_metrics` | Everything you can measure | What can I measure? | 36 metrics across 13 views; people counts are distinct, never added across groups |
| `query_metric` | A governed number, with filters and dates | `people_in_custody` by `custody_level` | G2 29,006 · G3 26,037 · G1 13,871 · ...; October 31 is provisional, waiting on Classification |
| `define_term` | A business definition | `SID` | "One SID for life, the same on every record that person has"; synonyms SID, person ID |
| `business_rules` | The rules about a term | about `fight` | "A charge follows its fight, and its outcome follows the charge", enforced by a dbt test |
| `data_product_info` | A product's promise and whether to trust this month | `court outcomes` | Its question, tables, views and contract; October provisional, waiting on the Courts liaison; fresh |
| `data_quality` | Quality counts by area | area `world` | 1,167,509 values flagged in world silver, most in `damage`; no quality alert firing |
| `find_by_tags` | Tables and columns by their tags | `Governance.CJIS` and `PIIType.FreeText` | 5 tables, including the incident reports in bronze, silver and redacted gold |
| `describe_table` | One table: columns, tags, products, contract | `fct_charge` | 12 columns, two personal; delivered by court-outcomes; monthly contract |
| `lineage` | What a table or metric is built from, and what a change would reach | `people_in_custody` | 2 views reading 4 tables, 12 tables upstream |
| `pipeline_status` | Whether the jobs ran | job `daily_lake` | Runs at 05:00 Central; last success and any failure |
| `platform_health` | Whether the platform is healthy | (nothing) | Healthy: 10 sites and 7 targets up, no alerts, disk and backups fine |
| `search_incident_reports` | The incident reports, with every personal detail replaced | `bridge`, witness statements | 2,017 reports, names shown as `[PERSON NAME]`, `[ALIAS]` and so on |

**Good questions to try:**

- "Which tables hold birth dates, and which data products use them?"
- "If world\_silver.incident changed, what would break?"
- "Did last night's load work, and is anything alerting?"
- "How many fights in Gotham City this year, and are those numbers final?"

**What it can't do.** It can't run SQL, write anything, see a raw name or a restricted value, or start and stop jobs. The server holds no lake credentials and no admin login.

## Find and understand data

Start in OpenMetadata to find a table and learn what it means; use Fuseki when you want to ask the same meaning in a query. Both are rebuilt every morning from the lake and the repo, so nothing in them is typed by hand except a steward's own additions, which are kept.

**OpenMetadata** (`/openmetadata/`) holds the catalog:

| What | How much (Nov 4, 2026) | Comes from |
| --- | --- | --- |
| Lake tables, with columns, types and descriptions | 76 | The lake, plus dbt's descriptions |
| Glossary terms, with synonyms and typed relations | 28 | `glossary/glossary.yml` |
| Tag families: Governance, PIIType, Source, Layer, Refresh, Sensitivity, PII, Lakehouse | 8 | The tagger, dbt and the glossary |
| Lineage edges, table to table | 120 | dbt, marked `DbtLineage` |
| Domains, data products and contracts | 3, 5 and 7 | `products/*.yml` and dbt's contracts |

To find data:

1. **Search** with the bar at the top: a table name, a column, or a business word like *custody*.
2. **Open the table.** The Schema tab shows each column with its type, description and tags. A `PII` or `PIIType.*` tag means personal data; `Sensitivity.Restricted` means Cube masks it.
3. **Open Lineage** to see what the table is built from and what's built from it. Edges marked `DbtLineage` are rebuilt each run; an edge you draw by hand is marked `Manual` and never touched.
4. **Open the Glossary** (Govern → Glossary) for a term's definition, its synonyms, and the columns and metrics it maps to.
5. **Open Domains** for the five data products, their contracts, and who owns them.

**Tags arrive on their own.** As data lands, the tagger tags every table and column: CJIS (and PII when a column holds personal data), the kind of personal data (`PIIType.BirthDate`, `PIIType.FreeText` and so on), the source, the layer and the refresh. Its record is in `ops.table_tags` and `ops.column_tags`.

**Fuseki** (`/fuseki/`) serves the same meaning as RDF, at `<tailnet-host>`. Reading needs no login. Its graphs: the glossary as SKOS with the tables and tags, the 12 business rules, the data products as DCAT with the business inputs each waits on, and the deductions' results. A first query, every term and its synonyms:

```sparql
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
SELECT ?term ?synonym WHERE { ?t skos:prefLabel ?term . OPTIONAL { ?t skos:altLabel ?synonym } } ORDER BY ?term
```

The [ontology guide](https://claude.ai/artifact/QZzDB9Lp8k94cXoU7smD7S) has the worked recipes: terms, relations, the rulebook, which rules hold today, and the SHACL shapes the daily run checks.

## Gold data and data models

Gold tables are built by dbt from silver; Cube turns them into the business model people query. Adding either is a file in the repo, a build command, and a check.

**The layers, and where your model belongs:**

| Layer | Holds | Who writes it |
| --- | --- | --- |
| Bronze | Data exactly as delivered, every column text | The loader |
| Silver | Cleaned and typed; every problem flagged, no row dropped | The loader (course 1's data), dbt (the world) |
| Gold | Certified dimensions and facts, with enforced contracts | dbt: `dbt/models/gold/`, `dbt/models/world/gold/` |
| Marts | Gold reshaped for one domain's questions | dbt: `dbt/models/marts/<domain>/` |
| Cube | Measures, dimensions and views over gold and marts | `cube/model/*.yml` |

### Add a gold table or mart

1. **Write the SQL** as a new file, for example `dbt/models/marts/custody/my_model.sql`. Read other models with `{{ ref('fct_offender_record') }}`, never by table name, so dbt knows the lineage. Start the file with a comment saying what one row is.
2. **Describe it** in the folder's `schema.yml`: a description, an enforced contract, every column with its type, and its tests. Mark personal or restricted columns, and the semantic layer masks what's restricted:

```yaml
  - name: my_model
    description: One row per offender record per month-end it is open.
    config:
      contract: {enforced: true}
    columns:
      - name: month_end
        data_type: date
        data_tests: [not_null]
      - name: race_code
        data_type: varchar
        meta: {sensitivity: restricted}
```

3. **Build it and its tests** from the VM:

```bash
cd ~/lakehouse/lakehouse
docker compose --profile core exec -T jupyter dbt build --project-dir lakehouse/dbt --profiles-dir lakehouse/dbt --select my_model+
```

`--select my_model+` builds your model, everything downstream of it, and all their tests. A contract mismatch or a failing test stops the build and names the column.

4. **Let the morning run take it from there.** `daily_lake` builds every dbt model, so from tomorrow your table is rebuilt daily, tagged, and in OpenMetadata with its lineage.

### Add a data model in Cube

A **cube** describes one table: what a row is, its dimensions, its measures, and how it joins. A **view** is what people query: it picks members from cubes and joins.

1. **Add a cube** to a file in `cube/model/`, pointing at the lake table. People are always `count_distinct` on the SID, never a sum:

```yaml
cubes:
  - name: my_cube
    sql_table: lake.mart_custody.my_model
    public: false
    dimensions:
      - {name: month_end, sql: month_end, type: time}
    measures:
      - {name: records, type: count}
      - {name: people, sql: sid_number, type: count_distinct}
```

2. **Add a view** that people will query. Its `meta.reads` must list the lake tables it reads; a test fails without it:

```yaml
views:
  - name: my_view
    description: What this view answers, and how to count people with it.
    meta:
      reads: [mart_custody.my_model]
    cubes:
      - join_path: my_cube
        includes: [month_end, records, people]
```

3. **Restart Cube** so it reads the file: `docker compose --profile core restart cube`. Then query `SELECT MEASURE(people) FROM my_view` in SQL Lab.

Don't write masks by hand. Which columns Cube masks is decided in OpenMetadata: tag a column `Sensitivity.Restricted` there, then run `scripts/bootstrap.sh`, which rewrites the masks; review the change with `git diff lakehouse/cube/model/`.

**Before you commit,** run the offline tests: `docker compose --profile core exec -T jupyter pytest -q lakehouse/tests`. They check every view has `meta.reads`, every contract, and more.

## Create a data product

A data product is one file in `products/` that promises what some tables answer, who owns them, what they mean, that their shape won't change silently, and how fresh they are. Write the file, run the setup script, and every system publishes and enforces it.

**What one file turns into:**

| The promise | Where it ends up |
| --- | --- |
| The question, owner and description | OpenMetadata, as a Data Product in its Domain |
| The tables it delivers | Your dbt models, with enforced contracts; none may hold a restricted or personal column |
| A shape that won't change silently | OpenMetadata Data Contracts, mirroring dbt's |
| What it means | Glossary terms on its columns; a DCAT dataset in Fuseki |
| Who may see what | Its Cube views, with no restricted members |
| Fresh by when | `max_age_hours`; the `DataProductStale` alert fires past it |
| Whether this month is final | `depends_on` the business inputs that must close each month |

### Steps

1. **Build its tables** as gold or mart models with enforced contracts (see *Gold data and data models*).
2. **Add a Cube view per question** it answers, with no restricted members.
3. **Write `products/<name>.yml`.** Copy a neighbour; this is the Court Outcomes product, whole:

```yaml
name: court-outcomes
title: Court Outcomes
domain: Justice
owner: Lakehouse stewards
question: How many charges do the courts decide each month, how do they end, and how many people are convicted?
description: >
  Every charge from the expanded world's fights, by the month the court decided it, its NIBRS offense code and its
  outcome, with convictions and the distinct people charged. No restricted or personal columns.
tables:            # what the product delivers
  - world_gold.fct_charge
sources:           # where its data comes from
  - world_gold.fct_incident
  - gold.dim_offense
cube_views: [court_outcomes]
glossary_terms: [Charge, Court Outcome, Offense Code, Person Key, Offender Number]
depends_on: [courts]   # the business input that must close each month
refresh: {every: 1, unit: month, at: "05:30", timezone: America/Chicago}
max_age_hours: 768     # 32 days
```

4. **A new domain?** Add `products/domains/<name>.yml` too (copy `justice.yml`).
5. **A new business input?** Add `products/inputs/<name>.yml`: the unit that closes each month, its system, and how many days it has:

```yaml
name: courts
title: Sentencing orders and charge decisions
unit: Courts liaison
system: Court case feed
description: The month's court decisions, entered by the Courts liaison unit.
closes_within_days: 7
```

6. **Publish it:** `bash ~/lakehouse/lakehouse/scripts/bootstrap.sh`, or wait for the 05:00 run. OpenMetadata, Fuseki, the readiness view and monitoring pick it up.
7. **Check it:** `pytest lakehouse/acceptance/test_products.py` in the Jupyter container checks every table, view and term the file names is real. Then ask the agent: `data_product_info` for your product.

**Final or provisional.** Each month of a product is *provisional* until every unit in `depends_on` has closed that month, then *final*. `period_readiness` shows it for every product and month-end, with who it still waits on. To record a close by hand:

```bash
docker compose --profile core exec -T jupyter python lakehouse/readiness/closes.py report courts 2026-10-31 --by "Courts liaison"
```

**People, not records.** A person can hold several records, so a product counts people as distinct SIDs at query time and never stores a people count.

## Check processing and data quality gates

Every morning at 05:00 Central, `daily_lake` loads and checks the data in a fixed order, and a failed gate stops what comes after it. So the first question is always: did today's run pass?

**The gates, in the order the run meets them:**

1. **Land course 1's pinned handoff** as `ref`, `bronze` and `silver`. The files' fingerprints must match the manifest, or nothing lands.
2. **The parity gate:** the 19 Facilitator Guide numbers must match, and every offline test must pass. If one fails, gold is not built.
3. **dbt builds gold and the marts,** running every test and enforced contract. A failing test stops its model and everything built from it.
4. **Tag** every table and column.
5. **Sync** OpenMetadata (tables, tags, lineage, products), then Fuseki.
6. **Check the business rules,** push the quality numbers, and refresh readiness.

The world's monthly jobs run the same way on the 1st: `world_refresh` at 04:30 and `world_monthly_job` at 05:30, the second with the answer-key tests.

### Did it run?

- **In Dagster** (`/dagster/`): open **Runs**. Each run shows its steps in order, green or red; click a red step for its log. **Assets** shows when each table was last built.
- **Ask the agent:** `pipeline_status` for job `daily_lake` gives the schedule, the last success and any failure; `platform_health` says whether anything is alerting.
- **On your phone:** a failed job raises `JobFailing`, which reaches the `lakehouse-alerts` topic in ntfy with a link to its runbook.

### Is the data good?

| Check | Where | What it tells you |
| --- | --- | --- |
| Quality scorecard | `gold.dq_scorecard`; Cube view `dq_scorecard` | Pass rate per dimension, column and rule: completeness, conformity, validity, consistency, uniqueness, timeliness |
| Flagged values (course 1's data) | `silver.hero_offenders_exceptions` | One row per value a rule flagged: unmapped codes, failed conversions, impossible birth dates, offense and violence conflicts |
| Flagged values (the world) | Cube view `world_exceptions`; the agent's `data_quality` | Counts by table and kind of problem |
| dbt tests | The `daily_lake` dbt step in Dagster | Which test failed, on which model and column |
| Business rules | The run's rule-check step; the agent's `business_rules` | Which of the 12 rules hold today |
| Final or provisional | Cube view `period_readiness`; `closes.py status` | Each product's month-ends, and who they still wait on |

A quick look at quality by dimension, in a notebook:

```sql
%%sql
SELECT dimension, round(100 * sum(passed) / sum(checked), 2) AS pass_pct
FROM gold.dq_scorecard GROUP BY 1 ORDER BY 2
```

And who each product is waiting on, from the VM:

```bash
docker compose --profile core exec -T jupyter python lakehouse/readiness/closes.py status
```

**Watching it all.** Grafana's **Home Lakehouse** dashboard (`/grafana/`) shows the platform, the pipeline and the data. Prometheus holds 27 alert rules; each has a runbook in `lakehouse/runbooks/<AlertName>.md`, linked from the alert itself. Critical means act now; warning means look today.

## Enter business rules and data processing rules

Every rule is a file in the repo, never something typed into a tool: Fuseki and OpenMetadata are rebuilt each morning, so a hand edit there is gone the next day. Pick the file by what the rule does.

| The rule | Kind | Write it in | It is enforced by |
| --- | --- | --- | --- |
| "A person is counted once, by SID" | A business rule, stated | `rules:` in `glossary/glossary.yml` | Whatever it names in `enforced_by` |
| "Every SID column is a pseudonymous key" | A deduction: new facts from the catalog | `ontology/rules/<name>.rq` (SPARQL `CONSTRUCT`) | The daily run, into its own graph |
| "Every glossary term has a real definition" | A constraint: what must be true of the metadata | `ontology/shapes.ttl` (SHACL) | Fuseki's validator; a violation fails setup and raises `BusinessRuleViolated` |
| "Every month's snapshot has one row per record" | A data test: what must be true of the rows | `dbt/tests/<name>.sql`, or `data_tests:` in a `schema.yml` | dbt, in the daily run |
| "`N/A` and `UNK` mean no value" | A processing rule: how raw values are cleaned | `dbt/macros/world.sql` (the world); course 1's data dictionary and crosswalks (its data) | The silver models; what can't be cleaned is flagged, never dropped |
| "Alert when a product is stale" | A threshold | `monitoring/` alert rules | Prometheus and Alertmanager |

### A business rule, in the rulebook

State it in plain words, name the glossary terms it is about, and name what enforces it. `enforced_by` must point at something real, prefixed by kind: `cube:`, `dbt:`, `prometheus:`, `shacl:`, `sparql:` or `test:`.

```yaml
rules:
  - name: People are counted by SID
    statement: >
      A person is counted once however many records they hold, by distinct SID at query time; people counts are
      never stored or added up, and records with no SID belong to no known person.
    about: [Person, SID Number]
    enforced_by:
      - cube:custody_population.people_in_custody
      - dbt:dim_person_counts_every_record
```

After the next run, the agent's `business_rules` tool and Fuseki's rulebook graph both show it.

### A data test, in dbt

A dbt test is a query that returns the rows that break the rule; no rows means it passes. Save it as `dbt/tests/<name>.sql`:

```sql
-- Each offender record appears once per month-end in the custody snapshot.
select month_end, offender_number, count(*) as copies
from {{ ref('custody_snapshot_monthly') }}
group by 1, 2
having count(*) > 1
```

For a simple column rule, add it to the column in `schema.yml` instead: `data_tests: [not_null, unique]`, or `accepted_values` and `relationships`.

### A deduction or a constraint, in the ontology

- **A deduction** is a SPARQL `CONSTRUCT` in `ontology/rules/<name>.rq`. The run repeats it until nothing new appears and keeps its results in their own graph, apart from what's stated. Delete the file, and its graph goes too.
- **A constraint** is a SHACL shape in `ontology/shapes.ttl`. Give each property shape a name like `lh:<Shape>-<what>`, so a violation names its rule. `check_rules.py` reports each violation by name.

### A processing rule, in silver

The expanded world's cleaning lives in dbt macros (`dbt/macros/world.sql`). `w_text` trims a cell and turns blanks and the "no value" codes into nulls; other macros read dates in every format, money and codes. To add a code that means "no value", add it to the list in `w_is_token`. Course 1's data dictionary (`NULL_TOKENS`) and crosswalks belong to course 1, in its repo, and reach the lake as `ref.null_tokens` and the other `ref` tables.

**Then publish and prove it:** run `scripts/bootstrap.sh`, and the tests. `acceptance/test_business_rules.py` shows how to prove a shape catches a violation, using a scratch graph.

## Add a new data source

A new source is files in the landing area, one entry in the source register, and a bronze and a silver model in dbt. The expanded world was added exactly this way, so its files are the pattern to copy.

**The path a delivery takes:**

| Step | Where | Rule |
| --- | --- | --- |
| Land the files | `/lake/landing/<source>/` on the VM | Never edited after they land |
| Register the source | `tagging/sources.yml` | Every table it lands gets its governance tags the moment it lands |
| Bronze | a dbt model per table | Exactly as delivered: every column text, plus the file name |
| Silver | a dbt model per table | Typed and cleaned; every problem flagged, no row dropped |
| Gold and products | dbt and Cube | See *Gold data and data models* and *Create a data product* |

### Steps

1. **Land the files** in their own folder, for example `/lake/landing/visitors/`, one subfolder per table.
2. **Register the source** in `tagging/sources.yml`. `people: true` makes the tagger scan its columns for personal data; `governance` sets the tags every one of its tables gets, and tables built from it inherit them through lineage:

```yaml
  - name: visitors
    title: The visitor log, weekly CSVs from the front desk system
    tag: Visitors
    governance: [CJIS]
    refresh: Weekly
    people: true
    tables: [visitors_bronze.*, visitors_silver.*]
```

3. **Write a bronze model per table,** reading the CSVs exactly as written. This is the world's pattern, from `dbt/macros/world.sql`:

```sql
{{ config(alias='visit') }}
-- The visitor log as delivered: every column VARCHAR, with the file it came from.
SELECT * FROM read_csv('/lake/landing/visitors/visit/*.csv', all_varchar = true, header = true, filename = true)
```

4. **Write a silver model per table** that types and cleans each column and flags what it can't: use `w_text` for text, and the date and code macros beside it in `dbt/macros/world.sql`. Keep the bad values with a flag; the world's `ws_*` models show how.
5. **Describe both** in a `schema.yml`: a description per table, `meta: {sensitivity: personal}` or `restricted` on columns that need it, and tests. Give the folder its own schemas in `dbt_project.yml` with `+schema`, as `models/world/` does.
6. **Build it:** `dbt build --select <folder>` as in *Gold data and data models*. From tomorrow `daily_lake` builds it every morning, the tagger tags it, and OpenMetadata shows it with lineage.
7. **Check the tags it got:** in OpenMetadata, or ask the agent `find_by_tags` for `Source.Visitors`. If a personal column was missed, add a rule to `tagging/rules.yml`.

A source that needs a Python step to fetch or reshape it before it lands (an API, a database extract) is a pipeline: see the next section.

## Build a new data pipeline

In Dagster, a pipeline is a set of **assets** (a table, a file, a published catalog) and a **job** that builds them on a **schedule**. Most new pipelines need no Dagster code at all, because every dbt model is already an asset.

**Which kind of pipeline you need:**

| Your pipeline | What to write | When it runs |
| --- | --- | --- |
| Only dbt models (SQL), daily | The models; nothing in Dagster | In `daily_lake` at 05:00, automatically: it builds every dbt model not tagged `world` |
| A Python step (fetch from an API, reshape files, publish somewhere) | An asset in `orchestration/definitions.py` | In `daily_lake` too, unless you give it its own job |
| A different schedule (weekly, monthly, on demand) | A job and a schedule | When its schedule says |
| One month at a time, with backfills | A partitioned asset and job | Each month; backfill any range from the Dagster UI |

### A Python step

Add an asset to `orchestration/definitions.py`. `deps` says what must be built first, so Dagster runs it in the right order. Every function gets a docstring:

```python
@dg.asset(key=["landing", "visitors"], group_name="visitors", kinds={"python", "csv"},
          description="The front desk's visitor log, fetched each morning into /lake/landing/visitors.")
def visitors_landing(context: dg.AssetExecutionContext):
    """Fetch the latest visitor log and write it as CSV under /lake/landing/visitors/visit/."""
    ...
```

Then add it to the `assets=[...]` list in `defs = dg.Definitions(...)` at the bottom of the file. A dbt bronze model that reads those files declares the dependency with a `-- depends_on:` comment, as the world's bronze models do.

### Its own job and schedule

```python
visitors_weekly = dg.define_asset_job("visitors_weekly", selection=dg.AssetSelection.groups("visitors"))
visitors_schedule = dg.ScheduleDefinition(job=visitors_weekly, cron_schedule="0 6 * * 1",
                                          execution_timezone="America/Chicago")
```

Add the job to `jobs=[...]` and the schedule to `schedules=[...]` in `Definitions`. Take the assets out of `daily_lake` the way the world's are (`dg.AssetSelection.all() - WORLD_ASSETS`), or they run there too.

### One month at a time

Use the world's `MonthlyPartitionsDefinition` pattern (`world_months`, starting 1996-01-01): a partitioned asset builds one month per run, and the job's schedule builds each month as it closes. To build history, open the asset in Dagster and choose **Materialize → backfill** with a date range.

### Load it, run it, watch it

1. **Run the offline tests:** `docker compose --profile core exec -T jupyter pytest -q lakehouse/tests`.
2. **Load the new code:** in Dagster, **Deployment → Reload**, or `docker compose --profile core restart dagster-webserver dagster-daemon`.
3. **Run it once by hand:** open the job, **Launchpad → Launch run**, and watch each step go green.
4. **Turn its schedule on** under **Automation** if it isn't already.

Every job gets the success and failure sensors automatically, so a failed run raises `JobFailing` on your phone, like the daily run does.

## AI, BI and dashboards

Build dashboards in Superset, on Cube's governed views; ask questions in plain words through the AI agent; watch the platform in Grafana. All three read through governed paths, so masks and people counts hold everywhere.

| Tool | Use it for | Reads |
| --- | --- | --- |
| Superset (`/superset/`) | Dashboards and charts for the business; SQL Lab | Cube only |
| The AI agent (MCP) | Plain-word questions, definitions, lineage, health | Cube and the catalog |
| Jupyter (`/jupyter/`) | Analysis in Python and SQL | The lake (read-only) or Cube |
| Grafana (`/grafana/`) | The platform, pipeline and data-quality trends | Prometheus |

**The three dashboards today:** **Trust Test** (`/superset/dashboard/trust-test/`), course 1's eight questions before and after cleansing; **Custody** (`/superset/dashboard/custody/`), people in custody by month-end, level and offense; and **Fights, Damage and Courts** (`/superset/dashboard/world/`), the expanded world's three products. Each starts with a status table saying which months are final.

### Build a chart and a dashboard in Superset

1. **Add the dataset once:** **Datasets → + Dataset**, database **Cube**, then pick the view, for example `field_incidents`.
2. **Make a chart:** open the dataset, choose a chart type, and set the metric to **Custom SQL** using Cube's measure, for example `MEASURE(fights)`. For people, always use the view's people measure (`MEASURE(people_in_custody)`): Superset must never sum or count people itself.
3. **Add the month and `period_status`** to the chart or the dashboard, so readers can see which numbers are still provisional.
4. **Save it to a dashboard:** **Save → Add to dashboard**, then arrange the charts and publish.

A dashboard built in the browser lives in Superset's own database. To keep it in the repo, rebuilt the same way on every setup, add an entry to `DASHBOARDS` in `superset/dashboards.py`: a title, a slug, its charts (each naming a Cube view, a chart type and its measure) and their rows. Then run `scripts/bootstrap.sh`; a re-run changes nothing.

### Other BI tools

Cube's SQL interface speaks the Postgres protocol, so most BI tools can connect to it as a Postgres database. Today it listens only on the VM's own network (`cube:15432`), so from your laptop use Superset or the agent. Reaching Cube from an outside tool, such as Power BI or Tableau, would need that port published through the tailnet; it isn't set up.

### The AI agent as an analyst

The agent (see *Ask the AI agent*) is the quickest way to an answer you trust: it picks the governed metric, says whether the month is final, and names the tables behind the number. Ask it to explain a dashboard's number with `lineage`, or to check a product before a meeting with `data_product_info`.

## Quick reference

Run the commands on the VM, from `~/lakehouse/lakehouse`. Every `docker compose ... exec -T jupyter` command runs inside the Jupyter container, where the tools are installed. Paths are inside `lakehouse/` in the repo.

| To | Run or edit |
| --- | --- |
| Query the lake in a notebook | `%load_ext lakehouse.sql_magic`, then `%%sql` |
| Query in Python | `from lakehouse import lake; con = lake.lake_ro_connect()` |
| List lake snapshots, for time travel | `SELECT snapshot_id, snapshot_time FROM lake.snapshots()` |
| Query Cube | `psycopg2.connect(host="cube", port=15432, dbname="cube", user="lake", ...)`; `MEASURE(name)` |
| Connect the AI agent | `claude mcp add --transport http --scope user lakehouse <tailnet-host> --header ...` |
| Build dbt models and their tests | `docker compose --profile core exec -T jupyter dbt build --project-dir lakehouse/dbt --profiles-dir lakehouse/dbt --select <model>+` |
| Restart Cube after a model change | `docker compose --profile core restart cube` |
| Publish products, rules, masks, dashboards | `bash scripts/bootstrap.sh` |
| Check everything is in step | `bash scripts/bootstrap.sh --check` |
| Readiness: who a month waits on | `docker compose --profile core exec -T jupyter python lakehouse/readiness/closes.py status` |
| Record a business unit's close | `... closes.py report <input> <YYYY-MM-DD> --by "<unit>"` |
| Run the offline tests | `docker compose --profile core exec -T jupyter pytest -q lakehouse/tests` |
| Run the CI checks | `bash ci/checks.sh` |
| Load new Dagster code | Dagster → Deployment → Reload |

| File | What you put there |
| --- | --- |
| `dbt/models/gold/`, `dbt/models/world/gold/`, `dbt/models/marts/<domain>/` | Gold tables and marts (SQL + `schema.yml`) |
| `dbt/tests/<name>.sql` | Data tests: a query returning the rows that break a rule |
| `dbt/macros/world.sql` | Cleaning rules for silver (`w_text`, `w_is_token`, dates, money, codes) |
| `cube/model/*.yml` | Cubes and views; every view lists `meta.reads` |
| `products/<name>.yml`, `products/domains/`, `products/inputs/` | Data products, domains and the business inputs that close each month |
| `glossary/glossary.yml` | Glossary terms, and the business rulebook under `rules:` |
| `ontology/rules/<name>.rq`, `ontology/shapes.ttl` | Deductions (SPARQL) and constraints (SHACL) |
| `tagging/sources.yml`, `tagging/rules.yml` | Data sources and their tags; the personal-data rules |
| `orchestration/definitions.py` | Dagster assets, jobs and schedules |
| `superset/dashboards.py` | Dashboards kept in the repo |
| `runbooks/<AlertName>.md` | What to do when an alert fires |

**Before any change you commit:** write the test first and see it fail, run `lakehouse/tests`, and never put a password, a Tailscale name or address, or a real organization's name in the repo.
