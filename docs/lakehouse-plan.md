> Snapshot of the live Claude Doc (https://claude.ai/artifact/Js8ovfd7HE7BJ5Sj6TS3Sj), kept for safe keeping. Network addresses are redacted. The Claude Doc is the current copy.

# DuckDB Home Lakehouse Plan

Updated Nov 2, 2026 · @wrolfgar

## Summary

Build one Debian VM on the Proxmox host (<proxmox-host-ip>) running Docker Compose, with DuckLake as the lakehouse format, Postgres as its catalog, and Parquet on local disk. The course generator feeds bronze, the course's own pandas cleansing produces silver, and dbt builds gold. Cube is the semantic layer, OpenMetadata is the ontology layer, and Prometheus/Grafana watches all of it. Seven phases, roughly 10 to 12 of your night research sessions.

Decisions baked into this plan:

- **DuckLake 1.0, not a single .duckdb file.** A plain DuckDB file allows one writer, which breaks the moment Jupyter, Superset, Cube and a pipeline all touch it. DuckLake keeps metadata in Postgres so many DuckDB clients can read and write the same tables, with snapshots and time travel.
- **Pin DuckDB 1.5.x now, upgrade to 2.0 later.** DuckDB 2.0.0 LTS shipped October 21, 2026, with a built-in client-server mode and DuckLake 1.1. It's three days old and the first patch is due in November. Run the upgrade as its own phase once 2.0.1 lands.
- **No MinIO.** MinIO's repo was archived April 25, 2026 and community images stopped in October 2025. Local disk is enough for a 100k-row dataset. If you want S3 semantics to mirror the agency's cloud pattern, use Garage or SeaweedFS.
- **Docker Compose, not Kubernetes, for the first pass.** One node gains nothing from k3s except overhead. Phase 7 is an optional k3s move if you want the practice.
- **Cube maps to Unity Catalog metric views; OpenMetadata maps to Domains, Pages and governed tags.** Same split as the agency deck: OpenMetadata authors meaning, the serving layer enforces it.

I confirmed the core path works before writing this. The generator builds 100,000 rows in 10 seconds, `clean_through(4)` runs in about 4 seconds, and the result lands in DuckDB with correct BIGINT, DATE, TIME, DECIMAL(12,2) and BOOLEAN types. The DuckLake extension itself couldn't be downloaded from my sandbox, so its first run on your box is the first test of that piece.

## Where it stands (November 2, 2026)

Phases 0 to 6 are built and running, Phase 7 waits on DuckDB 2.0.1, and a Phase 8 the original plan didn't have, the expanded world, is nine chunks in. On November 2 the course 1 / course 2 boundary was built: the lake now lands course 1's frozen, checked output instead of running course 1's code. The phase sections below are the plan as written; this table says what was actually built.

| Phase | Status | As built, where it differs from the plan |
| --- | --- | --- |
| 0. Proxmox build | Done | One Debian VM. Resized October 28 for the expanded world: 12 vCPU, 47 GiB RAM, 148 GB root disk, 1 TB `/lake`. Reached over the tailnet only; nothing is port-forwarded |
| 1. Platform services | Done | Compose with profiles, every image and package pinned in the repo (never in `.env`); Cube 1.8.3, Superset 6.1.0, OpenMetadata 2.0.5, our own verified Fuseki image |
| 2. Generator and medallion layers | Done | Changed November 2: course 1 publishes its cleansed output as a pinned handoff, checked against the Facilitator Guide's 19 numbers before it's published. The lake lands that handoff under a written contract (13 tables, keys and column types) instead of rerunning course 1's cleansing. dbt builds gold |
| 3. Run the notebooks | Done | The seven notebooks run in the lab and, while the course 1 add-on is on (LAKEHOUSE\_COURSE1, on by default), weekly in `notebook_smoke` |
| 4. Query layer | Done | Cube attaches DuckLake read-only through `initSql`, so no serving file was needed. Superset and the MCP agent go through Cube; only engineering attaches to DuckLake directly |
| 5. Semantic and ontology stack | Done | Masks in Cube come from OpenMetadata's Restricted tags (`sync_masks.py`). The glossary and column tags go to Fuseki as RDF, with SPARQL deduction rules and SHACL shapes for the business rules. Since November 2 every table and column is also tagged automatically as data lands (Governance such as CJIS and PII, PIIType, Source, Layer, Refresh) |
| 6. Monitoring and alerting | Done | Prometheus, Grafana and Alertmanager in the VM's own monitoring profile. Alerts go to a self-hosted ntfy server on the phone, not PagerDuty |
| 7. Upgrades | Waiting | DuckDB 2.0 waits for 2.0.1; k3s not started |
| 8. The expanded world | Chunks 0 to 9 done | See Phase 8 below |

Built beyond the plan:

- **Data products** (five, in three domains: Custody Operations, Field Operations and Justice): descriptor files drive OpenMetadata's domains, products and contracts, DCAT, Cube views, Superset dashboards and freshness alerts.
- **Data readiness:** the business units' closes and declared inputs feed a live `period_readiness` view that marks each month final or provisional.
- **Ops hardening:** weekly DuckLake housekeeping (30 days of history), `ci/checks.sh` with GitHub Actions CI on every push, runbooks, nightly catalog dumps and restic backups. The backups still go to a local folder on the VM; moving them off the VM (TrueNAS) is set aside until you raise it.
- **The MCP agent's seven tools:** `query_metric` (with filters and time ranges), `define_term`, `list_metrics`, `business_rules`, `data_product_info` (a product's promise, contracts, readiness and freshness in one answer), `data_quality` (the course scorecard and the world's flagged values, counts only) and `find_by_tags` (tables and columns by any tags they carry: one, any of many, or all, on tables, columns or both).
- **pugwala/homelake:** the lab's own copy of the repo, without the course name. Work lands in the course repo's `duckdb-lakehouse` branch and is cherry-picked there.
- **The course boundary:** course 1 is sessions 1 to 7; course 2 is the lakehouse ([boundary doc](https://claude.ai/artifact/R1688c4LU7fYfwiQGJQDij)). Course 2 starts from course 1's pinned handoff (`lakehouse/handoff/`) and runs none of its code. Course 1's Trust Test, parity gate and notebook smoke are an add-on behind one switch, `LAKEHOUSE_COURSE1`, and CI proves the platform builds with it off.
- **Automatic tags:** `lakehouse/tagging/` registers each source (`sources.yml`) and holds the column rules (`rules.yml`). Every daily run tags each table and column, follows dbt lineage into gold, and publishes the tags to OpenMetadata. Live: 54 CJIS tables, 26 with personal data, 86 personal columns.

How the risks below turned out:

- Cube did attach DuckLake directly, read-only, so the serving-file fallback wasn't needed.
- dbt-duckdb on DuckLake works, including incremental models and enforced contracts.
- The single VM is still the biggest exposure until the backups go off it.

## Target architecture

&#91;embedded content: home lakehouse architecture as built · 4 columns, 1 band\]

Read left to right: course code and the business units' closes build each layer daily, DuckLake stores it, OpenMetadata, Fuseki and Cube give it meaning, rules and readiness, and people reach it through Cube, the MCP agent and Superset, only on the tailnet. Only engineering attaches to DuckLake directly, read-only. Monitoring watches every service and rule, and alerts reach your phone. As built on October 27, 2026. It doesn't yet show that evening's additions (housekeeping, CI, runbooks, backups) or the expanded world (Phase 8).

## Phase 0: Proxmox build (1 session)

One full VM, not an LXC container. Docker inside unprivileged LXC works but fights you on nesting, overlay storage and cgroup limits, and OpenSearch is the first thing to break.

| Item | Setting | Why |
| --- | --- | --- |
| Guest OS | Debian 13, cloud-init template | Stable, small, matches most container base images |
| vCPU | 8 (CPU type `host`) | DuckDB and local Spark scale with cores; `host` exposes AVX2 to DuckDB |
| RAM | 32 GB, ballooning off | OpenSearch (\~6 GB) + OpenMetadata (\~3 GB) + Spark session 5 (\~4 GB) + Superset, Cube, Jupyter, Postgres |
| Disk 1 | 40 GB, OS + Docker | Keeps images and logs off the data disk |
| Disk 2 | 200 GB on ZFS or LVM-thin, mounted at `/lake` | DuckLake Parquet, landing files, backups; ZFS gives you snapshots |
| Network | Static IP on vmbr0, e.g. <vm-lan-ip> | Stable target for Prometheus scrapes and DNS |
| Proxmox backup | Nightly vzdump of the VM | Rollback before risky upgrades (the DuckDB 2.0 phase) |

Steps:

1. Create the VM from a Debian 13 cloud image, enable the QEMU guest agent, set CPU type to `host`.
2. Install Docker Engine and the Compose plugin from Docker's apt repo. Install `git`, `just` or `make`, and `chrony`.
3. Format disk 2, mount at `/lake`, create `/lake/{landing,data,catalog-backups,notebook-runs}`.
4. Add a local DNS name (`lake.home.arpa`) and put Caddy in front of every web UI with an internal CA. Nothing gets port-forwarded from the internet.
5. Fork `pugwala/lunch-and-learn-data-cleansing` and create a `duckdb-lakehouse` branch. All new code lives in a `lakehouse/` folder plus one helper module, so `main` stays clean for the Databricks course.

If the host has less than 48 GB total RAM, drop the VM to 24 GB and run OpenMetadata only when you're working on Phase 5.

## Phase 1: Platform services (1 to 2 sessions)

One `lakehouse/compose.yaml` with profiles, so you can bring up the core without the metadata stack: `docker compose --profile core up -d`, then `--profile governance` and `--profile monitoring` as you reach those phases.

| Service | Profile | Image / version | Role |
| --- | --- | --- | --- |
| `catalog-pg` | core | Postgres 17 | DuckLake catalog; separate `superset` and `dagster` databases |
| `jupyter` | core | `quay.io/jupyter/pyspark-notebook` + DuckDB 1.5.6 | Runs the seven notebooks; ships Java and Spark for session 5 |
| `dagster` (webserver + daemon) | core | Dagster OSS | Schedules generate → bronze → silver → gold → publish |
| `cube` | core | Cube Core ≥ 1.6.23 | Semantic layer; Postgres-wire SQL API on 15432, REST on 4000 |
| `superset` | core | Apache Superset | SQL Lab and dashboards through Cube |
| `openmetadata` + `opensearch` + `om-ingestion` | governance | OpenMetadata 1.13.x or 2.0.x | Glossary, classifications, domains, ontology, MCP |
| `jena-fuseki` | governance | Apache Jena Fuseki | RDF store OpenMetadata's knowledge graph requires |
| `node-exporter`, `cadvisor`, `postgres-exporter`, `blackbox`, `pushgateway` | monitoring | Prometheus exporters | Feed your existing Prometheus/Grafana |
| `caddy` | core | Caddy 2 | TLS and one hostname per UI |

Conventions that save pain later:

- **One shared mount.** Every container that touches data mounts `/lake` at the same path, so a DuckLake `DATA_PATH` of `/lake/data/` resolves identically everywhere.
- **One DuckLake attach string**, kept in `.env` and in a tiny `lake_connect()` helper: `ATTACH 'ducklake:postgres:dbname=ducklake host=catalog-pg' AS lake (DATA_PATH '/lake/data/')`.
- **Pin everything.** Image tags and Python packages pinned in the repo; Renovate or a monthly manual bump. DuckDB extension versions must match the DuckDB version in every container, so the Jupyter, Dagster and Cube images all pin the same DuckDB.
- **Secrets in `.env`, never in the repo.** Postgres passwords, the Cube API secret, the OpenMetadata bot token, the PagerDuty routing key.

## Phase 2: Generator and medallion layers (2 sessions)

Silver comes straight from the course's own cleansing code, so the lakehouse and the class always agree on every standardized value. That's the point of reusing the repo instead of rewriting the rules in SQL.

| Layer | DuckLake schema.table | Built by | Contents |
| --- | --- | --- | --- |
| Landing | `/lake/landing/*.csv` | `env.generate()` with `LNL_DATA_DIR=/lake/landing` | Raw CSV + answer key, seed 2026, 100,000 rows |
| Reference | `ref.unit_crosswalk`, `ref.race`, `ref.religion`, `ref.stg_groups`, `ref.nibrs_offenses`, `ref.violence_codes` | Loaded from `lnl/reference/*.csv` | The crosswalks, versioned by snapshot |
| Bronze | `bronze.hero_offenders_raw` | `read_csv(..., all_varchar = true)` + `_ingested_at`, `_source_file`, `_seed`, `_data_version` | Untouched text, every column VARCHAR |
| Bronze | `bronze.conduct_notes_answer_key` | Same | Scoring only; tagged restricted |
| Silver | `silver.hero_offenders` | `lnl.pipeline.clean_through(4)` | Typed, crosswalked, `offender_number` BIGINT key |
| Silver | `silver.hero_offenders_exceptions` | Rule checks | One row per flagged value, with the rule; records stay in silver (flag, don't fix) |
| Gold | `gold.dim_unit`, `gold.dim_offense`, `gold.dim_stg_group`, `gold.fct_offender_record`, `gold.dq_scorecard` | dbt-duckdb 1.11 | Certified, documented, tested |

Work items:

1. **Write `lnl/lake.py`** (about 100 lines): `lake_connect()`, `write_bronze()`, `write_silver(df)`, `snapshot_note()`. Session notebooks stay untouched.
2. **Fix ordered codes on the way into silver.** In my test, pandas ordered categoricals (`custody_level` G1–G5, `threat_level`, `violence_code_std`) landed as plain VARCHAR and lost their order. Write them as DuckDB `ENUM` types, or carry an `_rank` column from the reference table.
3. **Reconcile.** Port the course's 22 reconciliation metrics into a dbt test or SQL check: pandas silver vs DuckDB-recomputed counts must match to the cent, same as the Spark session does.
4. **Gold in dbt.** `dbt-duckdb` attaches DuckLake through its `attach` profile setting. Verify that path on 1.11 first; if it misbehaves, run gold as plain SQL from Dagster and add dbt later.
5. **Data-quality scorecard.** `gold.dq_scorecard` scores each column on your seven dimensions (DAMA's six, with validity split into conformity and validity) per run. That table feeds Grafana and the ontology later.
6. **Orchestrate in Dagster.** One asset per table, a daily schedule, and a manual `regenerate` job. Every run becomes a DuckLake snapshot, so `SELECT ... AT (VERSION => n)` lets you diff runs.

Port of the enterprise track: the `enterprise/` notebooks call Unity Catalog, Lakeflow and the Databricks SDK, so they don't run here. Their concepts map across: Lakeflow expectations become dbt tests with `warn`, quarantine and `error` severities; the scheduled job with PagerDuty becomes the Dagster schedule plus a failure sensor; column masks on race and religion move to Cube (Phase 5).

## Phase 3: Running the seven notebooks (1 session)

The notebooks already run outside Databricks with no edits. `lnl/env.py` detects that it isn't on Databricks, writes data to `LNL_DATA_DIR`, and session 5 starts a local Spark session and saves Parquet instead of a Delta table. The repo's README says all seven were executed end to end this way on pandas 3.0 and PySpark 4.2.

| Session | What it needs on this box | Change |
| --- | --- | --- |
| 1–4 Meet the Mess → Types | pandas ≥ 2.0, PyArrow | None |
| 5 PySpark | Java 17+, PySpark 4.x, \~4 GB driver memory | None; the `pyspark-notebook` image ships Java and Spark |
| 6 Text I | spaCy + the model wheel in `wheels/` | None |
| 7 Text II | sentence-transformers + `all-MiniLM-L6-v2` | Pre-download the model to `/lake/models` and set `EMBEDDING_MODEL` to that path, so runs don't depend on Hugging Face being up |

Steps:

1. Build a `lnl-jupyter` image from `pyspark-notebook` with `requirements.txt`, `duckdb==1.5.6`, `jupysql`, `papermill` and the spaCy wheel baked in. The setup cell's `pip install` then finds everything present and never touches the network.
2. Mount the repo at `/home/jovyan/course` and `/lake` at `/lake`. Set `LNL_DATA_DIR=/lake/landing`.
3. Run sessions 1 to 7 interactively once, filling the `___` blanks from the answer keys, to confirm the numbers match the Facilitator Guide.
4. Add a Dagster job, `notebook_smoke`, that runs all seven as delivered through papermill into `/lake/notebook-runs/<date>/` weekly. It pushes pass/fail and duration per notebook to Pushgateway, which gives you a regression test whenever the generator or a dependency changes.
5. Add one new notebook, `lakehouse/08_from_lake.ipynb`, that rebuilds sessions 1 and 4's Trust Test from `lake.silver` and `lake.gold` through DuckDB SQL. This is the bridge from "pandas on a CSV" to "querying the lakehouse."

Leave the session notebooks themselves alone, so the same files keep working on Databricks for the course.

## Phase 4: Query layer (1 to 2 sessions)

Run queries through Cube's Postgres-wire SQL API by default, and keep raw DuckLake access for engineering. DuckDB has no grants or masks of its own, so the semantic layer is the only place a rule like "race is masked for analysts" can actually be enforced.

| Path | Who | How it connects | Sees |
| --- | --- | --- | --- |
| Superset SQL Lab + dashboards | Analysts, demo audiences | Postgres driver → Cube SQL API (port 15432) | Gold metrics and dimensions, masked per role |
| Jupyter with `jupysql` (`%%sql`) | You, engineering | `lake_connect()` → DuckLake | Every layer, bronze to gold, plus time travel |
| DuckDB CLI over SSH | Quick checks | Same attach string | Every layer |
| AI agent over MCP | Claude, your home-lab MCP server | Your MCP server → Cube REST (`/load`) + OpenMetadata API | Governed metrics plus glossary meaning |
| DuckDB 2.0 Quack server (later) | Remote DuckDB clients | `ATTACH 'quack:lake.home.arpa'` with a token, behind Caddy TLS | Every layer; Phase 7 only |

Steps:

1. Point Superset at Cube as a Postgres database. Build one dashboard from the Trust Test questions so you can show the same answers the class gets.
2. Install `jupysql` in the Jupyter image and save a `%sql` connection that runs the DuckLake attach on connect.
3. Wire your existing MCP server experiment to two tools: `query_metric` (Cube REST) and `define_term` (OpenMetadata glossary). That's the home-lab stand-in for Genie: the agent asks for a governed metric by name instead of writing SQL against bronze.
4. Create a read-only Postgres role for the DuckLake catalog and use it for every reader. Writers (Dagster) get the read-write role. That's the closest thing DuckLake has to grants.

One caution: Cube's DuckDB driver documents a database file path, S3 settings and extension lists, but not an init statement to attach DuckLake. Test the attach first. If it won't take, have Dagster publish gold as a read-only `/lake/serving/gold.duckdb` after each run and point Cube at that file. That's also the cleaner "certified gold" boundary.

## Phase 5: Semantic and ontology stack (3 sessions)

This is the agency stack from the October deck, rebuilt with open-source parts: Cube computes metrics one way, OpenMetadata says what things mean and how they relate, and an MCP agent reads both. The same rule from the deck applies here: a term that lives only in OpenMetadata is invisible to the serving layer until something syncs it.

| Agency stack (Databricks) | Home lab equivalent | Owns |
| --- | --- | --- |
| Unity Catalog metric views | Cube cubes and views (YAML) | Measures, dimensions, synonyms |
| Governed tags + ABAC, column masks | OpenMetadata classifications → generated Cube access policies with `member_masking` | Sensitivity labels and their enforcement |
| UC Domains | OpenMetadata Domains and Data Products | Ownership boundaries |
| UC Pages / business glossary | OpenMetadata glossary with typed relations (synonym, broader, partOf) | Entity definitions, system of record |
| Formal ontology (RDF/OWL/SHACL) | OpenMetadata 1.13 Ontology Explorer + RDF knowledge graph on Apache Jena | Machine-readable graph of terms and assets |
| Genie Ontology | Your MCP server over Cube + OpenMetadata | Answers in governed terms |

### 5a. Semantic layer in Cube (1 session)

- **One cube per gold table**, plus an `offender_overview` view that joins them for consumers.
- **Measures:** offender records, distinct persons (by `sid_number`), escape-risk rate, protective-custody rate, average disciplinary points, total restitution owed, DQ score by dimension.
- **Dimensions:** unit, custody level, threat level, violence code, offense-against category, intake month. Ordered codes get explicit sort order.
- **Agent metadata:** every measure carries a description and synonyms in `meta`, the same job agent metadata does in UC metric views.
- **Masking:** `race_code`, `race_omb`, `religion_group`, `religion_family` and `stg_group` get a `mask`. An `analyst` role sees masked values; a `restricted` role sees real ones. Data masking needs Cube Core 1.6.23 or newer.

### 5b. Ontology in OpenMetadata (2 sessions)

1. **Classifications** (the governed-tag analog): `Sensitivity` (Restricted, Internal), `QualityDimension` (your seven), `Layer` (Bronze, Silver, Gold, Reference).
2. **Domains:** the two or three domains from your 24-domain taxonomy this dataset touches, each with a data product for its gold tables.
3. **Glossary:** about 15 terms to start: Offender Record, Offender Number, SID Number, Unit, Custody Level, Threat Level, STG Affiliation, Offense Code (NIBRS), Violence Code, Restitution, Escape Risk, Protective Custody, Conduct Note. Add typed relations, for example Offender Number *identifies* Offender Record and Offense Code *broader* Offense-Against Category.
4. **Metadata push, not pull.** OpenMetadata has no DuckDB or DuckLake connector. The one community DuckLake connector calls itself an exploratory sketch. Write `lakehouse/om_sync.py` against the `openmetadata-ingestion` 2.0.x SDK: create a Custom Database service, push schemas, tables and columns from DuckLake's `information_schema`, descriptions from dbt's `manifest.json`, and classification tags. Run it as the last Dagster step.
5. **Lineage:** run OpenMetadata's dbt ingestion against the same service for bronze → silver → gold lineage. Verify table names line up with what `om_sync.py` pushed before trusting it.
6. **Close the loop:** `om_sync.py` also reads which columns carry `Sensitivity.Restricted` and regenerates Cube's access-policy file. Tag a column in OpenMetadata, the next run masks it in Cube. That's the OpenMetadata-to-Unity-Catalog sync problem from the deck, solved in code you own.
7. **Knowledge graph:** run Jena Fuseki and the RDF index app so the Ontology Explorer works, then try SPARQL over the graph. SHACL shapes for the glossary are optional and worth one session only if you plan to push RDF at the agency.

## Phase 6: Monitoring and alerting (1 session)

Everything reports into the Prometheus/Grafana stack you already run at home, and pages through PagerDuty. Monitoring covers the platform and the data: a pipeline that succeeds while quarantining 40% of rows is a failure.

| Signal | Source | Alert when | Routes to |
| --- | --- | --- | --- |
| Proxmox host CPU, RAM, ZFS pool, VM state | `prometheus-pve-exporter` | Pool > 80% full; VM down 5 min | PagerDuty |
| VM and containers | `node-exporter`, `cadvisor` | Disk `/lake` > 80%; container restart loop | PagerDuty |
| DuckLake catalog | `postgres-exporter` | Catalog down; connections > 80% of max | PagerDuty |
| UIs and APIs (Superset, Cube, OpenMetadata, Jupyter, Dagster) | `blackbox-exporter` HTTP probes through Caddy | Probe fails 3 times; TLS cert < 14 days | PagerDuty |
| Pipeline runs | Dagster failure sensor + Pushgateway metrics | Any run fails; daily run missing by 6 AM | PagerDuty |
| Data quality | `gold.dq_scorecard` → Pushgateway per run | Any dimension score drops > 2 points run over run; records with exceptions > 5% | PagerDuty (warning) |
| Notebook regression | `notebook_smoke` job | Any of the 7 notebooks fails | Email |

Steps:

1. Add scrape jobs for the VM's exporters and the Proxmox host to your existing Prometheus.
2. Push per-run metrics from Dagster: rows in, rows quarantined, run seconds, snapshot ID, DQ score per dimension.
3. Build one Grafana dashboard, "Home Lakehouse," with three rows: platform, pipeline, data quality. Grafana can also query gold directly through Cube's Postgres endpoint for the DQ trend panels.
4. Alertmanager to PagerDuty with a routing key for this service. Work ticketing systems (ServiceNow and the like) stay out of the home lab; Alertmanager's generic webhook receiver is where they'd plug in at the agency.
5. Back up the Postgres catalog nightly with `pg_dump` to `/lake/catalog-backups`, and alert if the newest dump is older than 26 hours. Lose the catalog and the Parquet files are just files.

## Phase 7: Upgrades (optional, 1 to 2 sessions)

- **DuckDB 2.0 + DuckLake 1.1**, after 2.0.1 ships. Take a vzdump and a catalog dump first. Files written by 2.0 can't be read by older DuckDB, so upgrade every container's DuckDB in one change. Then try the Quack client-server mode, which listens on localhost by default and wants a TLS proxy for remote access.
- **k3s**, if you want Kubernetes practice. Convert the Compose file with Kompose as a starting point, use the OpenMetadata Helm chart, and keep `/lake` as a hostPath or local-path volume. Expect this to be more work than everything in Phase 1.

## Phase 8: The expanded world (12 chunks, started October 28)

The course's 100,000 records are one flat list. Phase 8 builds the world around them, lakehouse-only, with the course itself unchanged: about 16.6M rows at scale M covering people (today's 86,879 villains plus heroes, secondary heroes and civilians), powers, teams, places, fights with their participants, power uses and damages, charges and court outcomes linked back to today's offender records, and missions. Each chunk stops for your go-ahead.

| Chunk | What | Status |
| --- | --- | --- |
| 0 | Data model | Approved November 1 |
| 1 | Resize the lab | Done October 28 |
| 2 | Generator foundation (`lakehouse/universe`): deterministic, chunked, the S/M/L knob, a fingerprinted manifest | Done November 1 |
| 3 | People, powers, places | Done November 1 |
| 4 | Fights: participants, power uses, damages | Done November 1 |
| 5 | Charges linked to today's records; missions. 5b: new villains fight more, so convictions outnumber dismissals | Done November 1 |
| 6 | Built-in mess with answer keys: a messy CSV copy of every table, plus an exact key, 8.3M defects at M | Done November 2 |
| 7 | Lake layers: `world_bronze`, `world_silver` (cleaned, every problem flagged), `world_gold` (contracts enforced), tested against the answer key. In Dagster, `world_refresh` runs on demand and the big facts run monthly by partition from 1996-01 (a full backfill takes about 2 minutes) | Done November 2 |
| 8 | Glossary, ontology, rules for the new entities | Done November 2: 12 glossary terms with typed relations (a new `occursAt`: Incident occurs at Location), the world's schemas in OpenMetadata with personal and restricted tags, and six new rules (five dbt tests, one SHACL shape) |
| 9 | Data products, Cube, dashboards, readiness inputs (Field Ops, Insurance, Courts) | Done November 2: Field Incidents and Incident Damage (Field Operations) and Court Outcomes (Justice), served by four Cube views and a Fights, Damage and Courts dashboard, waiting on Field Operations', Insurance's and the Courts liaison's monthly closes, with monthly contracts and honest freshness |
| 10 | Scale-up (L) and benchmarks | After incident\_report, on wrolfgar's go-ahead |
| 11 | Course sessions (optional) |  |

Next, before chunk 10: `incident_report`, about 200k free-text fight write-ups for the text-analysis sessions. It's in the approved model but not built yet. The tagger's free-text rule should tag it PIIType.FreeText as it lands.

## Gaps vs Databricks and risks

| Gap or risk | Impact | What this plan does about it |
| --- | --- | --- |
| DuckDB and DuckLake have no table grants, row filters or column masks | Anyone with the attach string sees everything, race and religion included | Cube is the only governed path; read-only catalog role for readers; mock data only, per the course rule |
| No native OpenMetadata connector for DuckDB or DuckLake | Catalog won't populate itself | `om_sync.py` pushes metadata through the SDK |
| Cube may not attach DuckLake directly | Semantic layer can't see gold | Publish a read-only `gold.duckdb` serving file |
| dbt-duckdb + DuckLake path untested here | Gold build could stall | Fall back to plain SQL assets in Dagster |
| DuckDB 2.0 is days old | Early bugs, storage format change | Stay on 1.5.x until 2.0.1; upgrade as Phase 7 |
| Single VM, single disk | One failure takes it all down | Nightly vzdump, ZFS snapshots, catalog dumps |
| OpenSearch memory | The most likely thing to OOM the VM | Run the governance profile only when needed if RAM is tight |
| No Genie equivalent | Natural-language queries depend on your MCP server | That's the point of the MCP experiment; route it through Cube, not raw SQL |

The first row matters most if this ever moves toward real data. At home with superhero records it's fine. At the agency, that gap is why enforcement stays in Unity Catalog.

## Open questions

- [x] Host specs: total cores, RAM, and whether the storage pool is ZFS or LVM-thin. This sets the 32 GB VM size. **Answered:** the host had room to spare; the VM runs at 12 vCPU and 47 GiB since October 28.
- [x] Does your existing Prometheus/Grafana run on this Proxmox host or another box? It decides whether Phase 6 adds scrape targets or a new stack. **Answered:** a new stack, in the VM's monitoring profile.
- [x] Should the home-lab MCP server live in this VM's Compose file, or stay separate and call Cube and OpenMetadata over the LAN? **Answered:** in the Compose file, calling Cube and OpenMetadata inside the VM.
- [x] PagerDuty for the home lab: a separate free account, or email-only alerts at home? **Answered:** neither; a self-hosted ntfy server pushes to the phone.
- [x] Fork under the `pugwala` account or a personal one? The course repo is public, so keep lakehouse secrets and `.env` out of it either way. **Answered:** `pugwala`, and since October 31 also `pugwala/homelake`, the lab's own copy.

## Sources

- [homelake repo](https://github.com/pugwala/homelake)
- [Announcing DuckDB 2.0.0 LTS](https://duckdb.org/2026/10/21/announcing-duckdb-200)
- [DuckLake FAQ](https://ducklake.select/faq.html) and [release calendar](https://ducklake.select/release_calendar.html)
- [MinIO archived: self-hosted alternatives](https://pinggy.io/amp/blog/minio_archived_self_hosted_s3_alternatives/) and [MinIO CE in 2026](https://glukhov.org/data-infrastructure/object-storage/minio-dead/)
- [Cube DuckDB data source](https://docs.cube.dev/docs/configuration/data-sources/duckdb) and [Cube data masking changelog](https://cube.dev/changelog/2026-03-20-changelog-data-masking)
- [OpenMetadata release notes](https://docs.open-metadata.org/v1.13.x/releases/all-releases)
- [OpenMetadata new connectors request](https://github.com/open-metadata/OpenMetadata/issues/26653) and [community DuckLake connector](https://github.com/surf-ori/openmetadata-ducklake-connector)
