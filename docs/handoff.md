> Snapshot of the live Claude Doc (https://claude.ai/artifact/2Ee11DTfMk8kLEoLtR7d3U), kept for safe keeping. Network addresses are redacted. The Claude Doc is the current copy.

# Home Lakehouse Handoff

Updated Nov 3, 2026 · @wrolfgar

Everything a new Claude session needs to pick up wrolfgar's home-lab DuckDB lakehouse: where it stands, how to reach it, what's built, and what not to break.

## Status right now

As of 2026-11-03, 06:50 CST. Phases 0 to 6 are built and running; Phase 7 (upgrades) waits on DuckDB 2.0.1. Phase 8, the expanded world the original plan didn't have, is complete and benchmarked: about 16.7M rows at scale M in the live lab, five data products in three domains, and L (65.6M rows) built and run end to end in a scratch lake of its own. On 2026-11-02 the course boundary was built. Course 1 is sessions 1 to 7. Course 2, the lakehouse, lands course 1's pinned, checked handoff and runs none of its code. Every table and column is now tagged automatically as data lands, and the MCP server has seven tools. Everything is reached over Tailscale at one name with a trusted certificate. The repo was anonymized on 2026-10-25 and 26 (record key `offender_number`). Since 2026-10-31 the lab also has its own repo, `pugwala/homelake`. Step-by-step detail is in the [Home Lakehouse Work Log](https://claude.ai/artifact/Pr3cjkiYEo6rnXKb95XuJd).

**Works, verified on the VM:**

- Proxmox VM 140 (`lakehouse`), Debian 13, LAN IP <vm-lan-ip>, Tailscale <tailnet-ip>. Claude Code runs on the VM as user `claude`, runs commands directly and explains each step.
- `/lake` is on the 200 GB data disk (ext4, `LABEL=lake`); root is 79 GB.
- Twenty-two services in the `core` profile: catalog-pg, jupyter, load-lake (one-shot), dagster-webserver, dagster-daemon, cube, superset, mcp, opensearch, om-migrate (one-shot), openmetadata-server, fuseki, prometheus, node-exporter, cadvisor, postgres-exporter, blackbox, pushgateway, catalog-backup, alertmanager, grafana, caddy. All twenty long-running ones are up; nineteen report healthy (Caddy has no healthcheck).
- The lake was wiped and rebuilt under `offender_number` after the scrub; `daily_lake` run a549b40d is green. The schedule runs it at 05:00 Central.
- Tests: parity 19, acceptance 59 (daily run 14, Cube 6, Superset 6, %sql 6, notebooks 9, MCP 13, anonymized 5), bootstrap bats 26, tie-back guard bats 5. `bootstrap.sh --check` passes.
- Tie-back guard: `tools/tieback_check.sh` runs as a pre-commit hook and as a GitHub Action; secret scanning and push protection are on.

**Not done yet:**

- DuckDB 2.0 + DuckLake 1.1 once 2.0.1 is out and two weeks old (Proxmox snapshot first).
- Two stale acceptance tests: VM RAM and the population headline.
- The leftover Fuseki scratch graph.
- A retry in `dashboards.py` for Superset's 429 rate limit.
- A recheck of GitHub code search.
- Clearing the pre-scrub session records (wrolfgar sees the list first).
- The harmless `grpcio-status` pip warning in the jupyter image.

The full list is the Work Log's "Up next". Settled since the last update: alerts go to self-hosted ntfy, and pushes now start GitHub Actions on their own.

## Next steps

Every step is test-first, logged in the Work Log, and committed only when wrolfgar asks. Every command says where it runs and as whom.

**Now. Phase 5, semantic + ontology: done 2026-10-26, pushed as 3255c15 on `duckdb-lakehouse`.** OpenMetadata 2.0.5 (with OpenSearch 2.19.6) runs at <tailnet-host> log in as `admin@open-metadata.org` with `OM_ADMIN_PASSWORD` from `.env` (read it in your own SSH session). `openmetadata/om_sync.py` pushes the Lakehouse glossary (typed relations), the Sensitivity tags (Restricted, Personal) and every lake table; the MCP server's `define_term` now reads OpenMetadata as the read-only `mcp-reader`. Cube masks the restricted columns (`***`) for every group but `restricted_reader`, and `cube/sync_masks.py` keeps those masks equal to OpenMetadata's `Sensitivity.Restricted` tags: tag a column in the UI, run `bootstrap.sh` (it restarts Cube when masks change), review `git diff lakehouse/cube/model/`, commit. The two optional extras are built too (next item).

**Now, part 2. Phase 5 extras: done 2026-10-26, pushed as 24fef43, 173686d, f8a3378 and 9735191.** The 05:00 `daily_lake` run now goes load → parity → gold → `openmetadata/lake` (om\_sync, plus a non-blocking WARN check that Cube's masks still match OpenMetadata's Restricted tags) → `fuseki/glossary`. Apache Jena Fuseki 6.2.0 (our own image from Apache's release, SHA-512 pinned, signature checked on every build) runs at <tailnet-host> reads open, writes need `writer` (`FUSEKI_WRITER_PASSWORD`), admin only inside the container. `openmetadata/om_to_rdf.py` publishes the glossary as SKOS plus every column's sensitivity and term as one named graph (715 triples); the README has a SPARQL example (restricted columns that hold part of an offender record: `stg_group`, `stg_status`). Also this session: `LAKE_RW_PASSWORD` and `OM_DB_PASSWORD` were rotated after I printed them via `docker compose config`; never print resolved compose config or container env.

**Now, part 3. Phase 6, monitoring: done 2026-10-26, pushed as seven commits, 01cf003 through 4277db0.** Home Lakehouse dashboard at <tailnet-host> (`admin` / `GRAFANA_ADMIN_PASSWORD`; read it in your own SSH session). Prometheus at /prometheus/ and Alertmanager at /alertmanager/, both behind the Dagster basic-auth login. Exporters for the VM, containers, catalog-pg and every site through Caddy; Dagster pushes job outcomes, load numbers and quality pass rates to the Pushgateway; 17 alert rules; nightly catalog backup at 02:00 Central to `/lake/catalog-backups` (uid 999, dumps mode 600, 14 days). Alerts go nowhere yet (receiver `undecided`): wrolfgar decides PagerDuty or email later. To test an alert, launch `monitoring_selftest` with `fail: true`, then `false`. README section "Monitoring and alerting" has the details and a restore recipe.

**Now, part 4. Phase 7 started 2026-10-26: every image pinned, pushed as a2bf4ff.** jupyter base `pyspark-notebook:2026-10-12` (was `latest`, rebuilt on a same-day base each time), `postgres:17.11-trixie`, `caddy:2.11.7`, and the lakehouse Python requirements with `==`. Pins live in `compose.yaml` defaults and Dockerfile `ARG`s, never in `.env`; `acceptance/test_pins.py` and `bootstrap.sh` both catch a floating tag. DuckDB 2.0 + DuckLake 1.1 waits for 2.0.1 to be out two weeks (2.0.0 shipped 2026-10-21); take a Proxmox snapshot first.

**Now, part 5. Data products, done 2026-10-27, pushed as 0bab8ff through 7a8e38d.** Two products in the Custody Operations domain, Custody Population and Custody Offenses, each one descriptor file in `lakehouse/products/` that every system is held to: dbt mart `mart_custody` (a record x month-end snapshot carrying the SID, enforced contracts), Cube views `custody_population`, `custody_offenses`, `custody_admissions`, OpenMetadata Domain, Data Products and Data Contracts (published by `om_sync.py`), DCAT datasets in Fuseki, and freshness and coverage alerts (`DataProductStale`, `DataProductCoverageLow`) with a Data products row on Home Lakehouse. People are counted as distinct SIDs, never summed: a Person glossary term (SID identifies Person, Offender Record isAbout Person) and `gold.dim_person` (no personal data). README "Data products" says how to add one; memory note `data-products` has the OpenMetadata 2.0.5 traps. Superset Custody dashboard (/superset/dashboard/custody/) on those views, pushed as 64b4d4c and 8bc899d on 2026-10-26: four charts whose metrics are Cube's own MEASURE(...), with "latest month-end" from Cube's is\_latest\_month\_end flag; superset/dashboards.py now holds one spec per dashboard in DASHBOARDS.

**Since then (2026-10-26/27):**

- **Pushed through 2026-10-27:** alerts to wrolfgar's iPhone through self-hosted ntfy; business rules in the ontology (rulebook, deductions, SHACL); data readiness per product month; and ops hardening (weekly DuckLake housekeeping, `lakehouse/ci/checks.sh`, a runbook per alert, nightly restic backups with restore drills).
- **Pushed 2026-10-28 to 11-03:**
  - CI live on GitHub (17 checks).
  - The expanded world, chunks 0 to 9: the universe generator, messy CSVs with answer keys, `world_bronze`/`world_silver`/`world_gold` monthly in Dagster, glossary and rules, three more data products.
  - The course boundary (Priorities 1 to 4).
  - Automatic tags (4b).
  - MCP tools `business_rules`, `data_product_info`, `data_quality` and `find_by_tags`.
  - Incident reports, the world's free text (Priority 5, 2026-11-03): 200,000 at M with a mention key (`mention_key/incident_report`) that says where every name, alias, SID, birth date and phone sits in the text. The approved model is complete.
  - The scale-up to L, benchmarked (chunk 10, 2026-11-03): `python -m lakehouse.universe.bench --scale L` builds a scale and runs it in a scratch DuckLake in `/lake/scratch/<scale>`, never the live lake. L (65.6M rows) builds in 164 s at a 27.6 GB peak, dbt in 44 s, queries under 0.3 s; the build's memory is the limit (`--workers 4` for less).
  - The docs snapshots in `homelake/docs` (2026-11-03), scrubbed for the public repo.
- **Waiting on wrolfgar:**
  - The go-ahead for chunk 11, the optional course sessions on the world (then course 2's own repo and the how-to doc).
  - A TrueNAS share, and `RESTIC_PASSWORD` kept off the VM (set aside 2026-11-01; backups go to a local folder until then).
- **Course:** `main` gained `notebooks/clearing-out-the-old.ipynb` and `DATA_VERSION` 6, after the rebuild left stale caches.

Details are in the Work Log.

**1. Phase 4, slice 3, `%sql` in Jupyter: done 2026-10-26, pushed as a9b8b1e.** `%load_ext lakehouse.sql_magic` connects jupysql to the lake read-only as `lake_ro`: the password goes through a temporary DuckDB secret, a SQLAlchemy engine attaches the lake on every connection, and a failed query is rolled back so the next one works. The Trust Test dashboard before it is pushed (4ff076b).

**2. Phase 4, MCP tools: done 2026-10-26, pushed as d132983, and connected from wrolfgar's Mac (Claude Code, user scope).** The `mcp` service serves `query_metric` (a Cube measure by name, through Cube's REST API) and `define_term` (from `lakehouse/glossary/glossary.yml`, 14 terms) at <tailnet-host> with `MCP_TOKEN` as a bearer token. To connect Claude Code on the Mac, without the token ever on screen: `claude mcp add --transport http --scope user lakehouse <tailnet-host> --header "Authorization: Bearer $(ssh lakehouse 'grep ^MCP_TOKEN= ~/lunch-and-learn-data-cleansing/lakehouse/.env | cut -d= -f2-')"`

**3. Phase 3 notebooks: done 2026-10-26, pushed as 2035849.** The seven course notebooks plus `lakehouse/08_from_lake.ipynb` run in the weekly `notebook_smoke` Dagster job: first run 1215d367, all 8 notebooks passed in 110 s, session 5 reconciled 22 of 22, session 6's F1 is 0.898. Session 7's model is staged on the lake disk at a pinned revision and the notebooks run offline. The spaCy OverflowError doesn't reproduce in the current image. **Course finding (fixed 2026-10-26, see the Work Log; few-shot now uses C=100 and beats the rules with either model):** with the real model (first time it ever ran), session 7's few-shot F1 is 0.750, below session 6's rules at 0.899, but the Facilitator Guide says few-shot scores highest. The guide was written from the fallback run. Course files are unchanged; that's wrolfgar's call.

Before any commit, the pre-commit hook runs `tools/tieback_check.sh`; run it by hand after editing anything that leaves the VM.

**4. Check health any time.** On the VM, as `claude`. It changes nothing, takes a few seconds, and lists anything wrong:

```bash
bash ~/lunch-and-learn-data-cleansing/lakehouse/scripts/bootstrap.sh --check
```

After a `daily_lake` run, the acceptance test confirms the run did its job:

```bash
cd ~/lunch-and-learn-data-cleansing/lakehouse && docker compose --profile core exec -T jupyter pytest -q lakehouse/acceptance
```

## Environment and access

Claude Code runs on the VM itself, as user `claude`, so Claude runs commands directly, explains each step, and asks before anything irreversible. wrolfgar can follow along in the terminal and still runs anything that needs the Proxmox host or his Mac.

| Item | Value |
| --- | --- |
| Proxmox host | `https://<proxmox-host-ip>:8006`; storage pool assumed `local-zfs` (not confirmed) |
| VM | ID 140, name `lakehouse`, Debian 13 "trixie" genericcloud image, cloud-init, 8 vCPU (`host` type), 32 GB RAM, ballooning off, QEMU guest agent working |
| VM IP | <vm-lan-ip> static via cloud-init (confirmed on the VM, 2026-10-25) |
| OS disk | scsi0, 80 GB; root partition grown to 79 GB with `growpart` + `resize2fs`. Stable name `/dev/disk/by-id/scsi-0QEMU_QEMU_HARDDISK_drive-scsi0` |
| Data disk | scsi1, 200 GB, ext4 on the whole disk, `LABEL=lake`, mounted at `/lake` (fstab, by label, `nofail`). Formatted 2026-10-25: it had never been formatted before. Stable name `/dev/disk/by-id/scsi-0QEMU_QEMU_HARDDISK_drive-scsi1` |
| `/lake` layout | `landing`, `data` (DuckLake Parquet), `notebook-runs`, `catalog-backups`, `models`, `dagster` (owned 1000:100) |
| Linux user | `claude`, uid **1001**, SSH key from wrolfgar's Mac, in the `docker` group, passwordless sudo. Both stay permanently (wrolfgar's decision); use them carefully |
| Container user | `jovyan`, uid **1000**. The repo has ACLs granting 1000 and 1001 rwX (`setfacl`, plus defaults) |
| Repo on VM | `~/lunch-and-learn-data-cleansing`, branch `duckdb-lakehouse`; `.env` in `lakehouse/` (mode 600, never committed) |
| wrolfgar's Mac | Apple Silicon, on the tailnet. Opens <tailnet-host> and `/dagster/` with a real certificate (no hosts entries, no warnings). `ssh lakehouse` via `~/.ssh/config` (<tailnet-ip>, user `claude`) |
| Exposure | LAN and wrolfgar's tailnet (VM at <tailnet-ip>, `<tailnet-host>`). Caddy on 80/443 serves only the Tailscale name; the `*.lake.home.arpa` names were retired 2026-10-25. Postgres bound to 127.0.0.1; Cube on the Docker network only; nothing port-forwarded |

Tools on the VM: `gh` (signed in as `pugwala`, used for pushes), `bats`, `shellcheck`, `tmux`, Node.js 20 and claude-mem (local only: Anthropic-plan provider, no cloud sync, telemetry off). Never ask for passwords or tokens in chat. Secrets are generated on the VM (`openssl rand -hex 24`, or by `bootstrap.sh`) or typed by wrolfgar into `.env`, and only ever shown as names or fingerprints.

## Repo and branch

All lakehouse work lives on the `duckdb-lakehouse` branch of [pugwala/homelake](https://github.com/pugwala/homelake/tree/duckdb-lakehouse), in a `lakehouse/` folder. The repo is wrolfgar's public Data Cleansing course, which runs on Databricks.

**Hard rule:** never change the course. On the branch, `lnl/`, `notebooks/`, `generator/` and `requirements.txt` must stay byte-identical to `main`; check with `git diff origin/main -- lnl notebooks generator requirements.txt`, which should print nothing. The lakehouse imports from the course, never the other way round. Outside `lakehouse/`, the branch adds only the root `.gitignore`. Nothing in the repo may tie back to wrolfgar's employer (see the standing rules under Working with wrolfgar).

**History.** On 2026-10-26 the repo was rebuilt as fresh history: the old repo, which had the old record-key name in every commit, was deleted, and the new one was renamed into its place, public, with secret scanning and push protection on. Each branch started as one commit: `main` 677eb0e (the course and the tie-back guard) and `duckdb-lakehouse` 54e0f0e (adds `lakehouse/` and `.gitignore`). Commit SHAs in older Work Log entries no longer exist on GitHub. The only copy of the old content is the mirror `~/lnl-backup.git` on the VM, kept at wrolfgar's request; never push it anywhere. Since then, duckdb-lakehouse has 4ff076b (the Trust Test dashboard), a9b8b1e (%sql in Jupyter), 2035849 (Phase 3: notebooks, model staging, notebook\_smoke; renames sql.py to sql\_magic.py), 73197bc (merge of main's c536880, the session 7 few-shot fix), 58d4372 (tests for it), d132983 (the MCP server), 3255c15 (Phase 5: OpenMetadata, Cube masking, the tags-to-masks loop), and the Phase 5 extras one chunk per commit: 24fef43 (daily om\_sync), 173686d (Fuseki), f8a3378 (glossary as RDF), 9735191 (daily Fuseki refresh, docs), then Phase 6 one chunk per commit: 01cf003, 6a33b28, 1685cd7, deb6c03, a4efa3a, fc31d04, 4277db0 (monitoring), then a2bf4ff (Phase 7: every image pinned), 2fe874e (Python packages as of the cutoff), e54794d (docstrings) and d5fdd87 (merge of main's c5ce083, the guard workflow comment). main is at c5ce083.

Layout of `lakehouse/`:

| Path | Purpose |
| --- | --- |
| `compose.yaml` | `core` profile: catalog-pg, jupyter, load-lake (one-shot), dagster-webserver, dagster-daemon, cube, superset, mcp, opensearch, om-migrate (one-shot), openmetadata-server, fuseki, caddy |
| `.env.example` | Every setting and secret name |
| `lake.py`, `load_lake.py` | DuckLake helpers and the loader CLI (prints JSON metrics on its last line) |
| `tests/test_parity.py` | 18 checks against the Facilitator Guide's numbers; the blocking step in `daily_lake` |
| `tests/bootstrap.bats` | 51 bats tests for `bootstrap.sh`, run against stub commands so they never touch the live stack |
| `acceptance/` | 179 checks run by hand (pins 24 more, besides) (`pytest lakehouse/acceptance` in jupyter): monitoring 22, daily run 17, Cube 15, MCP 13, om\_sync 12, glossary RDF 10, notebooks 9, OpenMetadata 8, pipeline metrics 8, alerting 7, Fuseki 7, Superset 6, `%sql` 6, backup 6, anonymized 5, masks 4. Kept out of `tests/` because the parity step runs that whole folder mid-run |
| `dbt/` | Gold models, sources, tests, `profiles.yml` with lake (DuckLake) and local (DuckDB file) targets chosen by `DBT_TARGET` |
| `orchestration/` | `definitions.py` (Dagster assets, jobs, schedule) and `dagster.yaml` (Postgres storage, one run at a time) |
| `postgres/init/` | `01-roles.sh`, `02-dagster.sh`, `03-superset.sh`, `04-openmetadata.sh`: idempotent roles and databases |
| `jupyter/` | Dockerfile and pinned `requirements-lake.txt`; one image runs Jupyter, the loader and Dagster |
| `cube/` | `cube.js` (attaches the lake `READ_ONLY` as `lake_ro`; `contextToGroups`), `model/` (offender\_records with restricted columns masked, dq\_scorecard, trust\_test; no personal columns) and `sync_masks.py` (masks follow OpenMetadata's Restricted tags) |
| `superset/` | Dockerfile (apache/superset 6.1.0 plus psycopg2), `superset_config.py`, `start.sh` (registers Cube as a database) |
| `caddy/Caddyfile` | Serves only the Tailscale name, with a Tailscale certificate: `/jupyter`, `/dagster` (basic auth), `/superset`, `/mcp`, `/openmetadata`, `/fuseki`, `/grafana`, `/prometheus` and `/alertmanager` (both basic auth) |
| `scripts/` | `bootstrap.sh` (set up, upgrade or check; safe to re-run; never formats a disk) and `set-dagster-ui-password.sh` |
| `README.md` | Setup, upgrade path, test status |
| `sql_magic.py` | %load\_ext lakehouse.sql\_magic: jupysql's %sql on the lake, read-only as lake\_ro (lake.attach\_lake\_ro does the attach) |
| `openmetadata/` | setup\_admin.py (replaces the default admin password, creates the read-only mcp-reader), om\_sync.py (glossary, Sensitivity tags, every lake table; --check compares only) and om\_to\_rdf.py (that meaning as one RDF graph in Fuseki) |
| `mcp/` | The MCP server (mcp 2.3.0): query\_metric over Cube's REST API, define\_term over OpenMetadata as mcp-reader |
| `glossary/glossary.yml` | The 14-term glossary with typed relations; om\_sync.py loads it into OpenMetadata, which is what define\_term reads |
| `fuseki/` | Dockerfile (Apache's Fuseki 6.2.0 release, SHA-512 pinned, GPG-checked), config.ttl (dataset lakehouse; writes need writer), shiro.ini (no users; admin localhost-only), start.sh (password file on a tmpfs) |
| `monitoring/` | prometheus/ (config, sites.yml probe targets with a placeholder host, fill-targets.sh, start.sh, rules/lakehouse.yml), alertmanager/ (the undecided receiver), blackbox/ (the site module), grafana/ (provisioning, the Home Lakehouse dashboard JSON, set\_home.py) |
| `backup/backup.sh` | The nightly catalog backup run by catalog-backup: pg\_dump of every app database, read back with pg\_restore --list, manifest, 14 days, textfile metrics |
| `metrics.py` | push(): Dagster's job outcomes, load numbers and quality pass rates to the Pushgateway; never fails a run |

At the repo root, on both branches: `tools/tieback_check.sh` (the guard; its banned list is written with bracketed letters so the file itself stays clean), `tools/tieback_check.bats` (5 tests), `.githooks/pre-commit` (enabled on the VM with `git config core.hooksPath .githooks`) and `.github/workflows/tieback-check.yml`.

The course's own README says its notebooks were tested locally with pandas 3.0 and PySpark 4.2. Outside Databricks, `lnl/env.py` writes data to `LNL_DATA_DIR` and session 5 saves Parquet instead of Delta, so the notebooks run unmodified in the lakehouse's Jupyter.

## What's built

The course generator feeds bronze. The course's own pandas cleansing (`clean_through(4)` equivalent) produces silver. dbt builds gold. Dagster runs it daily. Silver reuses the course code on purpose, so the lake and the class always agree on every value.

**Tables (DuckLake, attached as `lake`):**

| Table | Contents |
| --- | --- |
| `ref.*` | Six crosswalks from `lnl/reference/` (all VARCHAR), plus `ref.null_tokens` built from `lnl.cleaning.NULL_TOKENS` |
| `bronze.hero_offenders_raw` | Generator CSV as written, all VARCHAR, plus `_run_id`, `_ingested_at`, `_source_file`, `_seed`, `_data_version` |
| `bronze.conduct_notes_answer_key` | Answer key as written |
| `silver.hero_offenders` | Typed: BIGINT `offender_number`/`sid_number`, DATE, TIME, DECIMAL(12,2), BOOLEAN. Ordered codes (`custody_level`, `threat_level`, `violence_code_std`) are VARCHAR plus a `_rank` column, because DuckLake has no ENUM |
| `silver.hero_offenders_exceptions` | One row per flagged value. Rules: `domain_unmapped`, `conversion_failed`, `dob_check`, `offense_violence_conflict`. Records are flagged, never dropped (wrolfgar's course rule) |
| `silver.conduct_notes_answer_key` | BIGINT key, joins to silver |
| `gold.dim_unit`, `dim_offense`, `dim_stg_group` | From reference data. The STG group `None` means no recorded affiliation (`is_affiliation = false`) |
| `gold.fct_offender_record` | One row per record: keys, codes, measures, `exception_count`. Excludes names, aliases, notes and DOB. Race, religion and STG columns carry `meta.sensitivity: restricted` |
| `gold.dq_scorecard` | Per dimension × column × rule: completeness, conformity, validity, consistency, uniqueness, timeliness. Accuracy isn't scored (no ground truth). "Missing" means null, whitespace (tabs included) or a documented unknown code |
| `ops.load_runs` | One row per load: counts, seconds, data snapshot ID |

**One load = three DuckLake snapshots:** the data, then table comments, then the `ops` row. Comments run outside the data transaction, because one failed statement aborts a whole DuckDB transaction.

**The daily run** (`daily_lake`, 05:00 America/Chicago, schedule on by default) runs `load_lake` → the blocking parity check `matches_course_numbers` (runs the 18 pytest checks) → `dbt build`.

- If the parity check fails, the run fails and gold isn't rebuilt. Silver has already been written; DuckLake time travel can restore the previous version. Claude tested this deliberately in the sandbox.
- dbt tests at `error` severity fail the run: keys, the silver-equals-gold row count, accepted values, score ranges.
- `warn` tests only record: reference relationships, and `dq_score_floor`, which fires today on `disciplinary_points` completeness at 94.15%.
- `regenerate_lake` does the same, but rebuilds the CSV from the seed first.
- The run coordinator allows one run at a time, so DuckLake writers never race.

**Connection details.** `LAKE_CATALOG=ducklake:postgres:dbname=ducklake host=catalog-pg user=lake_rw`, with the password from `PGPASSWORD` and `LAKE_DATA_PATH=/lake/data/`. `lakehouse.lake.lake_connect(read_only=True)` attaches it and runs `USE lake`. With a plain file path in `LAKE_CATALOG`, the same code runs against a DuckDB file, which is how the sandbox tests work.

**Query layer (Phase 4, masking from Phase 5).** Cube v1.8.3 attaches the lake read-only as `lake_ro` through `initSql` and exposes a model over gold. Personal columns never reach it; the restricted ones (race, religion, STG) are in the model but masked (`***`) for every group except `restricted_reader` (a token's `groups` claim, mapped by `contextToGroups` in `cube.js`), and which columns count as restricted is decided by OpenMetadata's `Sensitivity.Restricted` tags through `cube/sync_masks.py`. Its SQL API listens on 15432 on the Docker network only. Superset 6.1.0 registers Cube as a Postgres database, so Superset users see only Cube's model, never the lake.

**Plan document:** [DuckDB Home Lakehouse Plan](https://claude.ai/artifact/Js8ovfd7HE7BJ5Sj6TS3Sj) has the target architecture diagram and all seven phases in detail.

## Phase tracker

The phases match the plan document.

| Phase | Status | Done | Left |
| --- | --- | --- | --- |
| 0 Proxmox build | Done | VM, Debian 13, Docker, ACLs; data disk at `/lake`, root 79 GB; snapshot `core-plus-dagster` before Phase 4 and another before the lake rebuild | Nothing |
| 1 Platform services | Done | Twenty services with their own healthchecks; secrets in `.env` (mode 600, hidden from containers); `bootstrap.sh` sets up and checks it all; Tailscale name with a trusted certificate | Nothing |
| 2 Generator + medallion | Done | Bronze, silver and gold on DuckLake, keyed by `offender_number`; `daily_lake` green (a549b40d); parity and acceptance tests pass | Optional: port the course's 22 Spark-vs-pandas reconciliation metrics |
| 3 Notebooks | Done | Jupyter at `/jupyter/`; all 7 course notebooks run unmodified, session 7 on the real model staged offline in `/lake/models`; `lakehouse/08_from_lake.ipynb`; weekly `notebook_smoke` job | Nothing |
| 4 Query layer | Done | Cube over gold, read-only as `lake_ro`; Superset on Cube at `/superset/`; the Trust Test dashboard; %sql in Jupyter, read-only as lake\_ro; MCP server with query\_metric and define\_term; 31 acceptance tests | Nothing (the glossary moved into OpenMetadata in Phase 5) |
| 5 Semantic + ontology | Done 2026-10-26, pushed as 3255c15 | OpenMetadata 2.0.5 + OpenSearch at `/openmetadata/`, no default credentials left; `om_sync.py` (glossary with typed relations, Sensitivity tags, every lake table), daily in `daily_lake`; `define_term` reads OpenMetadata; Cube masks restricted columns except for `restricted_reader`; `sync_masks.py` makes the masks follow OpenMetadata's tags; Fuseki 6.2.0 at `/fuseki/` with the glossary and column tags as SKOS, refreshed daily | Nothing |
| 6 Monitoring | Built 2026-10-26, uncommitted | Prometheus 3.15.0, node-exporter, cAdvisor, postgres-exporter, blackbox through Caddy, Pushgateway with Dagster sensors and data-quality metrics, Alertmanager 0.34.1 with 17 rules, Grafana 13.2.3 with the Home Lakehouse dashboard, nightly catalog backup with a restore drill; 43 new acceptance tests (155 in all), 12 new bats (49) | Pick an alert destination (PagerDuty, email or both) and add it to the `undecided` receiver |
| 7 Upgrades | Not started | DuckDB pinned at 1.5.6 (Cube bundles 1.5.5, the one accepted exception) | DuckDB 2.0 + DuckLake 1.1 after 2.0.1 ships (take a vzdump first; 2.0 files can't be read by older DuckDB); optional k3s |

## Decisions and why

These were settled with wrolfgar. Don't reopen them without a reason he'd care about.

| Decision | Why |
| --- | --- |
| DuckLake 1.0 (Postgres catalog, Parquet on local disk), not a single .duckdb file | A plain DuckDB file allows one writer. Jupyter, Dagster, Cube and Superset all need it at once. DuckLake adds snapshots and time travel |
| DuckDB pinned to 1.5.6 everywhere | DuckDB 2.0.0 LTS shipped 2026-10-21 with client-server mode and DuckLake 1.1. Its storage format can't be read by older versions. Wait for 2.0.1 (due November) and upgrade every container at once. Cube's bundled 1.5.5 is the one accepted exception; Cube only reads |
| One Docker image for Jupyter, the loader and Dagster | DuckDB extension versions must match DuckDB everywhere. One image guarantees it |
| No MinIO; Parquet on local disk | MinIO's repo was archived April 2026, and community images stopped in October 2025. If S3 semantics are ever wanted, use Garage or SeaweedFS |
| Docker Compose, not Kubernetes | One node gains nothing from k3s yet. k3s is an optional Phase 7 exercise |
| Silver comes from the course's own pandas code | The lake and the class must agree on every value. Rewriting the rules in SQL would drift |
| Exceptions are flagged, never dropped | The course's "flag, don't fix" rule. A quarantine table was in the original plan and was replaced for this reason |
| Parity tests are the contract | 18 checks pin the lake to the Facilitator Guide. A failure blocks gold |
| dbt test severities mirror the course's enterprise track | error = stop (like a Lakeflow expect\_or\_fail), warn = record (like expect) |
| Cube = semantic layer; OpenMetadata = ontology layer | The same split wrolfgar uses at work: Unity Catalog metric views ↔ Cube; UC governed tags, Domains, Pages ↔ OpenMetadata classifications, domains, glossary. OpenMetadata authors meaning; Cube enforces it (masks) |
| Cube is the only governed query path | DuckDB/DuckLake have no grants, row filters or masks. Engineering attaches directly; everyone else goes through Cube |
| Superset reads through Cube | Superset connects to Cube's SQL API as a Postgres database, so it only ever sees Cube's governed model |
| Gold excludes names, aliases, notes and DOB | Reporting needs keys, codes and measures. Sensitive codes stay, but are tagged for masking |
| Dagster UI behind Caddy basic auth | Dagster OSS has no login |
| Tailscale only, with a Tailscale certificate | Caddy serves only the MagicDNS name, with a certificate from tailscaled; nothing is port-forwarded or on the internet. The \*.lake.home.arpa names and Caddy's internal CA were retired 2026-10-25 |
| One name, paths not subdomains | `/jupyter/`, `/dagster/` and `/superset/` share one MagicDNS name and one certificate; each app runs with its base path set |
| Fresh history, public repo, tie-back guard | The old history carried the employer's identifiers in every commit, and a rewrite would leave traces on GitHub, so a new repo with two commits replaced it. The guard keeps it clean |
| Mock data only | The course's rule: nothing here may ever touch real offender data |

## Gotchas already hit

| Gotcha | What happened | Rule now |
| --- | --- | --- |
| Disk names swap between boots | `sda`/`sdb` traded places after a reboot. A `growpart` aimed at the data disk failed harmlessly | Identify disks by size, label or mountpoint. fstab uses `LABEL=lake` |
| uid mismatch | `claude` is 1001, the container user is 1000. The container couldn't write the repo (pytest cache; notebook saves would also fail) | ACLs on the repo for both uids. `/lake` dirs are owned 1000:100 |
| CUDA PyTorch | sentence-transformers pulled about 5 GB of NVIDIA libraries and filled the 40 GB OS disk on rebuild | CPU torch from `download.pytorch.org/whl/cpu` installed first. Pip layers split |
| Postgres init runs once | `postgres/init/` only runs on an empty volume. Adding the dagster role needed a manual `exec` | New roles get an idempotent script plus a manual run on existing installs |
| Compose `:?` checks | Missing `.env` keys stop `up` before anything starts. Useful, but a half-finished upgrade looks like "nothing happened" | Check `docker compose ps` CREATED times after an upgrade |
| DuckDB transactions | One failed statement aborts the transaction | Cosmetic writes (comments) go in their own transaction |
| DuckDB prepared parameters | Views can't take `?` parameters | `_lit()` quotes literals for view SQL |
| SQL `trim()` | Only strips spaces, so tab-only blanks counted as present | Use `regexp_full_match(x, '\s*')`. In dbt files, write the backslash once |
| UNPIVOT in a CTE | The simplified `UNPIVOT x ON ...` syntax fails inside a CTE | Use `SELECT * FROM x UNPIVOT INCLUDE NULLS (v FOR name IN (COLUMNS(*)))` |
| `qm` in the wrong shell | wrolfgar ran `qm` inside the VM | `qm` and `pvesm` run as root in the Proxmox host's web Shell |
| Static unit message | `qemu-guest-agent` "is a static unit" is normal; udev starts it | Verify with `qm agent 140 ping` on the host |
| Cloud-init SSH key | "SSH public key validation error" came from a pasted or wrapped key | `scp` the `.pub` to the host, check with `ssh-keygen -l -f` |
| Data disk never formatted | fstab's nofail let every boot skip a disk with no lake label, so /lake was a plain folder on the OS disk | bootstrap.sh stops unless /lake is a mounted disk. Check with findmnt /lake |
| Unpinned SQLAlchemy | pip took 2.1, which maps postgresql:// to the psycopg 3 driver; Dagster crash-looped on a missing module | Pin transitive dependencies in requirements-lake.txt, with a comment saying why |
| dbt reads .env | dbt 1.12 auto-loads any .env above its working folder; it hit PermissionError on the mode-600 file | compose.yaml mounts /dev/null over lakehouse/.env. Never loosen .env to fix this |
| Inherited healthcheck | Dagster containers ran the Jupyter image's check and always showed unhealthy, though Dagster was fine | Every service has its own healthcheck in compose.yaml |
| Bare up -d runs the loader | --profile core up -d with no service names also starts the one-shot load-lake | Name the seven long-running services, or use bootstrap.sh |
| sed -i on .env | It writes a new file, which inherits the repo's default ACL, so the container user could read every secret | After any edit: setfacl -b .env && chmod 600 .env (bootstrap.sh and the password script do this) |
| Duplicate .env keys | The old README upgrade step appended DAGSTER\_PG\_PASSWORD with >>, so running it twice left two different values | bootstrap.sh refuses duplicate keys and only fills missing secrets |
| bats ! lines | A bats line starting with ! never fails a test; only the last line counts | Use a helper function (not\_called); lint .bats files with shellcheck -s bash |
| Caddy and <tailnet-host> names | Caddy didn't recognize the Tailscale name and tried Let's Encrypt | tls { get\_certificate tailscale } in the Caddyfile, with tailscaled.sock mounted into the container |
| Single-file bind mounts | An edited Caddyfile on the host left the container reading the old file (editors write a new inode) | Mount folders (./caddy, ./superset), never single files |
| Superset 6 database URI | The URI is no longer on the database detail endpoint | Read it from /api/v1/database/\<id>/connection |
| claude-mem logs tool inputs | Any banned word typed into a command lands in claude-mem's database and logs | Build words from fragments or use bracketed regexes; in SQL concatenate with \|\| (a doubled quote inside a SQL string is an escaped quote, not a split) |
| Workflow pushes | Pushing .github/workflows was rejected without gh's workflow scope, and pushes to the new repo didn't trigger the Action | gh auth refresh -s workflow; run the check by hand with workflow\_dispatch |
| Plugin auto-update | The plugin marketplace moved claude-mem from the pinned 15.0.2 to 15.2.1 on its own | Check \~/.claude/plugins/installed\_plugins.json and the worker's /api/health version after restarts |
| claude-mem installer phones home | Every npx claude-mem install POSTs the hostname, install state and per-day observation and token counts to cmem.ai to make a sign-in link; CLAUDE\_MEM\_ONLINE\_OPTIN=false doesn't stop it | Prefix any future install with CMEM\_PRO\_ORIGIN=http://127.0.0.1:9, and ignore the link it prints |
| A module named sql.py | From a notebook in lakehouse/, lakehouse/sql.py hid jupysql's own sql package, so %load\_ext sql loaded itself forever (RecursionError) | Renamed to sql\_magic.py; a test imports both from inside lakehouse/ |
| jupysql error messages | Any failing query containing :: gets a named-parameters hint that hides the real DuckDB error | Follow the exception's \_\_cause\_\_ chain to the root error before believing the hint |
| Notebook settings per service | PYTHONPATH and LAKE\_RO\_PASSWORD were set for Jupyter only, so 08\_from\_lake failed when Dagster ran it | Anything a notebook needs goes in the shared lake-env in compose.yaml; a test checks all three services |
| Hugging Face cache in the container | Session 7's model downloaded into \~/.cache, lost whenever the container is recreated | HF\_HOME on /lake/models, HF\_HUB\_OFFLINE=1, staged by bootstrap.sh at a pinned revision (88 MB, not the 1 GB repo) |
| MCP Python SDK 2.x | FastMCP is now MCPServer; tools returning dict gave no structured content; ordinary exceptions reached the client only as "Error executing tool X" | Return Pydantic models, raise ToolError for messages the caller should see; check a 2.x API in a throwaway container before coding against it |
| Cube mask in YAML | mask: "\*\*\*" compiles to null, so masked columns come back empty | Write it as SQL: mask: {sql: "'\*\*\*'"}; restart cube after any model change (dev mode is off) |
| OpenMetadata passwords | changePassword fails the policy check; login fails | Login takes the password base64-encoded, changePassword takes it plain; the policy wants upper, lower, digit and special |
| OpenMetadata sync drift | om\_sync --check never settles | Descriptions come back HTML-escaped (unescape before comparing); glossary tags propagate to columns as Derived and steward tags survive PUT, so compare only the tags the repo wants |
| Writing the repo from jupyter | Permission denied, even reading a script, when exec runs as another uid | /home/jovyan is 770 jovyan:users: use exec -u "$(id -u):users" |
| Dagster after catalog-pg is recreated | GraphQL answers 500 for a few calls | Stale pooled connections; it recovers on its own, or restart dagster-webserver and dagster-daemon |
| docker compose config | Its output resolves .env, so secrets land in the transcript | Read compose.yaml source instead; compare secrets by hash or cmp and print only yes/no. Two passwords were rotated over this on 2026-10-26 |
| Fuseki UI build | Crash: Fuseki base is not writable: /run; a default shiro.ini with sample user1/passwd1 appears | start.sh sets FUSEKI\_BASE on the tmpfs and installs our user-less shiro.ini first; the version is at /fuseki/$/server (no Server header) |
| curl to the VM's own Tailscale name | Fails from the VM itself (accept-dns is off) | Add --resolve \<name>:443:127.0.0.1, as bootstrap.sh does |
| Dagster after catalog-pg is recreated (again) | GraphQL 500s for a while; tests that launch runs fail | bootstrap.sh now restarts Dagster when it recreates catalog-pg; after any other recreation, restart dagster-webserver and dagster-daemon by hand |
| Prometheus or Alertmanager config edits | Neither rereads its config on its own | bootstrap.sh refills the probe targets and sends SIGHUP to both on every run (no restart, no gap) |
| Grafana home dashboard | GF\_DASHBOARDS\_DEFAULT\_HOME\_DASHBOARD\_PATH loads a hidden second copy (uid default-home-dashboard) | Set the org preference homeDashboardUID instead (monitoring/grafana/set\_home.py) |
| Catalog backups | Permission denied reading a dump, or the first backup failing on a root-owned folder | By design: uid 999 owns /lake/catalog-backups and dumps are mode 600 (they hold password hashes); read with sudo; bootstrap chowns the folder to 999 |

**Not yet proven, likely to bite:**

- OpenMetadata has no DuckDB/DuckLake connector. Plan: `om_sync.py` on the ingestion SDK. The community DuckLake connector is a sketch.
- OpenMetadata's reverse-metadata push to Databricks is Collate-only. That matters at work, not in the home lab.
- `set-dagster-ui-password.sh` passes the password to `caddy hash-password --plaintext`. Fine at home, but it's briefly visible in the process list.
- GitHub code search hadn't indexed the new repo on 2026-10-26 (a search for `offender_number` found nothing), so an empty search there proves nothing yet. Recheck before relying on it.

## Reference numbers

With the default 100,000 rows and seed 2026, the lake must reproduce these exactly. They come from `FACILITATOR_GUIDE.md` and are enforced by `lakehouse/tests/test_parity.py`.

| Check | Expected |
| --- | --- |
| Bronze and silver rows; distinct `offender_number` | 100,000 each; `offender_number` is BIGINT |
| Unmapped coded values (total 1,966) | offense 1,379 · unit 266 · violence 104 · religion 86 · STG 77 · race 54 |
| Failed conversions (total 1,086) | points 206 · money 183 · time 185 · escape risk 220 · protective custody 0 · dampener 292 |
| Offense/violence conflicts | 228 |
| Birth dates flagged | 8 |
| Restitution total | 1,333,587,950.77, to the cent |
| Confirmed STG records | 3,612 |
| Exceptions table | 3,288 rows on 3,249 records |

Gold scorecard in the sandbox, as overall pass rate per dimension: completeness 96.89% · conformity 99.79% · consistency 99.81% · validity 99.99% · uniqueness 100% · timeliness 100%. The lowest single rule is `disciplinary_points` completeness at 94.15%, which trips the 95% warning floor. 26 dbt tests: 25 pass, 1 warns.

## Working with wrolfgar

wrolfgar is a public-sector data architect. This lab is self-education. It mirrors the stack wrolfgar uses at work (Databricks, Unity Catalog, metric views, OpenMetadata) and the Data Cleansing course with open-source parts.

- **Say exactly where and as whom.** Every command block should name the machine (Proxmox host web Shell as root, the VM as `claude`, or the Mac) and say whether it needs `sudo`. He asked twice; mixing these up caused two detours.
- **One step at a time, with the expected output.** He runs the commands and pastes the output back. Give what success looks like and what to paste if it fails.
- **Stop before anything irreversible.** Formatting disks, deleting data, the DuckDB 2.0 upgrade.
- **Direct, no filler, real recommendations.** Push back when an idea has a problem. Don't hedge with "it depends"; pick and explain.
- **Standards.** Industry-standard tools unless an emerging one has a critical advantage. Docker or Kubernetes based. Everything monitored: Prometheus/Grafana, alerts to PagerDuty (ServiceNow and another ticketing system at work).
- **Docs.** Conversational and professional, written for technical and non-technical readers alike.
- **Schedule.** The pipeline runs at 05:00 Central so results are ready by morning.
- **Secrets.** Never ask for passwords, tokens or keys in chat.

**Standing rules wrolfgar set on 2026-10-25.** Every session follows these; they are also in Claude's project memory.

- **Teach as you go.** Explain each step: what, why, the command, and what the output means.
- **Log and remember.** Every step goes into the [Home Lakehouse Work Log](https://claude.ai/artifact/Pr3cjkiYEo6rnXKb95XuJd), newest first, and into memory.
- **Test first, red then green.** Write the test, show it failing for the right reason, make it pass, commit the test with the change. Tests added to existing code are proven by breaking the code and watching them fail.
- **Every function has a docstring.** In bash, a one-line comment directly above the function.
- **GitHub only ever sees `pugwala`.** Author and committer `pugwala <36488669+pugwala@users.noreply.github.com>`; never wrolfgar's real name in commits, messages or PRs. Commit and push only when wrolfgar asks.
- **Sudo stays; be careful.** `claude` keeps passwordless sudo and the `docker` group. Read before changing, use stable disk names, and ask before anything irreversible.
- **No employer tie-backs.** Never write the employer's name or abbreviation, the old record-key name, or the real unit names anywhere: code, docs, commits, memory or claude-mem notes. The record key is `offender_number`, the agency is "the Department", units are fictional cities. `tools/tieback_check.sh` holds the list and must pass before every commit.
- **No Tailscale URLs on GitHub.** They're fine in private docs like this one.
- **Times in Central.** Report times as CDT (CST after 2026-11-01), not UTC.

## Open questions

- [ ] Is the Proxmox storage pool local-zfs?
- [ ] Proxmox host total cores and RAM: can the VM keep 32 GB once OpenSearch arrives?
- [x] Does wrolfgar's existing Prometheus/Grafana run on this Proxmox host or elsewhere? This decides whether phase 6 adds scrape targets or a new stack.

  Answered 2026-10-26: a new monitoring stack on this VM (Prometheus, Grafana, Alertmanager, Pushgateway, exporters), in the `core` profile.
- [x] Should the home-lab MCP server live in this Compose stack? Decided 2026-10-26: yes, as the mcp service, new rather than an older experiment.
- [ ] PagerDuty for the home lab: a separate free account, or email-only alerts?

  2026-10-26: decide later. Alertmanager routes to a placeholder receiver until wrolfgar picks; alerts show in Alertmanager and Grafana meanwhile.
- [x] Pin claude-mem back to 15.0.2? Done 2026-10-26: back on 15.0.2 with marketplace auto-update off (no schema change made it safe)
- [ ] Clear Claude Code's local session records (history.jsonl, file-history, paste-cache) that still hold pre-scrub text, once the scrub session has ended?

## Links

- Repo branch: [pugwala/homelake @ duckdb-lakehouse](https://github.com/pugwala/homelake/tree/duckdb-lakehouse). Start with `lakehouse/README.md`
- Plan with architecture diagram: [DuckDB Home Lakehouse Plan](https://claude.ai/artifact/Js8ovfd7HE7BJ5Sj6TS3Sj)
- [Announcing DuckDB 2.0.0 LTS](https://duckdb.org/2026/10/21/announcing-duckdb-200)
- [DuckLake FAQ](https://ducklake.select/faq.html) and [release calendar](https://ducklake.select/release_calendar.html)
- [Cube DuckDB data source](https://docs.cube.dev/docs/configuration/data-sources/duckdb) and [Cube data masking](https://cube.dev/changelog/2026-03-20-changelog-data-masking)
- [OpenMetadata release notes](https://docs.open-metadata.org/v1.13.x/releases/all-releases)
- [Debian trixie release information](https://debian.org/releases/stable/index.en.html) and [Docker Engine on Debian](https://docs.docker.com/engine/install/debian/)
- Day-by-day record: [Home Lakehouse Work Log](https://claude.ai/artifact/Pr3cjkiYEo6rnXKb95XuJd)
- Lakehouse over Tailscale (private; never on GitHub): [Jupyter](<tailnet-host>), [Dagster](<tailnet-host>), [Superset](<tailnet-host>)
- Course materials: [course site](https://claude.ai/artifact/7f591mfAiF8hsTHcGYoCZK), [slides](https://claude.ai/artifact/1pGTjUSVQPxmnFqXRoRqBJ)
