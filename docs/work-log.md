> Snapshot of the live Claude Doc (https://claude.ai/artifact/Pr3cjkiYEo6rnXKb95XuJd), kept for safe keeping. Network addresses are redacted. The Claude Doc is the current copy.

# Home Lakehouse Work Log

Updated Nov 3, 2026 · @wrolfgar

## How to use this log

Every piece of work on the home-lab lakehouse lands here as it happens, newest first: what was done, why, the key commands, and what the output proved. It is the history; the Home Lakehouse Handoff doc stays the snapshot of where things stand now.

- **Where the work runs.** Since 2026-10-25, Claude runs directly on the VM (`lakehouse`, <vm-lan-ip>) as user `claude`, so commands are run by Claude and explained step by step rather than handed to wrolfgar.
- **Memory alongside the log.** Decisions and standing rules also go into Claude Code's project memory, and claude-mem records each session on the VM. This log is the human-readable record of all of it.
- **Secrets never appear here.** `.env` values, tokens and passwords are referred to by name only.

## Quick reference

Everything is reached through the VM's Tailscale name from any device on wrolfgar's tailnet, at home or away, with a real certificate. The old `*.lake.home.arpa` names were retired on 2026-10-25.

| What | Where | Login |
| --- | --- | --- |
| Jupyter | <tailnet-host> | Token: `JUPYTER_TOKEN` in the VM's `lakehouse/.env` |
| Dagster | <tailnet-host> | User `<owner-user>`; password not stored (reset with `scripts/set-dagster-ui-password.sh`) |
| Superset | <tailnet-host> | User `admin`; password `SUPERSET_ADMIN_PASSWORD` in the VM's `lakehouse/.env` |
| SSH to the VM | `ssh lakehouse` (Mac `~/.ssh/config`) | User `claude`, SSH key from the Mac |
| VM addresses | Tailscale <tailnet-ip> (`<tailnet-host>`); LAN <vm-lan-ip> |  |
| Proxmox | https://<proxmox-host-ip>:8006, VM 140 |  |
| Code | GitHub `pugwala/lunch-and-learn-data-cleansing`, branch `duckdb-lakehouse` | Pushes as `pugwala` |
| Status snapshot | [Home Lakehouse Handoff](https://claude.ai/artifact/2Ee11DTfMk8kLEoLtR7d3U) |  |

**Read a secret, in your own SSH session (never in chat):**

```bash
grep '^JUPYTER_TOKEN=' ~/lunch-and-learn-data-cleansing/lakehouse/.env | cut -d= -f2-
```

**Check everything, on the VM as `claude`.** It changes nothing and takes a few seconds:

```bash
bash ~/lunch-and-learn-data-cleansing/lakehouse/scripts/bootstrap.sh --check
```

**After a `daily_lake` run:**

```bash
cd ~/lunch-and-learn-data-cleansing/lakehouse && docker compose --profile core exec -T jupyter pytest -q lakehouse/acceptance
```

## Up next

Now: Priorities 1 to 6 and 4b are done: the course 1 / course 2 boundary, automatic tagging, the incident reports (so the approved data model is complete) and chunk 10, the scale-up to L, benchmarked in a scratch lake of its own. So is the find\_by\_tags MCP tool, along with phases 0 to 7, dataset-expansion chunks 0 to 10 and all seven MCP tools. Next in the agreed order (2026-11-02) is chunk 11 (7), then course 2's own repo (8) and the how-to document (9). Each waits for wrolfgar's go-ahead. The other unticked items are housekeeping, done whenever there's room.

- [x] Steps 1 to 5 of the recovery plan (see the entries below), the Handoff doc update, and the `core-plus-dagster` snapshot
- [x] Passwordless sudo: kept permanently by wrolfgar's decision
- [x] Phase 4, slice 1: Cube v1.8.3 serving gold read-only (5 acceptance tests), pushed as `319117a`
- [x] Tailscale on the VM: `lakehouse`, <tailnet-ip>
- [x] **Phase 4, slice 2, Superset: done 2026-10-25 (see entry). Original research notes**, written before it was built:
  - Image `apache/superset:6.1.0` (1.27 GB, pulled) runs as `superset` (uid 1000) on 8088 with Python in `/app/.venv`, and has no Postgres driver. Plan: `lakehouse/superset/Dockerfile` adding `psycopg2-binary==2.9.13` (released 2026-09-09) with `uv pip install --python /app/.venv/bin/python`.
  - The image's own healthcheck curls `localhost:8088/health`; curl is present. Config is read from `/app/pythonpath` (`superset_config.py`), and the server starts via `/app/docker/entrypoints/run-server.sh`.
  - The `superset` database exists in catalog-pg, but there is no `superset` role. Plan: an idempotent `postgres/init/03-superset.sh`, like `02-dagster.sh`, run by `bootstrap.sh`.
  - New secrets for `bootstrap.sh` (bats tests first): `SUPERSET_SECRET_KEY`, `SUPERSET_PG_PASSWORD`, `SUPERSET_ADMIN_PASSWORD`. wrolfgar reads the admin password in his own SSH session, never in chat.
  - Caddy: add a `superset.{$LAKE_DOMAIN}` site proxying to `superset:8088`.
  - Tests first: `acceptance/test_superset.py` (health; the Cube database in Superset returns 100,000 records through SQL Lab), plus a bats check that bootstrap starts `superset` and that Caddy answers for it.
  - wrolfgar's Mac `/etc/hosts`, once Superset is up: `<tailnet-ip>  jupyter.lake.home.arpa  dagster.lake.home.arpa  superset.lake.home.arpa`
- [x] Phase 4, slice 3: saved `%sql` connection in Jupyter, as `lake_ro`
- [x] Bring code written before the docstring rule up to it (`lake.py`, `load_lake.py`, `definitions.py`, `bootstrap.sh`, `bootstrap.bats`) when wrolfgar asks
- [x] Sites served on the Tailscale name with a real certificate: <tailnet-host> and /dagster/
- [x] Committed the Tailscale-name change as f3b449a (pugwala)
- [x] wrolfgar: open both Tailscale URLs from the Mac; add the SSH entry (Host lakehouse, <tailnet-ip>)
- [x] Retire the old \*.lake.home.arpa names once the Tailscale URLs are confirmed
- [x] Committed the retirement of the lake.home.arpa names as 27508d6 (pugwala)
- [x] Commit the Superset slice once wrolfgar approves
- [x] Trust Test dashboard in Superset (test first)
- [x] Employer tie-backs removed (friend's audit, steps 1 to 4): fresh public repo, guard Action, lake rebuilt under offender\_number
- [ ] Re-check GitHub code search once the new repo is indexed (control word offender\_number must find hits first)
- [x] Confirm the guard Action starts on its own after the next normal push (so far only manual runs start)
- [x] Sessions 6 and 7 fail in the lakehouse image: spaCy model load error (OverflowError), present before any rename
- [x] Course site, README and Facilitator Guide docs, slides and Handoff brought in line with the anonymized repo (2026-10-26)
- [x] Phase 5 (OpenMetadata, Cube masking, the tags-to-masks loop) built and green, uncommitted: commit and push once wrolfgar approves
- [x] Superset Custody dashboard on the custody views, built and green (2026-10-26 19:35 CDT), uncommitted
- [x] Commit the Custody dashboard once wrolfgar approves
- [x] Alerts delivered by self-hosted ntfy (wrolfgar's choice), built and green 2026-10-26 20:07 CDT, uncommitted
- [x] Commit the ntfy alerting once wrolfgar approves
- [x] wrolfgar: set up the ntfy phone app (README, Monitoring and alerting, On the phone), then a test notification to lakehouse-alerts
- [ ] DuckDB 2.0.1 not released yet (only a dev build, 2026-10-22): recheck later
- [ ] GitHub code search: still not indexed (control word offender\_number: 0 hits, 2026-10-26 19:40 CDT); recheck later
- [x] Ops 1: DuckLake housekeeping (weekly; expire snapshots older than 30 days, clean old files, merge small files; metric + alert)
- [x] Ops 2: CI on GitHub (bats, dbt sandbox, promtool/amtool, docstrings, dagster definitions validate; no secrets)
- [x] Ops 3: Runbooks in lakehouse/runbooks/, linked from every alert and from ntfy
- [x] Ops 4: Off-machine backups with restic (catalog + /lake/data) plus a monthly restore drill; local folder until TrueNAS is ready
- [ ] wrolfgar: TrueNAS dataset + NFS share for <vm-lan-ip> (maproot root/wheel, NFS service on), then send the TrueNAS IP and dataset path
- [ ] wrolfgar: save RESTIC\_PASSWORD (in lakehouse/.env) in a password manager OFF the VM; without it a backup can't be read after losing the VM
- [x] wrolfgar: OK to push the CI workflow to main (local branch pending/lakehouse-ci, 8b74fc8), then dispatch lakehouse-ci on duckdb-lakehouse
- [ ] Switch backups to TrueNAS once the share exists (README: Off-machine backups, Switching to TrueNAS)
- [x] Data readiness (business inputs, closes, final/provisional per product month) built and green 2026-10-27 04:33 CDT, uncommitted
- [x] Commit data readiness once wrolfgar approves
- [x] Business rules in the ontology (rulebook, pseudonymous-key deduction, SHACL shapes), built and green 2026-10-26 20:27 CDT, uncommitted
- [x] Commit the business rules once wrolfgar approves (with or after the ntfy commits)
- [x] Chunk 5b, before chunk 6 (wrolfgar chose option B on 2026-11-01): new villains turn up in more fights, so fewer charges land on today's people and dismissals no longer lead (now 462k of 900k at M). Record fights stay as they are.
- [x] Chunk 6: built-in mess with answer keys (1305d86; homelake b990b54)
- [x] Chunk 7: the world's lake layers, bronze to gold, monthly in Dagster (fc2a595; homelake 46eace6)
- [x] Chunk 8: the world's meaning, glossary, sensitivity and rules (57a8380; homelake b6e6179)
- [x] MCP: filters and time ranges on query\_metric, and a business\_rules tool (5fd8d98; homelake 043903b)
- [x] Chunk 9: data products, Cube views, dashboards and readiness inputs for the world (dd07a64; homelake 1aa80bf)
- [x] Priority 1: the boundary between course 1 (cleansing) and course 2 (the architecture). Decided by wrolfgar on 2026-11-02: course 1 is sessions 1 to 7, ending with "Text II: Meaning Over Words", plus simple pipelines and the Unity Catalog basics the core sessions need. Everything else is course 2: the rest of enterprise/ (deep pipelines, governance, jobs and alerts, monitoring), extras/ and the whole lakehouse. Course 2 starts from course 1's cleansed output. Boundary document written 2026-11-02: [Course 1 / Course 2 Boundary](https://claude.ai/artifact/R1688c4LU7fYfwiQGJQDij). It maps each enterprise/ notebook to a course. wrolfgar left its 5 open questions to Claude: 02\_pipeline splits at section 5, 00\_preflight is trimmed, extras/ becomes a course 1 bonus exercise, the course 2 notebooks move with Priority 8, and automatic tagging is Priority 4b.
- [x] Priority 2: course 1's cleansed output as a pinned input to course 2. A frozen, versioned copy (the cleansed records and reference data, with a fingerprint), proven by course 1's 19 numbers before it's published. Course 2 lands it like any upstream source; universe builds from it and its own word lists, never from the live lake tables or by importing generator/. Done 2026-11-02 (commit 0d384ec, homelake 7e05069): lakehouse/handoff/ publishes v1 to /lake/landing/handoff/course1/v1 (11 tables, 19 of 19 numbers, 6 s) and course 2 pins it in course1.lock.json. universe reads its core from it and keeps its word lists in course\_words.json, and a code scan keeps it from reaching into course 1 (it found 14 places before). The world came out byte-identical at scale S (45 files) and M (75 files, 16.5M rows). 6 mutations caught; lakehouse/tests 106 passed. The first CI run failed because its sandbox had no handoff (on the VM it had quietly used the real one). The fix, 1225daa (homelake 63f3a42), gives the sandbox its own handoff folder and adds a \`handoff\` check that publishes into it, for 15 checks in all. CI is green on both repos, so a publish on a GitHub runner is byte-identical to the lock.
- [x] Priority 3: one cleansing story for course 2. Changed on 2026-11-02: dbt no longer re-cleans the core, which would repeat course 1. Instead, a written handoff contract for course 1's cleansed output (columns, types, keys, and the 19 numbers as its acceptance checks); the core arrives clean from upstream, and the expanded world is cleansed in dbt. Course 1's pandas pipeline leaves course 2's daily run. Done 2026-11-02 (commit cc0cd6c, homelake 7dd8f5f). The daily load now lands the pinned handoff after checking it, and no longer runs any of course 1's code. Handoff v2 adds bronze (the raw file, as text); its silver and ref files are identical to v1's. contract.yml lists every table's key and column types, and receive.adopt refuses a version that breaks it. regenerate\_lake is gone, and bootstrap.sh publishes the handoff on a fresh install. A live daily\_lake run succeeded, and all 13 ref, bronze and silver tables matched this morning's rows, types and contents. 7 mutations caught; acceptance 343 passed, with only the 2 known stale tests failing.
- [x] Priority 4: course 1's material as an optional add-on (Trust Test, the parity gate, notebook\_smoke), so course 2's platform stands on its own. Done 2026-11-02 (044f545, homelake 4560ad5). One switch, LAKEHOUSE\_COURSE1 (on by default, or off), and course1\_addon.py lists every piece. dbt builds models/course1/ only while on; cube.js loads cube/course1/ only while on; Superset skips the Trust Test dashboard and Dagster skips the parity check and the notebook job while off; bootstrap skips the model. NotebookSmokeStale now counts only while the add-on is on. checks.sh proves course 2 builds with it off (standalone) and that Cube loads course1/ only while on (cube\_addon). The live lab is on: daily\_lake succeeded and acceptance passed 343, with only the 2 known stale tests failing. Slip: 73ff4a4 went out with only the file renames (a failed git add), so its CI is red; the rest followed in 044f545 (CI green). Found along the way: dashboards.py doesn't retry on Superset's 429 rate limit (added to housekeeping).
- [x] Priority 4b (a course 2 topic wrolfgar raised on 2026-11-02): attach governance tags (CJIS, PII and so on) automatically when a data source is ingested, plus other metadata tags that make searching, parsing and organizing easier for end users. Today each sensitive column is tagged by hand (meta.sensitivity in dbt, pushed to OpenMetadata by om\_sync, and on to Cube masks). Placed right before incident\_report, since free text is where automatic detection matters most. Done 2026-11-02 (6939620, homelake a2ef0e0). In lakehouse/tagging/, sources.yml registers each source (its tables, system, governance such as CJIS, refresh, and whether its rows describe people), and rules.yml holds the column rules (by name, or free text by its values). Tags follow dbt lineage into gold, every table gets its layer, and a personal column makes its table Governance.PII. The daily run's new governance/tags step writes ops.table\_tags and ops.column\_tags; om\_sync publishes them as five classifications (Governance, PIIType, Source, Layer, Refresh) and adds OpenMetadata's own PII.Sensitive. Live: 54 CJIS tables, 26 with personal data, 86 personal columns. It finds all 42 hand-tagged columns, plus the state ID, offender number, gender, the conduct notes and the exceptions' raw values. Search by tag works. Hand-set Sensitivity tags and the Cube masks are unchanged.
- [x] MCP find\_by\_tags (wrolfgar, 2026-11-02): find lake tables and columns by any tags they carry. Done 2026-11-02 (38d85f7, homelake eb6d2cf). The seventh tool reads every lakehouse table and its tags from OpenMetadata as mcp-reader, so all 48 tags in use work: the tagger's, the hand-set Sensitivity tags, PII.Sensitive and glossary terms. It takes one tag or many, with match any or all, and level table, column or both (column with all means one column carries every tag). Names are forgiving (CJIS, PIIType.\*, any case, spaces or hyphens). With no tags it lists every tag in use; an unknown tag names close matches. 10 acceptance tests, 6 mutations caught. A failed check in my commit chain first stopped the commit and left homelake in an empty cherry-pick (skipped, nothing lost).
- [x] Priority 5: incident\_report table (free text): done 2026-11-03, 997268d, homelake de44bd6; it completes the approved model before the scale-up
- [x] Priority 6: chunk 10, scale-up (L) and benchmarks, measuring the final pipeline: done 2026-11-03 in a separate scratch lake (/lake/scratch/L), a4f77fd, homelake cf985dc
- [x] MCP tools data\_product\_info and data\_quality (6896c68; homelake 2ac8828)
- [ ] Fix two stale live acceptance tests: test\_node\_metrics\_describe\_the\_vm expects under 34 GiB of RAM (the VM has 47), and test\_population\_headline\_matches\_cube hard-codes 81,409 (now 80,877)
- [ ] Remove the leftover Fuseki scratch graph urn:test:8f395fd7-…
- [ ] Architecture drawing in the Lakehouse Plan: on hold (wrolfgar, 2026-10-31)
- [ ] Student handout PDF on homelake
- [ ] Update the outdated 'no push runs' comment in the CI workflow
- [ ] dashboards.py --check: retry on Superset's 429 rate limit (it failed once right after an acceptance run, 2026-11-02)
- [x] Docs snapshots in homelake/docs: committed and pushed 2026-11-03 as homelake 319a0b2 (wrolfgar's permission). From now on: re-export and re-scrub when a doc changes
- [ ] Clear pre-scrub session records (show wrolfgar the list first)
- [ ] Ontology guide: rerun recipes 1 to 8, 10, 11 and 13 to 16 against the expanded world (their answers predate it; recipes 9 and 12 were rerun 2026-11-02)
- [ ] Priority 7: chunk 11, course sessions (optional), on the settled boundary
- [ ] Priority 8: course 2 in its own repo (wrolfgar's call; homelake could become it), depending on course 1 at a tagged version, so the how-to document's paths and links are final
- [ ] Priority 9: Lakehouse how-to document (a Claude Doc, wrolfgar, 2026-11-02): how to use every part, including all seven MCP tools with worked examples. Best after chunks 10 and 11 and incident\_report, once the world stops changing. Today the MCP tools are described only in lakehouse/README.md (MCP section) and the server's docstrings.

## 2026-11-03 · Chunk 10: the scale-up to L, benchmarked in a scratch lake

**Ask:** wrolfgar, 2026-11-03: "build the new lake then update and commit the docs". The new lake is the separate scratch lake recommended for chunk 10; the live lab stays at M.

**Result:** the world at L (65.6M rows, four times M) builds, loads and passes every answer-key and rule test, and the dashboards' questions stay under 0.3 s. L lives in `/lake/scratch/L` to try things on. Commit `a4f77fd`, homelake `cf985dc`.

**How (step by step):**

- **The tool:** `universe/bench.py` (`python -m lakehouse.universe.bench --scale L`) builds a scale into a folder of its own and runs it end to end there: the build, a seed, dbt's `world_full` and `world_monthly` runs as Dagster makes them (every month in one run, as a backfill does), then six queries like the dashboards' asks, three times each.
- **The scratch lake** is a real DuckLake (same Parquet format as the live one), but its catalog is a file in the folder (`catalog.ducklake`) and its data goes to the folder's `data/`. Its two seed tables (`ref.nibrs_offenses`, `silver.hero_offenders`' keys and sentence dates) come from course 1's pinned handoff, like the world's core, so the live lake is never opened.
- **Measured:** each step is its own process, timed, with the peak memory of its whole process tree from /proc (the build's 10 workers are children, so the kernel's own one-process peak would miss most of it). Report: `bench.json` in the folder.
- **Safety:** a run clears its folder first, so a folder that is, sits inside, or holds the live data path or the live world is refused. Backups only mount `/lake/data`, so the scratch lakes are not in them. `/lake/scratch` was created owned by the container user (uid 1000), like `/lake/landing`.

**Numbers** (VM: 12 vCPU, 47 GB, whole stack running; the second of two runs, 06:33 to 06:38 CST, within a few percent of the first):

| Step | M (16.7M rows) | L (65.6M rows) |
| --- | --- | --- |
| Build (clean tables, mess, keys) | 38 s, peak 9.6 GB | 164 s, peak 27.6 GB |
| dbt world\_full | 9.9 s, 1.3 GB | 15.0 s, 2.0 GB |
| dbt world\_monthly (with the answer-key tests) | 13.0 s, 2.9 GB | 29.2 s, 6.3 GB |
| Slowest query (busiest villains, 24M participations at L) | 0.078 s | 0.261 s |
| Disk: world / lake Parquet | 1.0 GB / 774 MB | 4.1 GB / 3.1 GB |

**What it says:** L fits this VM; the limit is the build's memory, not the lake. dbt and the queries grow more slowly than the data (2 to 3 times for 4 times the rows). The build's 27.6 GB peak left about 7 GB free beside the stack: each worker keeps its own copy of the fight plan, which grows with the scale. For a bigger scale or a smaller machine, use fewer workers (`--workers 4`). Disk is no concern (7.1 GB for L of 951 GB free).

**Tests (TDD):** `tests/test_universe_bench.py`, 8 tests, a whole run at S in a temporary folder. Red first (no module), then green. **13 of 13 mutations caught.** The two mutants that would have pointed dbt at the live lake were checked through a unit test only and never run. `checks.sh` 17 of 17 (the bench test runs in CI's sandbox too).

**Caught on the way:** the boundary guard (`test_universe_never_reaches_into_course_1`) failed when the first version seeded from the live lake. Seeding from the handoff fixed it and is stronger: the benchmark never touches the live lake. The benchmarks were rerun with that code, so the committed numbers come from the committed code. Also: the container has no `/usr/bin/time`, hence the /proc measuring; and a stray `git push origin main` in homelake was a no-op (main was already level), then the right branch was pushed.

**Next:** chunk 11 (optional course sessions) on wrolfgar's go-ahead. The ontology guide's recipes 1-8, 10, 11 and 13-16 still show pre-world answers; rerun them with the how-to doc.

## 2026-11-03 · Priority 5: incident reports, the world's free text

**Result:** the expanded world has its last approved table. `universe/reports.py` writes 200,000 incident reports at M, each a free-text account of one fight, plus a **mention key** that says exactly where every personal detail sits in the text. Both are live in the lake (`world_bronze` and `world_silver.incident_report`). Commit `997268d`, homelake `de44bd6`; CI green on both.

**Why:** wrolfgar, 2026-11-03: "go 5". It completes the model approved 2026-11-01, before the scale-up (chunk 10). Automatic tagging went first (4b) so the tags would be waiting when the free text arrived.

**What we found:**

- The approved model said only "a free-text account of a fight, \~200k, linked to incident", so the columns were Claude's call: `incident_report_id`, `incident_id`, `author_person_id`, `report_kind`, `filed_at`, `narrative`.
- About 3% of today's villains have no alias or no full name (gaps from course 1's data), and civilians never have an alias. The text falls back from alias to name to "an unidentified suspect", and a name is only mentioned when both parts exist.
- The dbt test `world_flags_match_answer_key` reads `answer_key/*/*.parquet` as one glob. A mention key with other columns inside `answer_key/` broke it, so the key got its own folder, `mention_key/incident_report/`.
- The live M world was built Nov 2 at 01:00, before Priority 2 switched it to course 1's pinned handoff. Rebuilt today from the handoff, all 75 existing files were byte-identical.

**What we did:**

- **Three kinds of report.** A hero's `field report` (148k, third person), a civilian's `witness statement` (32k, first person, signed with their own name and phone), or the desk's `desk report` of the call (18k, no author). Bigger fights are written up more often, one report per fight at most. Each is filed after the fight ends, never after today.
- **It reads like people write.** Dates and times several ways, 10% in capitals, 15% with typos, 2.5% junk (`SEE ATTACHED`, `TBD`, null).
- **It names people.** Names, aliases, SIDs, birth dates, heroes' real names, witnesses' phone numbers (fictional 555-01xx only).
- **The mention key.** 1,893,406 rows at M: report, `start_pos`/`end_pos`, kind, `as_written`, person, and the truth as the person table holds it.
- **The lake.** The mess leaves the narrative alone, and silver keeps it exactly, so the places hold on the lake. dbt got `wb_`/`ws_incident_report` through `world_spec()`, the three report kinds in the code list, and the exceptions view.
- **Meaning.** The glossary term Incident Report: about Incident, related to Person. Published to OpenMetadata and Fuseki.
- **Live.** Rebuilt M beside the live world and compared every fingerprint, then ran `world_refresh` and a 370-month `world_monthly` backfill (all succeeded), the tagger, `om_sync.py` and `om_to_rdf.py`.

**Verified:**

- **Tests first.** `test_universe_reports.py` 13; `test_world_lake.py` adds one; `test_world_meaning.py` gains the term, the tags and the graph. All seen failing first.
- **Mutations.** 15 of 15 caught after strengthening. The first run let 3 through: a mention shifted by one character (it still matched its own text, so now the words must spell the truth), the filing cap (pulled into `filed_time()` and tested directly), and phones written one way only.
- **The tagger, with no rule change.** It tagged `narrative` `PIIType.FreeText` by its values. Both tables are now `Governance.PII` and CJIS: 56 CJIS tables, 28 with personal data, 88 personal columns, 44 hand tags (pinned counts moved in `test_tags.py` and `test_mcp_tags.py`).
- **Live lake.** 200,000 rows in bronze and silver, 0 narratives differ from the clean ones, and 0 of 1,893,406 mentions are off their place.
- **Suites.** `ci/checks.sh` 17/17. Acceptance 358 passed; only the 2 known stale tests failed. One more failed until `monitoring/data_products` was re-materialized: product freshness had trailed today's world rebuild, exactly as that test intends.

**Next:** chunk 10, the scale-up to L with benchmarks, on wrolfgar's go-ahead. First, his call on a separate scratch lake (recommended) or the live one.

## 2026-11-03 · Docs snapshots committed to homelake

**Result:** the five docs are in homelake as Markdown, scrubbed, in `docs/` with a `README.md` index (who's who and links to the live docs). Commit `319a0b2` on `duckdb-lakehouse`, by `pugwala`, pushed.

**Why:** wrolfgar, 2026-11-03: "commit the docs and go 5" (the permission he said he'd give once we had mopped up).

**What we did:**

- Re-exported all five docs. The Work Log (rev 156), Handoff and ontology guide were newer than yesterday's copies; the Plan (rev 34) and Boundary (rev 10) hadn't changed.
- Ran `~/docs-snapshot/scrub.py` (private, never committed) with the persona team: wrolfgar the public-sector data architect (stands in for wrolfgar), troglobyte the junior data engineer, pugwala the data analyst who commits.
- Staged the six files by name and committed them as `pugwala`.

**Verified:**

- 0 tailnet names or addresses, 0 of wrolfgar's name or email, 0 LAN addresses, 0 daily-schedule lines, in the files and in the staged diff.
- `tools/tieback_check.sh` clean, before the commit and again in the pre-commit hook.
- `test_homelake.py` 2 of 2 passed with the files staged. Its rule allows the old repo's full name; the 14 mentions left are VM folder paths and the repo's name, which wrolfgar chose to keep (2026-10-31).

**Next:** Priority 5, `incident_report`.

## 2026-11-02 · Docs snapshots for homelake/docs, prepared (not committed)

**Result:** scrubbed Markdown copies of the five lakehouse docs sit uncommitted in `~/homelake/docs/`, with a `README.md` index. They wait for wrolfgar's permission ("when we are done and we have mopped up, I will grant permission").

**Why:** wrolfgar, 2026-11-02 (16:03 CST): keep the docs in homelake/docs for safe keeping and update them as we go. homelake is public, so Tailscale details and his name come out "for sure"; where a name is needed, pugwala, troglobyte or wrolfgar.

**What we found:**

- The Handoff doc was a week behind (Oct 27). Its status, "Not done yet" and "Since then" sections were brought current first (rev 116).
- The Dagster and ntfy logins are a lowercase `<owner-user>`, which a capitalized name search misses.
- The export writes bare links as `<https://...>`, so a plain host rule left `<<tailnet-host>>`.
- The Handoff's "Working with" section described wrolfgar's job, and the Plan referred to "the agency". Neither names the employer. wrolfgar then corrected his role (a public-sector data architect; fixed in the Handoff, rev 117) and said "agency is probably OK for now", so the job wording stays in the copies. Only his daily schedule is dropped.
- `test_homelake.py` forbids the course's branding and links to the old repo, so the copies link to homelake.

**What we did:** exported each doc as Markdown and decoded the payloads from the saved results and the session transcript. A private scrub script outside every repo (`~/docs-snapshot/scrub.py`) holds the replacements and stops if any fixed phrase is missing or anything is left over. It replaced:

- 26 tailnet host addresses and 10 tailnet IPs;
- 10 LAN and Proxmox addresses;
- 209 name mentions and 2 logins;
- 8 branding and schedule phrases.

**Verified:**

- 0 hits in the new files for tailnet hosts and IPs, the tie-back pattern, the name (any case), personal email, LAN addresses, branding and the daily schedule.
- 6 mutations of the scrub rules were all stopped by the leftover checks.
- The tie-back pattern, taken from the script, matched all 12 of its own words in a de-bracketed copy, so its 0 is real.
- Nothing is staged.

**Next:** wrolfgar's permission, then re-export, re-scrub, and commit and push to homelake only.

## 2026-11-02 · MCP find\_by\_tags: find data by any tags it carries

**Result:** the MCP server's seventh tool, `find_by_tags`, finds lake tables and columns by their tags. Ask for one tag, any of many, or all of them, on tables, columns or both. Commit `38d85f7`, homelake `eb6d2cf`; CI green on both at 14:13 CST.

**Why:** wrolfgar asked for a tool that finds data by any tags on a table or column, built for many tags at once: "a single tag, multiple tags, or even match all of them if the user was crazy".

**What we found:**

- OpenMetadata holds every tag in one place: the tagger's five families, the hand-set Sensitivity tags, its own PII.Sensitive and the glossary terms (Lakehouse.\*). 48 tags are in use on lakehouse tables.
- `level=column` with `match=all` needs its own meaning: one column must carry every tag. Otherwise a table with a birth date in one column and a name in another would count as "a birth-date name".
- A bare `PII` is ambiguous: our tag Governance.PII, or OpenMetadata's PII family. A bare tag name now beats a family name, and `PII.*` asks for the family.

**What we did:** `lakehouse/mcp/server.py`:

- `lake_entities()` pages through OpenMetadata 50 tables at a time as mcp-reader.
- `squash()` and `resolve_tag()` make names forgiving: case, spaces and hyphens don't matter, a bare name works, and `Family.*` means the whole family.
- `tag_vocabulary()` describes every tag in use.
- `find_by_tags(tags, match, level)` returns `TagSearch`: the tables, the tags each matched, and counts.

With no tags it lists the vocabulary. An unknown tag raises a ToolError naming close matches. `acceptance/test_mcp_tags.py` has 10 tests, each checked against the lake's own ops.table\_tags and ops.column\_tags, never against the tool's other answers. `test_mcp.py` now expects seven tools. The README MCP section was updated.

**Verified:** every test failed first. 6 mutations caught, including one in paging. All 48 tags at once, with any or all, answers in well under 10 s. MCP acceptance 54 passed.

**Slip:** my "anything left unstaged?" check used a bare grep, which exits 1 when it finds nothing. So the commit chain stopped, the push was a no-op, and homelake was left in an empty cherry-pick. I skipped the cherry-pick and committed again with a `[ -z "..." ]` check. Nothing was lost.

**Next:** Priority 5, incident\_report, on wrolfgar's go-ahead.

## 2026-11-02 · Automatic tags as data lands (Priority 4b)

**Result:** every lake table and column is tagged on each daily run, and OpenMetadata shows the tags where people search. Live: 54 CJIS tables, 26 tables with personal data, 86 personal columns. Commit `6939620`, homelake `a2ef0e0`.

**Why:** wrolfgar, 2026-11-02: pipelines should attach governance tags (CJIS, PII and so on) automatically when a source is ingested, plus any metadata tags that make searching and organizing easier.

**What we found:**

- OpenMetadata already has system classifications named PII and PersonalData, so the column family is PIIType.
- The reference crosswalks matched name rules (alias columns) but hold no people. Sources now say `people: true/false`, and a built table inherits that through lineage.
- 25 of the handoff's columns were hand-tagged, not the 30 or more I first guessed in a test.

**What we did:**

- `lakehouse/tagging/`:
  - `sources.yml` registers each source: its tables, governance, Source tag, refresh and whether its rows describe people.
  - `rules.yml` holds the column rules (by name, or free text by its values) and the five families: Governance, PIIType, Source, Layer and Refresh.
  - `tags.py` follows dbt lineage into gold, gives every table its layer, and rolls a personal column up to Governance.PII.
- Dagster: a `governance/tags` asset writes ops.table\_tags and ops.column\_tags, before the OpenMetadata step.
- `om_sync.py`: a `tag_vocabulary` step, the automated tags, and OpenMetadata's own PII.Sensitive on every PIIType column. Hand-set Sensitivity tags and the Cube masks are unchanged.

**Verified:** `tests/test_tagging.py` 33 tests and `acceptance/test_tags.py` 5, all red first; mutations caught. All 42 hand-tagged columns were found, plus the state ID, offender number, gender, conduct notes and the exceptions' raw values. OpenMetadata's search filtered on Governance.CJIS returns exactly the tagger's 54 tables. `om_sync --check` is in step.

**Next:** the find\_by\_tags MCP tool (wrolfgar asked next), then incident\_report.

## 2026-11-02 · Course 1 / course 2 boundary built (Priorities 1 to 4)

**Result:** course 2's platform now stands on course 1's frozen, checked output and runs none of course 1's code. Course 1's own material (Trust Test, parity gate, notebook smoke) is a switchable add-on. Boundary doc: [Course 1 / Course 2 Boundary](https://claude.ai/artifact/R1688c4LU7fYfwiQGJQDij).

**Why:** wrolfgar decided course 1 is sessions 1 to 7 (ending with "Text II: Meaning Over Words") plus simple pipelines and the Unity basics. Everything else is course 2, which starts from course 1's cleansed output.

**What we did:**

- **Priority 1:** the boundary doc maps every enterprise/ notebook to a course. wrolfgar left its 5 open questions to me: 02\_pipeline splits at section 5, 00\_preflight is trimmed, extras/ is a course 1 bonus, notebooks move with Priority 8, and tagging becomes 4b.
- **Priority 2** (`0d384ec`, CI fix `1225daa`; homelake `7e05069`, `63f3a42`): `lakehouse/handoff/`.
  - `publish.py` runs course 1 and writes Parquet. It checks the 19 numbers on the files, then renames `.partial` into place.
  - `receive.py` holds the lock (`course1.lock.json`).
  - universe builds from the handoff and `course_words.json`, never from course 1's code.
- **Priority 3** (`cc0cd6c`; homelake `7dd8f5f`): handoff v2 (adds bronze and the answer key), and `contract.yml` (13 tables: key and column types), which `receive.adopt` enforces. `lake.run()` lands the pinned handoff; `regenerate_lake` is gone. bootstrap publishes on a fresh install.
- **Priority 4** (`73ff4a4` + `044f545`; homelake `6f7482e` + `4560ad5`): `LAKEHOUSE_COURSE1=on|off`, read by `course1_addon.py`. It gates dbt `models/course1/`, Cube `cube/course1/`, the Trust Test dashboard, Dagster's parity check and notebook job, and the NotebookSmokeStale alert. `checks.sh` gained `handoff`, `cube_addon` and `standalone` (17 checks).

**Verified:** the world is byte-identical at S and M. All 13 ref, bronze and silver tables match the morning's rows, types and contents. daily\_lake succeeded live. Acceptance 343 passed with only the 2 known stale tests failing. CI green on both repos after each fix.

**Slips:** CI's sandbox first had no handoff (fixed with its own `HANDOFF_ROOT`). `73ff4a4` went out with only the renames after a failed git add (finished in `044f545`, no force push).

**Next:** Priority 4b, automatic tagging.

## 2026-11-02 · MCP: data\_product\_info and data\_quality

Result: the agent has six tools. data\_product\_info answers "what is this data product, and can I trust this month's number?" in one call. data\_quality answers "how clean is the data?" for the course data and the expanded world.

Why: wrolfgar, "build the mcp tools data\_product\_info and data\_quality. what will data\_product\_info do or report?"

What data\_product\_info reports, for every product or one by name (any case, hyphens or spaces): its domain and question; the tables it delivers; the Cube views and metrics that serve it, to ask query\_metric; its glossary terms; the business inputs it waits on (unit, system, days to close); the data contracts OpenMetadata holds for its tables (refresh promise, column count) and any table without one; readiness (the latest month-end, final or provisional, and every provisional month with who it waits on); and freshness against its promise (refreshed when, hours old, the most it promises; fresh or stale). The custody products add the records their snapshot can't place in time.

What data\_quality reports: for the course data, each dimension's pass rate on the latest load, its number of rules, and every rule under the 95% floor (today one: disciplinary\_points completeness, 94.15%); for the world, flagged values per silver table and rule, and the rows they touch (1,158,306 values today, damage the most), optionally for one table; and the data-quality alerts firing now (none).

What we found:

- The server still holds no lake credentials. Everything comes from governed, read-only sources: Fuseki's catalog (DCAT and readiness graphs), OpenMetadata as mcp-reader (which can read data contracts), Cube and Prometheus.
- The world's flags reached Cube through a new world\_exceptions cube that holds counts only: a flagged value can be a person's name, so neither values nor row ids are ever exposed.
- A mutation showed that matching a product by title was untestable, because every title is its name in words. Name matching that ignores case and hyphens already covers it, so the title branch was removed.

What we did: mcp/server.py (both tools, typed results, docstrings); cube/model/world.yml (world\_exceptions); acceptance/test\_mcp\_products.py (14 tests); test\_mcp.py now expects six tools; README MCP section and test-status row.

Verified: 15 tests red first, then 42 of 42 MCP tests green, and 71 with the Cube and world-product tests. 8 mutations caught (exact-name matching, uncontracted tables hidden, freshness inverted, inputs dropped, the floor ignored, rows counted as values, the table filter ignored); the ninth, title matching, survived and that code was removed. checks.sh all passed. Commits 6896c68 and homelake 2ac8828; CI green on all 4 runs (05:59 CST). The DuckDB Home Lakehouse Plan lists the six tools (rev 29).

Next: chunk 10 (scale-up to L, benchmarks) on wrolfgar's go-ahead.

## 2026-11-02 · Dataset expansion chunk 9: the world's data products

Result: the expanded world has three data products in two new domains, declared in files like the custody ones: Field Incidents and Incident Damage (Field Operations) and Court Outcomes (Justice). Cube serves them through four views, Superset shows them on a new Fights, Damage and Courts dashboard, the MCP agent answers questions about them with their readiness, and each month is final only once Field Operations, Insurance or the Courts liaison has closed it.

Why: wrolfgar, "do chunk 9 and then update the lakehouse work log and DuckDB Home Lakehouse Plan and the ontology document, if necessary."

What we found:

- The world's gold tables already have enforced dbt contracts, so the products deliver world\_gold directly; no mart was needed.
- OpenMetadata refuses a data contract whose column type is INTEGER, with only "Invalid request format". A probe showed it wants INT; om\_sync now translates. It also found contracts by model name, which missed the aliased world models (wg\_fct\_incident builds world\_gold.fct\_incident); it now uses the table a model builds.
- The daily run stamped every product "refreshed now". That was true for custody, which is rebuilt daily, but would be false for the world, which is rebuilt monthly. A product's refresh time is now the oldest of its tables' latest Dagster builds, and a new schedule rebuilds the whole world at 04:30 on the 1st, so its 32-day promise holds.
- Readiness months came from the custody snapshot, which starts in October 1996; the world's fights start in January. The readiness view is now a calendar from January 1996 (dbt var readiness\_start), the same for every product.
- The courts input now covers charge decisions too (retitled "Sentencing orders and charge decisions"): one unit's close finalizes Custody Offenses and Court Outcomes, in two domains.

What we did: products/ (3 descriptors, domains Field Operations and Justice, inputs field-reports and insurance-claims, courts widened); cube/model/world.yml (hidden cubes over world\_gold, views field\_incidents, fight\_participants, incident\_damage and court\_outcomes, each with period\_status); period\_readiness calendar; om\_sync contracts by table with INTEGER as INT; definitions.py freshness from materializations and world\_refresh\_schedule; superset/dashboards.py (the world dashboard, a grouped table, status tables filtered to each dashboard's products); the DataProductStale runbook; the README. Published by a daily\_lake run, dashboards.py, closes.py sync and om\_to\_rdf.py.

Verified: test\_world\_products.py written first, 19 tests, all red, then green. 7 mutations all caught (people summed, the uninsured and conviction filters dropped, the calendar back to the snapshot, Incident Damage forgetting Insurance, contracts keyed by model name, the Custody status table listing every product). Full acceptance suite 329 passed; the only 2 failures are the two known stale tests. checks.sh all 14 passed. Commits dd07a64 and homelake 1aa80bf; CI green on all 4 runs (05:39 CST).

Also updated: the DuckDB Home Lakehouse Plan (rev 28: nine chunks in, five products in three domains, four MCP tools, chunk 10 next), and the ontology guide (rev 28: today's counts, recipes 9 and 12 rerun, a property-path example for impact through Charge isAbout Incident).

Next: chunk 10 (scale-up to L, benchmarks) on wrolfgar's go-ahead. The MCP tools data\_product\_info and data\_quality are unblocked.

## 2026-11-02 · Up next list brought up to date

Result: the Up next checklist now matches where things stand. wrolfgar asked whether Phase 4 slice 2 (Superset) was still waiting; it wasn't, but this list still showed it open, and its opening line still said "Now: Phase 4, Superset and Cube".

What changed: ticked five items that were done (Superset slice 2 and its commit, the lake.home.arpa retirement commit, the docstring backfill, which acceptance/test\_docstrings.py now enforces in CI on every file, and the guard Action starting on push, seen on today's push runs). Rewrote the opening line, removed the stale "Trust Test dashboard is still to do" note, and added chunks 6 to 8 and the MCP tools as done, plus the open to-dos from the work-state list (chunk 9, incident\_report, two MCP tools, two stale tests, the Fuseki scratch graph, the drawing on hold, the handout PDF, the CI comment, the session records).

Verified: the superset container healthy for 5 days; Superset commits 4ff076b, 8bc899d, 0fe32fd in git; gh run list shows push-triggered runs (05:05 CST).

## 2026-11-02 · MCP: filters and time ranges on query\_metric; a business\_rules tool

**Result:** the agent has four tools. `query_metric` now takes filters (dimension, operator, values) and a time range: `time_dimension`, `date_from` and `date_to` inclusive, and `granularity` from day to year. A view with one time dimension uses it unasked. `business_rules(about)` returns the rulebook from Fuseki, all of it or the rules about one term or synonym, and says whether each SHACL shape and Prometheus alert holds today. wrolfgar asked for both before chunk 9, so the world's metrics can be asked by month the day they land in Cube. Commits `5fd8d98`, homelake `043903b`.

**What we found:**

- A filter on a masked column compares the masked value: `race_code` equals `W` finds 0 records, and equals `***` finds all 100,000. Filters can't be used to count a race. A test now holds this.
- Cube's `notEquals` keeps empty values (G5 plus "not G5" gives all 100,000). The tool's description says so.
- SPARQL trap: matching a rule's terms and their names in separate OPTIONALs gave the one rule about no term ("Every glossary term has a real definition") every term's name. They're now matched in one OPTIONAL keyed on the rule.
- The first status test passed with a tool that always said "holds", because every rule does hold today. It now compares with Prometheus directly.

**What we did:** `mcp/server.py`: `MetricFilter`, `TimeWindow`, the validation helpers, `query_metric`'s new arguments, and `business_rules` with `Enforcer`, `BusinessRule` and `RuleBook` (reading Fuseki's public SPARQL endpoint and Prometheus, with no new credentials). `acceptance/test_mcp.py` has 12 new tests (28 in all). README MCP section and test-status row. Container restarted (its code is mounted read-only).

**Verified:** 13 tests red first, then 28/28 green. 8 mutations all caught: filters dropped, granularity ignored, date range ignored, operators not checked, `about` ignored, synonyms not matched, shape status inverted, alert status inverted. `checks.sh` all passed.

**Next:** chunk 9 on wrolfgar's go-ahead. Still on the to-do list: `data_product_info` and `data_quality`, after chunk 9.

## 2026-11-02 · Dataset expansion chunk 8: the world's meaning (glossary, sensitivity, rules)

**Result:** OpenMetadata and Fuseki now know the expanded world. The glossary has 12 new terms (27 in all) with typed relations, including a new `occursAt`. `world_bronze`, `world_silver` and `world_gold` are in OpenMetadata, with names and birth dates tagged Personal and STG groups Restricted. Six new rules are in the rulebook (12 in all): five dbt tests over the world's gold and one SHACL shape. Published live through Dagster (`openmetadata/lake`, `fuseki/glossary`); both checks passed. Commits `57a8380`, homelake `b6e6179`.

**What we found:**

- Column names like `outcome` and `status` mean different things in different tables, so a term's `columns:` may now be qualified (`world_gold.fct_charge.outcome`). Bare names still link everywhere.
- om\_sync matched dbt docs by model name, but world models build aliased tables (`wb_person` builds `world_bronze.person`), so it now reads `config.alias`.
- Person Key identifies Person, so the existing pseudonymous-key deduction covers `person_key` with no change to the rule.
- The power rule had 1,713 unexplained uses at S (0.43%). The answer key explains every one: 1,649 needed a holding whose person or power link had been orphaned, and 64 involved a duplicate silver didn't resolve. So that test passes under 1% and fails above it. A real break (fights 40 years before the powers) gave 222,450.
- Two existing tests assumed things the world changed: the pseudonymous keys were only `sid_number`, and every `partOf` pointed at Offender Record. Both were updated to the new truth.

**What we did:** `glossary/glossary.yml` (12 terms, 6 rules, the pseudonymous-key rule now names Person Key); `om_sync.py` (world schemas, qualified links, `occursAt`/`locationOf`, aliases); world bronze/silver `schema.yml` with `meta.sensitivity`, and `stg_group` restricted in gold; `ontology/shapes.ttl` `PersonalStaysOutOfGoldShape` (SPARQL-based); five rule tests in `dbt/tests/world/`; `test_world_lake.py` copies the course's sentence dates into its temporary lake; README section.

**Verified:** `test_world_meaning.py` written first (10 tests, red), then green. 67 acceptance tests pass across meaning, rules, OpenMetadata, RDF, MCP and person; om\_sync and om\_to\_rdf `--check` are in step; `checks.sh` all passed; world and universe tests 17/17. 6 mutations all caught, each by its own rule (the first power mutation was a no-op for that rule; its opposite was caught).

**Next:** chunk 9, data products, Cube views, dashboards and readiness inputs for the world, on wrolfgar's go-ahead. `incident_report` (free text) is still unbuilt.

## 2026-11-02 · Dataset expansion chunk 7: the world's lake layers, monthly in Dagster; Lakehouse Plan brought up to date

**Result:** dbt now builds the expanded world in three new schemas. `world_bronze` holds the messy CSVs as written; `world_silver` holds them cleaned and typed, with every problem flagged in an `issues` list and the `exceptions` view; `world_gold` holds 4 dimensions and 6 facts under enforced contracts. Answer-key tests prove silver against the clean truth. In Dagster, `world_refresh` runs on demand and `world_monthly_job` runs the big facts one month per partition from 1996-01. Both have run on the live lake at M: refresh in 43 s, the full 370-month backfill in about 2 min, all tests passing, about 1 GB in `/lake/data`. Commits `fc2a595`, homelake `46eace6`.

**What we found:**

- DuckDB's `%Y` reads `3/22/01` as year 1, so two-digit years are parsed first, with a pivot: 00-26 are the 2000s. A two-digit birth year outside 1927-2026 can't be told apart (1925 written `25`), so silver flags it `two_digit_year`.
- The first duplicate match (names plus alias) found only 77%, because civilians have no alias. Adding the birthday (month, day and two-digit year) raised it to 95% at M, with 99.5% precision.
- dagster-dbt ran tests that read monthly tables during the full run, before those tables existed. Fix: `world_full` leaves out `tag:world_monthly+`.
- The mutation pass found a loophole: a loose two-digit excuse in the truth test would have hidden a broken pivot. I tightened it before the final run.
- Two live acceptance tests are stale and unrelated to this change: `test_node_metrics_describe_the_vm` expects under 34 GiB of RAM (the VM has had 47 GiB since Oct 28), and `test_population_headline_matches_cube` hard-codes the Sept 30 headline, 81,409 (the Oct 31 figure is 80,877).

**What we did:**

- `dbt/macros/world.sql`: `world_spec()` (every column once), the cleaning macros, `world_silver()`, `world_bronze()`. 15 bronze and 15 silver models, `code_spellings` (from seeds `world_codes.csv` and `world_code_spellings.csv`), `person` with duplicate resolution, and the `exceptions` view. The six big silver tables and four gold facts are incremental (`delete+insert`, `on_schema_change: fail`) and carry `_partition`.
- Three answer-key dbt tests in `dbt/tests/world/`: silver matches truth, flags match the key, every truth row is in silver. `tests/test_world_lake.py` (5 tests) builds an S world and runs `dbt build --select tag:world` on a temporary lake.
- Dagster: `landing/world`, `world_full`, `world_monthly` (single-run backfills), `world_refresh`, `world_monthly_job` and `world_monthly_job_schedule` (05:30 Central on the 1st). `daily_lake`, `regenerate_lake` and CI's dbt check leave the world out.
- Lakehouse Plan (rev 24): a "Where it stands" section (each phase's status and how the build differs from the plan, what was built beyond it, how the risks turned out), a Phase 8 section with the 12 chunks, the open questions ticked with their answers, and a note that the drawing predates the ops pieces and the world. The drawing itself is unchanged, per wrolfgar on Oct 31.

**Verified:** test first (red: "Nothing to do"), then 5/5 green. 11 mutations all caught: six by the truth test, two by the flags test, one by the contract, two by pytest. `checks.sh` all 14 passed; Dagster definitions validate and reload. At M the three answer-key tests passed inside the backfill.

**Next:** chunk 8, glossary, ontology and rules for the new entities, on wrolfgar's go-ahead. Still to add to the model: `incident_report`, the free-text write-ups.

## 2026-11-02 · Dataset expansion chunk 6: built-in mess with answer keys

**Result:** every clean table now also gets a messy CSV copy (`messy/<table>/part-NNNNN.csv`) and an exact answer key (`answer_key/<table>/part-NNNNN.parquet`: `id`, `column_name`, `kind`, `as_written`, `truth`), made by `lakehouse/universe/mess.py` as part of a whole build. At M: 8.3M defects, 692 MB of CSV, 63 MB of keys, about 9 s more (whole build 18 s). Commits `1305d86`, homelake `b990b54`.

**What we found:** `column` is a reserved word in DuckDB, so the key's field is `column_name` (no quoting in chunk 7's SQL). The earlier universe test fixtures don't need the mess, so they pass `with_mess=False` to stay fast.

**What we did:**

- 11 kinds at fixed rates (`mess.RATES`; `mess.SPEC` says which columns): date formats 30%, code variants 12% (each spelling means one value, so a crosswalk undoes it; NIBRS damage like `13b`, `290.0`), money as text 60%, numbers as text 5%, name case 15%, unknown tokens 1%, null tokens 25% of nulls, orphaned links 0.2%, out-of-order dates 0.4%, duplicate people 2% (8,877 at M, same SID, new ids after the last person), links pointing at the duplicate 30%.
- One draw per cell picks its kind from fixed slices, so each cell gets at most one kind and each kind's share is exactly its rate. Ids, `sid_number` and `disposition.offender_number` stay clean.
- The mess has its own random streams, so the clean tables keep their bytes; the manifest now fingerprints the messy files and keys too (`mess` section).

**Verified:** test first (red: no `mess` module), then green: `test_universe_mess.py` 27 tests, including the key listing exactly the cells that differ from the truth. 9 mutations all caught. 74/74 universe tests; `checks.sh` all passed. At M the 15 clean tables are byte-identical to before (manifest diff). CI green on both repos.

**Next:** chunk 7, dbt layers (bronze from the messy CSV, silver cleaned and tested against the answer key), on wrolfgar's go-ahead.

## 2026-11-01 · Dataset expansion chunk 5b: new villains in more fights

**Result:** wrolfgar's option B. Each random villain slot in a fight now goes to a new villain with chance 0.6, so convictions outnumber dismissals at M: 391k convicted or pleaded guilty vs 303k dismissed (before: 162k vs 462k). Pushed as 74bd483 and copied to homelake as 3326609; CI is green on both.

**What we found:** at S only 1.5% of the charges after the records fell on new people (1,312 new villains against \~84,000 of today's). After the change it's 63% at M. New villains now average \~135 fights each, today's \~14.

**What we did:**

- Red: `test_convictions_outnumber_dismissals` in `test_universe_cases.py` (at least half the non-record charges on new people; convictions above dismissals), failing at 1.5%.
- Green: `fights.py` splits villains into two pools (today's and new), so a fight takes some from each without picking anyone twice; the plan draws each fight's new-villain count last, capped by how many are about that day. Record fights keep their villain in slot 0.
- Mutations: share set to 0, and both slot types drawn from one pool, both caught. README updated.

**Verified:** 47/47 universe tests, checks.sh all passed. The before/after manifests show fights, damages, charges and missions byte-identical; only participant, power\_use and disposition changed. GitHub green on both repos.

**Next:** chunk 6, built-in mess with answer keys, on wrolfgar's go-ahead.

## 2026-11-01 · Dataset expansion chunk 5: charges, court outcomes and missions

**Result:** five more tables: charge (900,000), disposition (900,000), mission (150,000), mission\_member (600,000) and mission\_incident (200,000). The whole world, about 16.6M rows, builds at M in 9 s and the manifest verifies. Pushed as dba1ec2 and copied to homelake as 5ee237a; CI is green on both.

**What we found:**

- The lake's `ref.nibrs_offenses` holds 26 NIBRS codes; charges use them, with codes that fit each kind of fight. 4,068 linkable records have no standardized code, so their charges keep it null.
- Today's people can only be convicted through their records (any other conviction would need a record the course doesn't have). About 85% of villains are today's people, so dismissals lead overall: 462k dismissed, 198k acquitted, 162k convicted or pleaded guilty, 79k pending. Open question for wrolfgar before chunk 9 (Courts product).
- At S the approved counts gave fewer charges (90k) than records (94,120), so charge and disposition now keep one row per record at every scale (no change at M).
- Early years have under one non-record fight a day at S, so mission links are shared out in proportion to the fights in each mission's window.

**What we did:**

- Red: `lakehouse/tests/test_universe_cases.py`, 11 tests on a scale-S build in 40k-row chunks, failing on the missing tables.
- Green: `universe/courts.py` (charge plan over captured villains via DuckDB; record charges first; outcomes) and `universe/missions.py` (mission plan; members from the fights' hero pools; links inside the window); `core.py` adds the record's offense code; `scale.py` and `build.py` extended.
- Mutations: 10 real breaks, all caught. One (an unseeded charge plan) first survived: the rebuild test used chunk 1, which holds only record charges. It now rebuilds the last chunk, and went red. README section extended.

**Verified:** 46/46 universe tests (warnings as errors), checks.sh all passed, the M build verified, course files identical to main, tieback clean, no tailnet names, GitHub green on both repos.

**Next:** chunk 6, built-in mess with answer keys, on wrolfgar's go-ahead. Decide first whether today's people's extra charges should stay acquitted or dismissed.

## 2026-11-01 · Dataset expansion chunk 4: fights

**Result:** the fight tables: incident (1,200,000), participant (6,000,000), power\_use (4,000,000) and damage (1,800,000). The same `python -m lakehouse.universe.build --scale M` now builds the whole world, about 13.8M rows, in 8 s, and the manifest verifies. Pushed as 89d3d5d and copied to homelake as cfa82be; CI is green on both.

**What we found:**

- 94,120 of today's offender records have a SID and a sentence date; every sentence falls between 1996-10-08 and 2026-09-24. Each gets its own fight (incidents 0 to 94,119, in offender-number order), before the sentence, with that villain captured, so chunk 5 can hang the charge and conviction on it.
- 2,336 of today's people hold no power: they still fight, but never use one. One record has a birth date after its sentence (planted mess), so the age check covers new people only.
- A fight's participants can straddle two chunk files, so the factories share a **fight plan** from its own stream (day, size, side counts, outcome per fight); participant and damage ids run consecutively per fight.
- M profile: fights grow from about 52k in 1996-99 to 373k in 2020-24; median 4 people a fight, the biggest 41; 426k of 440k people fight at least once; median damage $60k, 65% insured.

**What we did:**

- Red: `lakehouse/tests/test_universe_fights.py`, 11 tests on a scale-S build in 250k-row chunks, failing on the missing `fights` module.
- Green: `universe/fights.py` (the plan; pools of who could fight on a day, sorted so "active by day t" is a prefix; a stride over a prime gives distinct people per fight; one DuckDB join finds the powers held on the day); `core.py` extracts the linkable records (count pinned); `build.py` gains `context()`, `factory()` and `chunk_rows`.
- Mutations: 8 real breaks (random slots, lost powers usable, wrong partial outcome, record fight after sentence, repairs in the future, insurer paying uninsured damage, unseeded plan, villains on the hero side), all caught. One more was a no-op (civilians hold no powers) and was replaced. README section extended.

**Verified:** 35/35 universe tests (warnings as errors), checks.sh all passed, the M build verified, course files identical to main, tieback clean, no tailnet names, GitHub green on both repos.

**Next:** chunk 5, charges (NIBRS codes) and court outcomes linked to today's offender records, plus missions, on wrolfgar's go-ahead.

## 2026-11-01 · Dataset expansion chunk 3: people, powers and places

**Result:** the first six tables of the expanded world, built from today's people in silver: location (20,000), power (400), team (300), person (440,000), person\_power (263,916) and team\_member (60,000). `python -m lakehouse.universe.build --scale M` builds all 784,616 rows into `/lake/landing/universe/M` in about a second, and the manifest verifies. Pushed as b704fcd and copied to homelake as 25e1fe2; CI is green on both.

**What we found:**

- Today's villains already hold 140,795 person-power pairs (88 distinct powers), which the approved \~150k for person\_power didn't count. At M it's now 263,916; the total world grows by \~114k rows, to \~16.7M.
- 9,065 STG affiliations become real team memberships.
- 2,355 of today's people have no sentence date on any record, so their power and joining dates are null, not made up. A few have planted absurd birth dates (year 1213), so powers count from 1900 at the earliest.
- Custody units sit in 106 places, 51 of them not on the course's city list, so cities are the union of both.
- DuckDB 1.5's `.arrow()` returns a reader (use `.read_all()`). Days before 1970 are negative, so test nulls, not `>= 0`.

**What we did:**

- Red: `lakehouse/tests/test_universe_people.py`, 11 tests on a scale-S build against the lake. A 12th, "every date is real or unknown", was added after the first green run showed cast warnings, and it went red.
- Green: `universe/core.py` `extract_core` (people, powers, memberships, units into `_core/`, with pinned counts) and `course_constants`; `universe/scale.py` roles and `powered_rows`; `universe/world.py` (six factories); `universe/build.py` (order, CLI, manifest).
- Tests run with warnings as errors. 4 mutations (made-up core aliases, full-power secondary heroes, powers after the first sentence, heroes in villain teams) were all caught. README section extended.

**Verified:** 24/24 universe tests, checks.sh 14/14, the M build verified, GitHub green on both repos.

**Next:** chunk 4, fights (incident, participant, power\_use, damage), on wrolfgar's go-ahead.

## 2026-11-01 · Dataset expansion: model approved, chunk 2 (generator foundation) done

**Result:** wrolfgar approved the chunk 0 data model as drafted (16 tables, about 16.6M rows at M) and resumed the expansion. Chunk 2, `lakehouse/universe/`, is built test-first and pushed as ce72c77 on lunch-and-learn-data-cleansing, and cherry-picked into homelake as 2c3ab51. CI is green on both. Backups to TrueNAS are deprioritized (wrolfgar: "not interested at this point in time in worrying about the backup of the VM"); they keep running nightly to the local folder.

**What we found:** the course generator draws from one Python `random` sequence, so the new world mustn't share it; it gets its own numpy streams. The work stays in the old repo where the stack runs, copied to homelake per chunk (wrolfgar's choice). Fork-based workers warned (pyarrow runs threads), so workers use spawn. A mutation test exposed a gap (every chunk reusing chunk 0's stream passed), which is now covered. The homelake branding test flagged its own file once committed; it was fixed there as 4b8e6d3.

**What we did:**

- Red: `lakehouse/tests/test_universe.py`, failing on the missing package.
- Green: `universe/rng.py` (one stream per seed, table and chunk; CRC-32 table key; first draws pinned), `writer.py` (1M-row Parquet chunks, vectorized, parallel), `scale.py` (approved counts; S = 0.1, M = 1, L = 4; today's 86,879 people at every scale; catalogs fixed), `manifest.py` (fingerprints; `verify()` names missing or changed files), `core.py` (CORE\_SHA256 of the course file; the test regenerates it).
- Mutations: 4 deliberate breaks, every one caught after the added test. README section "The expanded world (in progress)".
- Benchmark: a 6M-row stand-in table in 0.8 s on 1 worker and 0.6 s on 12, with identical bytes.

**Verified:** 12/12 universe tests, `bash lakehouse/ci/checks.sh` 14/14 locally, both GitHub runs green on both repos, course files identical to main, tieback clean, no tailnet names.

**Next:** chunk 3, people, powers and places, on wrolfgar's go-ahead.

## 2026-10-31 · Ontology guide: brought up to date, recipes 10 to 16

**Result:** [How to Use the Lakehouse Ontology](https://claude.ai/artifact/QZzDB9Lp8k94cXoU7smD7S) now describes all the named graphs and shows the graph's fuller uses. Every new query was run against the live Fuseki first, and its real answer is in the guide.

**What we found:** the guide said "one graph" (there are four kinds now), gave 194 and 173 columns (213 in 27 tables today), said five rules (six), and left out Pseudonymous and the readiness vocabulary. There's also a leftover scratch graph in Fuseki, `urn:test:8f395fd7-…` (1 triple), probably a test that didn't clean up after itself. It wasn't touched.

**What we did:** fixed the opening, the vocabulary and the rule count, and added recipes 10 to 16: stated vs deduced facts (`GRAPH ?g`); property paths (all 14 terms reach Person; 57 columns describe a person by meaning against 13 one step away); readiness (who each product waits on); `ASK` and `GROUP BY` (sensitivity by layer); `DESCRIBE`; downloading the graph (Turtle/TriG via `get`) into `rdflib` and `networkx`; and the graph plus Cube through the MCP server (all 6 restricted fact-table columns come back `***`). A "What it doesn't do" note went under Good to know.

**Verified:** each query was run in the jupyter container against `fuseki:3030`, and recipe 16 was run exactly as printed, using the guide's own notebook helper.

## 2026-10-31 · homelake: the course name removed

**Result:** pugwala/homelake no longer carries the course's name: main 9689d7b, duckdb-lakehouse d3f959f (merge 7620904), all four GitHub runs green. Both repos are kept (wrolfgar); the old repo is untouched.

**What we found:** wrolfgar chose name and links only (course wording, sessions and guides stay as learning material) and to leave functional names alone: the VM folder \~/lunch-and-learn-data-cleansing, the Databricks volume lunch\_and\_learn, the lnl package, and the cleanup notebook's search for old copies. docs/student-handout.pdf has the course's title in all 10 page headers and no source in the repo, so it is unchanged. main has no .gitignore and tracks no .pyc, so a compile check plus `git add -A` swept 5 .pyc files into the first commit; it was amended before any push.

**What we did:**

- Work in a separate clone, \~/homelake (origin = homelake, hooks on), so the live stack and the old repo are untouched.
- Red: lakehouse/acceptance/test\_homelake.py (no branding, no links to the old repo), run in a throwaway lnl-jupyter:local container with \~/homelake mounted: 2 failed (12 branding lines, the old-repo links).
- main: README title (Homelake: data cleansing and a home-lab lakehouse), lnl docstring, Databricks job descriptions and tags (the course tag became project: homelake), schema comments, Spark appName homelake, the cleanup notebook's Git folder link.
- duckdb-lakehouse: merged main, then 27 runbook\_url links, test\_runbooks.py BASE and the README clone URL now point at homelake.
- `gh repo edit pugwala/homelake --description "Home-lab data cleansing and DuckDB lakehouse: fictional superhero records, pandas and PySpark notebooks, for self-study"`

**Verified:** test\_homelake 2/2, test\_docstrings, test\_runbooks file checks 6/6 (the live-Prometheus check needs the stack on homelake's rules). Course files identical between homelake's branches, tieback clean, no tailnet names, every commit pugwala, no .pyc tracked.

## 2026-10-31 · Copied the repo to pugwala/homelake

**Result:** github.com/pugwala/homelake (public, created by wrolfgar at 5:52 PM CDT) is an exact copy of lunch-and-learn-data-cleansing: main (8b74fc8, default) and duckdb-lakehouse (370a7c8), all 55 commits, and no other refs. All four GitHub runs there passed (tieback-check and lakehouse-ci on both branches).

**What we found:** the old repo has no secrets, variables or rulesets to copy; the only setting that differed was the wiki (on in the new repo, off in the old). Files still name the old repo in about 30 places: runbook links in the Prometheus alert rules, test\_runbooks.py, lakehouse/README.md and enterprise/. They were left as-is, since both repos exist (wrolfgar to decide).

**What we did:**

- Scanned every commit on both branches before pushing to a public repo: the guard's pattern over all files (0 hits outside the PDF; the PDF has one version in history, and its extracted text is clean), no tailnet names or 100.x addresses, and every author and committer is pugwala.
- Pushed only the two branches, not a mirror, so the old orphaned pre-scrub commit can't come along: `git remote add homelake https://github.com/pugwala/homelake.git`, then `git push homelake main` and `git push homelake duckdb-lakehouse`.
- `gh repo edit pugwala/homelake --description "..." --enable-wiki=false`

**Verified:** branch heads match on both repos, 55 commits reachable in each, only refs/heads/main and refs/heads/duckdb-lakehouse on homelake, CI green. The local origin still points to the old repo; homelake is a second remote.

## 2026-10-31 · MCP: list\_metrics tool (pushed, 370a7c8)

**Result:** the MCP server has a third tool, `list_metrics()`, that lists every metric `query_metric` offers, so an agent no longer has to guess names. Built test-first; 16 of 16 MCP acceptance tests pass. Pushed to duckdb-lakehouse as 370a7c8 (pugwala) at 5:44 PM CDT; both GitHub runs (tieback-check, lakehouse-ci) passed. The notebooks/03\_dates.ipynb outputs from Oct 27's instructor run were discarded at wrolfgar's choice, so course files still match main.

**What we found:** Cube's `meta` already carries what an agent needs per metric: `shortTitle`, `description`, `aggType` and the view's `meta.product`. The same name can sit in several views with different dimensions (`people_in_custody` is in `custody_population` and `custody_offenses`), so the list has one entry per metric per view. The server code is mounted read-only into the container, but uvicorn doesn't reload, so edits need `docker compose --profile core restart mcp` (never `up -d`, which starts load-lake).

**What we did:**

- Red: 3 new tests in `lakehouse/acceptance/test_mcp.py` (names match `query_metric`'s list; view, product and dimensions; `countDistinct` flags people counts) and the tool-list test changed to three tools. 4 failed with `Unknown tool: list_metrics`, 12 passed.
- Green: `list_metrics` in `lakehouse/mcp/server.py` returns a `MetricList` of `Metric` (Pydantic, so clients get structured output). Its description tells the agent never to add `countDistinct` values across groups. Module docstring, server instructions and `lakehouse/README.md` updated.
- `docker compose --profile core restart mcp`, then `docker compose --profile core exec -T jupyter pytest -q lakehouse/acceptance/test_mcp.py`.

**Verified:** 16 passed. A live call returned 19 entries across 7 views, 4 of them `countDistinct`. `tools/tieback_check.sh` clean; no tailnet names in the diff. `notebooks/03_dates.ipynb` was already modified before this work and is not part of it.

## 2026-10-28 · Dataset expansion: plan and decisions

**Why.** wrolfgar: the 100k dataset is too limited, the schema more than the size. Expand it to chronicle fights, locations, damages, powers used, charges, secondary heroes with weak or temporary powers, missions; resize the lab as needed; plan it in chunks. On size: it comes from the row count (`ROWS`); the seed only picks which random universe.

**Decisions (wrolfgar).** Lakehouse-only (the course stays unchanged); scale M (about 15M rows); the host has many TB (resize up to 2 TB as needed); nothing off-limits in the fiction. Keep $20 of usage credit for questions about the system, so I go one chunk at a time and stop for a go-ahead.

**Chunks.** 0 data model (for approval) · 1 resize the lab · 2 generator foundation (`lakehouse/universe/`, deterministic, chunked, vectorized, core 100k byte-identical) · 3 people, powers, places · 4 incidents (participants, power uses, damages) · 5 charges linked to offender records, missions · 6 mess with answer keys · 7 dbt layers, incremental · 8 meaning and rules · 9 products, Cube, dashboards, readiness inputs · 10 scale-up and benchmarks · 11 optional course sessions.

**VM today.**

- 8 vCPU, 31 GiB RAM.
- **Root disk:** 79 GB, 72% used. 32.8 GB of that is Docker's build cache, 30.9 GB reclaimable (`docker builder prune`, waiting for wrolfgar's OK).
- **`/lake`:** 200 GB ext4 on the whole disk `/dev/sda`, 1% used. It can grow online after a Proxmox resize; root `/dev/sdb1` can grow with `growpart` and `resize2fs`.
- **Proposed for M:** root 150 GB, `/lake` 1 TB, RAM 48 GB, 12 vCPU (wrolfgar to confirm RAM and CPU).

**Build cache cleared (wrolfgar: "clear docker build cache now").** `docker builder prune -f` freed 30.94 GB: the root disk went from 55 GB used (72%) to 29 GB (38%). Only cached build layers were removed; the next image rebuild will be slower.

**Chunk 1, disks done.**

- **Proxmox:** wrolfgar ran `qm resize` for VM 140: `scsi0` (root, `/dev/sdb`) to 150G and `scsi1` (`/lake`, `/dev/sda`) to 1T, and set cores 12 and memory 49152. The VM saw the new sizes only after a SCSI rescan (`echo 1 > /sys/class/block/sdX/device/rescan`; dmesg: capacity change).
- **Grown online:** `growpart /dev/sdb 1` and `resize2fs /dev/sdb1` (root: 148 GB, 20% used), then `resize2fs /dev/sda` (`/lake`: 1007 GB, 1% used).
- **Still pending:** RAM and CPU (the VM still shows 8 vCPU and 31 GiB) need a VM power cycle, `qm reboot 140` on the host. wrolfgar must do it, since Claude Code runs on this VM.
- **Snapshot:** `qm config` shows `parent: pre-anonymize`, so no new pre-resize snapshot was taken.

**Chunk 1 done: reboot and a fix.** After wrolfgar's `qm reboot 140`, the VM has 12 vCPU and 47 GiB RAM, and the disks kept their new sizes. `bootstrap.sh --check` failed: **Prometheus and Alertmanager hadn't restarted.**

- **What happened:** every container stopped at 00:46:09 UTC as Docker shut down; only these two stayed down.
- **Cause, confirmed:** `HasBeenManuallyStopped=true` in both containers' `config.v2.json` (false for Grafana and ntfy). Bootstrap reloaded their config with `docker kill -s SIGHUP`, and Docker counts any `docker kill`, even a reload signal, as a manual stop, so `restart: unless-stopped` skips the container at boot.
- **Fix:** both started by name (which clears the flag). Bootstrap now reloads from inside (`exec -T <svc> kill -HUP 1`); the bats test changed first (red), then green 61/61. Live: both logged "Completed loading", the flag stayed false, `bootstrap.sh --check` passed.
- **Pushed:** `bd1035c`; `tieback-check` and `lakehouse-ci` started from the push and succeeded. Memory: monitoring-quirks.

## 2026-10-27 · Ops hardening plan (wrolfgar away about a day)

**Why.** Asked what else the home lakehouse needs, I found:

- **Backups:** only the Postgres catalogs are dumped, onto the same `/lake` disk; the Parquet data (546 MB) isn't backed up at all.
- **Housekeeping:** none for DuckLake. Old snapshots and their files are kept forever.
- **Lineage:** none in OpenMetadata.
- **CI:** none beyond the employer guard.

wrolfgar: the Proxmox server runs TrueNAS, so back up there; he likes the housekeeping, the CI and the runbooks. "Can you chunk this up and get to it when you can get to it? I won't be in Claude much for the next day or so."

**wrolfgar's decisions (14:3x CDT).**

- **Commits:** push each chunk to `duckdb-lakehouse` once it's green (the same safe way); never to `main` without asking.
- **Retention:** 30 days of snapshots.
- **Backups:** to a TrueNAS **NFS** share.
- **Runbooks:** in the repo.

**Waiting on wrolfgar.** A TrueNAS dataset with an NFS share for this VM, `<vm-lan-ip>` (maproot root/wheel, NFS service on), then the TrueNAS IP and dataset path.

**Order.** 1 housekeeping, 2 CI, 3 runbooks, 4 backups (against a local folder until the share exists).

**Ops 1 done: DuckLake housekeeping (pushed `6540126`, 14:48 CDT).**

- **What the catalog showed:** DuckLake 1.5.6 has `ducklake_expire_snapshots`, `ducklake_cleanup_old_files` and `ducklake_delete_orphaned_files` (each with `dry_run`) and `ducklake_merge_adjacent_files`. There were 351 snapshots in 2 days, and only 18 of 320 files (38 of 571 MB) were live. `/lake/data` holds only lake Parquet files.
- **`housekeeping.py`:** expires snapshots older than 30 days, merges small files, deletes unneeded files after a day's grace and orphans older than a week; `--dry-run` only reports.
- **Schedule and alerts:** the Dagster job `lake_housekeeping` runs Sundays 03:30 Central and pushes `lakehouse_lake_snapshots`, `_live_bytes` and `_total_bytes`; the new `LakeHousekeepingStale` makes 23 rules.
- **Tests:** 8 acceptance tests, red first (no module). The deleting steps were tested on a scratch DuckLake: every snapshot down to the current one with today's data unchanged; a dry run changed nothing; a planted orphan was deleted.
- **Live:** after Dagster restarted, its definitions **loaded** (checked through GraphQL). The first run, 19d44482, succeeded: nothing to remove yet, as the lake is 2 days old.
- **Proof:** full acceptance 271, bats 56, `bootstrap.sh --check` passed, guard success.

**Ops 2a done: the CI checks script (pushed `369fce4`, 14:55 CDT).**

- **What it runs:** `lakehouse/ci/checks.sh`, 14 checks with no secrets and no running stack, on a copy of the working tree (never `.env` or dbt's `target/`). A virtualenv from the lakehouse's pins (`--uploaded-prior-to` the image's `PIP_CUTOFF`); compile, YAML, docstrings, ontology; bats 56; promtool, amtool, compose validation (dummy env, `-q`); a sandbox lake (load, readiness, `dbt build --target local`, 19 parity checks); and `dagster definitions validate`.
- **Results:** all green in 73 s.
- **Shown to fail:** a throwaway copy of the definitions with the `@multi_asset` `deps=` mistake put back failed validation with the morning's `DagsterInvalidDefinitionError` (exit 1).
- **Host change:** `python3-venv` installed on the VM so the script runs here as on a CI runner.

**Ops 2b ready, waiting for wrolfgar's OK.** GitHub only lets a workflow be started by hand if the file is on `main` (a course file), so the workflow `lakehouse-ci.yml` is committed on the **local** branch `pending/lakehouse-ci` (`8b74fc8`, off `origin/main`), not pushed.

- **Pins:** checkout v7.0.1, setup-python v7.0.0 (2026-07-20; v7.1.0 is 5 days old), ubuntu-24.04.
- **On the course branch:** it only says there's no lakehouse to check.
- **Lint:** actionlint 1.7.12 is clean on both workflows.
- **Once wrolfgar approves:** merge into `main`, push, merge `main` into `duckdb-lakehouse`, then `gh workflow run lakehouse-ci.yml --ref duckdb-lakehouse` and watch it.

**Ops 3 done: runbooks (pushed `2b78f11`, 15:08 CDT).**

- **The pages:** `lakehouse/runbooks/<AlertName>.md` for all 23 alerts, plus an index. Each has four sections (what it means, what to check, how to fix it, when it clears), copy-pasteable commands, and `<LAKE_TS_HOST>` placeholders.
- **The links:** every rule has a `runbook_url` to its page on GitHub (checked: 200), and ntfy's template ends each notification with a `Runbook:` line. ntfy ignores `click:` in a template (tested), so the link is message text.
- **Tests:** 7 in `test_runbooks.py`, red first. The end-to-end alert test now requires `runbooks/JobFailing.md` in the notification, and passed.
- **Proof:** full acceptance 278, CI checks all green; the employer and Tailscale/LAN scans of the staged diff were clean; guard success.

**Ops 4 done, local target for now: off-machine backups (pushed `541c028`, 15:24 CDT).**

- **The service:** `offsite-backup` (restic 0.19.1, 2026-07-05), `backup/offsite.sh` in BusyBox `sh`. It runs nightly at 02:30 Central and backs up `/lake/catalog-backups` and `/lake/data` (both read-only) into an encrypted repository on `BACKUP_TARGET`, `/mnt/lakehouse-backups`. Retention 7 daily / 4 weekly / 6 monthly; `restic check` nightly.
- **The monthly drill:** `check --read-data`, then restore the latest snapshot and compare every file with its original.
- **The marker:** `.lakehouse-backup-target` (`local` or `truenas`) is required. `bootstrap.sh` prepares a local folder, warns that it isn't off the machine, and fails `--check` if a marker is missing.
- **The password:** `RESTIC_PASSWORD` was generated into `.env` and reaches the service as a Compose secret. The restic settings are in the service's environment, so `exec offsite-backup restic` works.
- **The full drill:** `backup/restore_drill.sh` restores the latest snapshot, puts its newest catalog dump into the scratch database `ducklake_drill` (grants for `lake_rw`), runs the 19 parity checks in a throwaway `lnl-jupyter` container with the restored files mounted read-only at `/lake/data`, and always cleans up. Its 6 bats tests are in CI.
- **Alerts:** OffsiteBackupStale, OffsiteBackupFailed, RestoreDrillStale and RestoreDrillFailed, with runbooks (27 rules).
- **Results:**
  - first backup: 330 files, 550 MiB down to 126 MiB, 8 s;
  - first drill: all 330 restored files identical;
  - full drill: catalog 20261027T070000Z (263 snapshots) restored, 19 parity checks passed, scratch database and files removed, 3.7 s.
- **Proof:** tests red first (5 acceptance, 5 + 6 bats). Then acceptance 284, bats 67, CI checks green, `bootstrap.sh --check` passed (with the local-backup warning), guard success. Staged-diff scans for Tailscale, the LAN address, banned words and secret values were clean.
- **Also fixed:** compose's Alertmanager comment still said alerts go to "undecided".

**Ops 2b done: CI live on GitHub (16:27 CDT).** wrolfgar: "push the ci workflow".

- **The push:** `pending/lakehouse-ci` was a fast-forward of `origin/main` (2bbf5f4) and was pushed as `main` 8b74fc8 (the workflow file only; author pugwala). It was merged into `duckdb-lakehouse` as `f6fa5a6`; the course files match `main`; the local guard was clean.
- **First runs:** `lakehouse-ci` on `duckdb-lakehouse` ran all 14 checks on an ubuntu-24.04 runner, all ok, in about 2.5 minutes. On `main` it reported "No lakehouse/ on this branch". `tieback-check` succeeded on both.
- **News:** **push-triggered runs now start** (`event=push`), the first ever on this repo. `81463ef` (a README note that CI runs on GitHub) confirmed it: `tieback-check` and `lakehouse-ci` both started from the push and succeeded. Memory updated. The workflow's own comment, "GitHub starts no runs from pushes", is now outdated; it's a course file, to fix next time `main` is touched.

## 2026-10-27 · Class workspace can't see the course volume (10:56 CDT)

**What wrolfgar reported.** The cleanup notebook still says the volume is missing ("ask your instructor to create it"). That is the **earlier** version's message, so that copy hadn't pulled 2bbf5f4 yet; the advice was Git folder → Pull.

**Diagnosis given.** The volume really isn't visible from the lab cluster. I can't see the workspace, so I gave wrolfgar one cell to paste. It prints the cluster's access mode (`spark.databricks.clusterUsageTags.dataSecurityMode`), the catalogs, the volumes in `workspace.default`, and whether `/Volumes` exists. Matching fixes:

- **Not Unity Catalog–enabled** (No isolation shared): set the access mode to Standard or Dedicated.
- **Catalog isn't named `workspace`:** a one-line change to `lnl/config.py`.
- **Volume missing or misnamed** (it must be exactly `lunch_and_learn`; wrolfgar's message read `lunch_andlearn`): `CREATE VOLUME IF NOT EXISTS workspace.default.lunch_and_learn`.
- **No permission:** `GRANT READ VOLUME, WRITE VOLUME` to account users, plus `USE CATALOG` and `USE SCHEMA`.

**For 11:00.** Class doesn't need the volume: without it, `lnl` uses the cluster's local `/tmp/lnl_data`; DATA\_VERSION 6 means no stale cache can be reused; and a workspace that never had the volume never had an old cache in it. On a shared cluster, wrolfgar should run notebook 2's first cell before class, so the dataset is built once.

**Offered after class.** Make the cleanup notebook run this diagnosis itself and print the specific fix.

## 2026-10-27 · Cleanup notebook: start the lab cluster first (uncommitted)

**Result.** `clearing-out-the-old` now starts with starting the lab cluster and attaching the notebook to it, and it refuses to run against the wrong folder. Tested; waiting for wrolfgar's OK to push (10:48 CDT).

**Why.** wrolfgar: "the cleaning out the old needs to stipulate spinning up the lab cluster so the notebook can find the /Volums/workspace/default/lunch\_and\_learn".

**What I found.** Without the cluster attached, the volume isn't visible, and `lnl.env.data_dir()` silently falls back to `/tmp/lnl_data`. The old version printed a ⚠️ about the volume but also two misleading ✅s about the temporary folder.

**What changed.**

- **Step 1** now opens with: start the lab cluster (Compute; a cold start can take 5 minutes or more), and attach this notebook with the compute menu.
- **Step 2** explains why the cluster matters.
- **The cell's new step 0:** if the volume isn't visible, it prints one ⚠️ with the fix and does nothing else.
- **No Spark on Databricks** now gives a ⚠️ pointing at the cluster, instead of "Not on Databricks".
- **Troubleshooting** names the cluster first.

**What verified it.** Three cases in throwaway course-image containers:

- **A**, Databricks without the volume: only the ⚠️, and the planted files in the temporary folder were untouched.
- **B**, Databricks with the volume: cleaned it and built v6. Its Git-folder ⚠️ is a simulation artifact (no Databricks credentials).
- **C**, outside Databricks: All clear.

The notebook validates under nbformat with no outputs; the employer guard and Tailscale scan are clean. Memory: course-lab-cluster.

**Pushed (10:52 CDT).** wrolfgar: "push it". `2bbf5f4` on `main`, merged into `duckdb-lakehouse` as `b31feb0`; the course files match `main` (0 differ). The tieback hook was clean, and the guard Action succeeded on both branches. Author pugwala.

## 2026-10-27 · Plan's architecture drawing brought up to date

**Result.** The architecture drawing in the DuckDB Home Lakehouse Plan now shows the lakehouse as built (07:04 CDT).

**Why.** wrolfgar: "update the lakehouse plan architecture drawing if it's changed". It had: the drawing dated from October 24.

**What changed in the drawing.**

- **Alerts:** PagerDuty became Monitoring (Prometheus, Grafana, Alertmanager), with ntfy alerts to wrolfgar's phone.
- **Fuseki** has its own box: SKOS, DCAT, the rulebook, SHACL, deductions.
- **Gold** became Gold and marts (custody, readiness).
- **New boxes:** Business inputs (`inputs/`, `depends_on`, closes) and Ops (load runs, inputs, closes).
- **Consumers:** Jupyter shows `%sql` as `lake_ro` and SPARQL; MCP adds readiness; Superset shows two dashboards; the direct attach is marked read-only.
- **Bands:** the Dagster band names the 05:00 steps; the subtitle says everything is reached only on the tailnet through Caddy.

The redraw kept the text ids wherever the words still apply. It validated with no diagnostics, and the screenshot was checked (nothing overlaps or is cut off). The sentence under the drawing and its caption were updated too.

**Not updated.** The rest of the plan (the phase sections, the gaps table, the open questions) still reads as of October 24.

## 2026-10-27 · Cleanup notebook and DATA\_VERSION 6, pushed

**Result.** `notebooks/clearing-out-the-old.ipynb` is on `main` for the group, and `DATA_VERSION` is 6, so a stale cache can no longer break session 2. Both branches were pushed and both guards passed by 06:14 CDT.

**Why.** wrolfgar asked for a notebook that runs the cleanup script ("None of these folks write Python"). Then, asked two questions, he chose "Push it" and "Yes, bump it" (DATA\_VERSION 5 → 6).

**The notebook.** Markdown steps by hand (save your answers, move the old Git folder to Trash and empty Trash, clone the new copy), then **one cell to run**, which prints a ✅ or ⚠️ checklist:

- **Old data:** removes cached dataset files that aren't the current version or whose record key isn't `offender_number`; keeps anything new.
- **Old table:** drops the session 5 table only if its key is old.
- **Leftover copies:** names any other Git folder of the course (Databricks SDK `repos.list`).
- **Fresh data:** builds the dataset and checks its header.

It ships without outputs, with cell ids like the other notebooks, and nbformat validates it. Its name doesn't start with `0`, so the weekly smoke run never executes it. I spelled the name `clearing-out-the-old` (the request said "cleearing"); easy to rename.

**What verified it.** I ran `main`'s code in a throwaway `lnl-jupyter:local` container with the worktree mounted read-only, against a stale data dir (old v5 CSV, its answer key, an unrelated file):

- notebook 2 **with the stale cache left in place**: 31 cells, 0 errors (it built v6);
- notebook 1: 14 cells, 0 errors;
- the cleanup notebook, twice: the first run removed 2 old files and kept v6, the unrelated file and session 2's outputs; the second found nothing to do.

The earlier version deleted fresh data on a second run; that was fixed before committing. **Not tested:** the Databricks-only parts (the table drop, the Git folder listing). They are wrapped so a failure prints a ⚠️ with what to do by hand.

**Commits.**

- `bc9b92e` on `main` (notebook, README line, DATA\_VERSION 6); guard success.
- Merged into `duckdb-lakehouse` as `5c27805`; course files match `main` (0 differ); guard success.

**Lakehouse on v6.** The 05:00 run (f858186f) succeeded; it was the first scheduled run with readiness. The manual run 1ed94fd4 loaded bronze from `hero_offender_data_v6_s2026_r100000.csv` (`_data_version` 6, 100,000 rows). Full acceptance 263, bats 56, 19 parity checks, `bootstrap.sh --check` all passed.

## 2026-10-27 · Re-clone instructions; a stale data cache would break session 2

**Result.** wrolfgar has instructions for the group to delete their old copies and re-clone. On the way I found that **an old cached CSV breaks notebook 2** (`KeyError: 'offender_number'`), and re-cloning alone doesn't fix it (04:54 CDT).

**Why.** wrolfgar asked how to have the group re-clone so their copies of the banned words are gone.

**Where old copies live.**

- **The Databricks Git folder and its history.** The repo URL is the same, but the history is new, so Pull won't remove the old commits. Delete the folder, empty the Trash, and create the folder again.
- **The cached generator CSVs** in `/Volumes/workspace/default/lunch_and_learn` (`hero_offender_data_v5_s2026_r100000.csv` and `_answer_key.csv`).
- **Session 5's Delta table** `workspace.default.hero_offenders_clean_<user>`, whose history keeps old versions, so it must be dropped. Also any forks, downloads and old handout PDFs.

**Found: the stale cache.** The old repo also used `DATA_VERSION = 5`, so an old cache file has the same name and the new code reuses it. Its header is the old record-key name (the backup has the interim `id_number`; earlier clones have the original, banned name).

- **Reproduced** in a scratch `LNL_DATA_DIR`: a CSV with an `id_number` header makes `cleaning.session2` fail with `KeyError: 'offender_number'`. Scratch removed.
- **Fix options:** attendees delete the cache (in the instructions), and/or bump `DATA_VERSION` to 6 on `main` so a stale cache is never reused. The bump is awaiting wrolfgar's OK.

**Slip, cleaned up.** I fetched `~/lnl-backup.git` into a local-only ref to compare the generators. It was never pushed, and I deleted it right after. The diff was checked for banned words first (0) before printing.

## 2026-10-27 · Notebook 2 checked for the 11:00 lesson

**Result.** `02_cleansing.ipynb` runs cleanly; nothing needed fixing (checked 04:43 CDT).

**Why.** wrolfgar: the second lesson is taught at 11; fix notebook 2 if it no longer runs.

**What verified it.**

- The course files are identical to `main`: `git diff origin/main HEAD` over `lnl`, `notebooks`, `generator`, `requirements.txt`, `FACILITATOR_GUIDE.md`, `README.md` and `.github` shows 0 files.
- Papermill ran the notebook in a fresh kernel in the lakehouse Jupyter: 31 of 31 code cells, 0 errors, nothing on stderr, in 9 s (output to a temporary folder, not the repo).
- The 19 parity checks against the Facilitator Guide passed in this morning's `bootstrap.sh --check`.

**Limit.** This was tested in the lakehouse Jupyter only, not in Databricks or on attendees' machines; the files are unchanged from `main` there too.

## 2026-10-27 · Data readiness: is this month's number final yet? (uncommitted)

**Result.** Each custody product's number for each month-end is now **final** or **provisional, waiting on** a business unit, live, everywhere people query it. A teaching guide covers it. All green at 04:33 CDT; not committed.

**Why.** wrolfgar clarified what he meant by business rules: data has meaning at a given moment only once several asynchronous systems and business units have done their part, and without those inputs the queried value is wrong. He asked for both the write-up and the build ("do both please"), and then said he needs to "teach others how to do it". So everything a person adds is a file, with no code.

**Write-up.** The ontology how-to has a new section, "Data readiness: is this number final yet?". It covers period close; the difference between fresh, complete and correct; the model; how it works here; a six-step recipe; a 30-minute exercise (including the trap of adding an input without closing its history); common mistakes; and a map of which file does what.

**What we built.**

- **Inputs:** `products/inputs/{records,classification,courts}.yml` (fictional units Records, Classification and Courts liaison, closing within 5, 10 and 7 days).
- **Dependencies:** `depends_on:` in both descriptors (Population: records + classification; Offenses: records + courts).
- **`readiness/closes.py`:** `sync` (files to `ops.business_inputs` and `ops.product_inputs`), `report` (append to `ops.input_closes`; the latest report wins, so an earlier date reopens a month), `simulate` (the fictional units close on day 3, 5 and 8), and `status`.
- **dbt:** the view `mart_readiness.period_readiness`. A view, so a close shows on the next query. It has a dbt test for one row per product per month; `om_sync` now catalogs `mart_readiness`.
- **Cube:** hidden readiness cubes joined to the snapshot by month-end; `period_status` and `waiting_on` in both product views; a public `period_readiness` view; a `meta.product` tag on each product view.
- **MCP:** `query_metric` adds `readiness` (the latest month-end, plus every month still provisional, with who it waits on) for a product's metric.
- **Superset:** a "Period status by month-end" chart at the top of Custody.
- **Daily run:** a `readiness_inputs` asset (sync, simulate, and `lakehouse_input_days_late` pushed per input). `data_products` pushes `lakehouse_product_latest_period_final`.
- **Alert:** `BusinessInputLate` (22 rules).
- **Ontology:** `graph/readiness` (`lh:BusinessInput`, `lh:dependsOn`); SHACL shapes `ProductInputsShape` and `InputShape` (4 shapes now); a rulebook rule.
- **Bootstrap:** runs `closes.py sync` (or `--check`).

**What I checked first.** DuckLake stores views that `lake_ro` can read (tested in a scratch schema, then dropped).

**Found on the way.**

- Cube refuses a cube and a view with the same name, so the hidden cube is `all_readiness`.
- **Dagster failed to load the definitions** after my first edit: this version rejects `deps` beside `specs` on a `@multi_asset`. Compiling the file didn't catch it; querying the code location through GraphQL did. It was fixed at 04:27 CDT, before the 05:00 run. The deps now sit on each AssetSpec.

**What verified it.** Tests first, seen red (bats: bootstrap didn't sync; acceptance: no inputs). Then green:

- `test_readiness.py`: 13, including the live flip. Classification reopened September, Custody Population went provisional, waiting on Classification, in the lake and in Cube; Offenses stayed final; closing it made it final; the test's reports were deleted after.
- `daily_lake` 38b54419 succeeded.
- Full acceptance 263, bats 56, `bootstrap.sh --check` all passed, guards clean.
- The guide's exercise query was run through Cube: 81,409 people for September, final.

**Next.** wrolfgar approves the commit.

**Pushed (04:40 CDT).** wrolfgar: "commit". Three commits on `duckdb-lakehouse`, made the same safe way. The plan placed 58 hunks and 8 new files, each used once, and the last commit matched the working tree; only `test_readiness.py` was split (A had its 7 core tests, B all 13).

- `d905f7f` Readiness: business inputs, closes and the period\_readiness view
- `0fe32fd` Readiness: in Cube, MCP, Superset, alerts and the ontology
- `0ffb394` Readiness: README

Each snapshot passed compile, YAML, compose, promtool (21, 22, 22 rules), amtool, bats 56, docstrings, the Tailscale and employer scans, and the tieback hook. Author and committer are pugwala. Guard Action dispatched by hand: success on 0ffb394.

## 2026-10-27 · iPhone relay on; ntfy and business rules pushed

**Result.** Five commits pushed to `duckdb-lakehouse` by 03:46 CDT; the guard Action passed on d2fbb9d. ntfy now relays iPhone wake-ups through ntfy.sh.

**Why.** wrolfgar: "do the commits and I have an iphone 17". Asked about the relay, wrolfgar chose **"Turn it on"**.

**iPhone relay.**

- **The setting:** `upstream-base-url: "https://ntfy.sh"` in `ntfy/server.yml`, test first: `test_iphone_wakeups_relay_through_ntfy_sh_without_the_alert` was red with `KeyError`, then green, so `test_ntfy.py` has 8 tests.
- **Why it's needed:** iOS wakes an app only through Apple's push service, so ntfy forwards each message's ID and a SHA-256 hash of its topic URL to ntfy.sh, never the text. The app then fetches the alert from this server over Tailscale.
- **Verified:** the ntfy container reaches ntfy.sh. With debug logging switched on for a moment (then back to info via SIGHUP), a message to `lakehouse-selftest` logged `Publishing poll request to https://ntfy.sh/<sha256>`.
- **README:** iPhones need Tailscale's VPN On Demand.

**Commits (the same safe way).**

- **Method:** a plan script split 68 hunks and 8 new files across five commits, using each hunk exactly once; the last commit matched the working tree byte for byte. Mixed lines got earlier versions: the `RULES` set, Compose's secrets block, the README rule and bats counts, and the heartbeat and Prometheus tests.
- **Snapshot checks:** each commit's snapshot passed compile, YAML, `compose config -q`, promtool (19, 20, 20, 20, 21 rules), amtool, bats (53, 53, 53, 53, 55), docstrings, the Tailscale and employer scans, and the tieback hook.
- **The commits:**
  - `d0f5d6e` Alerts: ntfy, self-hosted on the tailnet
  - `021b89c` Alerts: Alertmanager delivers to ntfy
  - `7ba7a40` Alerts: README for ntfy
  - `2ba9720` Ontology: business rules
  - `d2fbb9d` Ontology: daily business-rule check and alert
- **Identity and guard:** author and committer are pugwala with the no-reply address. Guard Action dispatched by hand: success on d2fbb9d.

**Next.** wrolfgar sets up the ntfy app on the iPhone (README, On the phone); then a test notification to `lakehouse-alerts`.

**Phone verified (04:00 CDT).** wrolfgar set up the ntfy app on his iPhone 17 and subscribed to `lakehouse-alerts` ("subscribed").

- **The test:** at 03:57 CDT I posted a made-up critical alert, `LakehouseTestAlert` (ending after 2 minutes), to Alertmanager's API, so it took the full path: route, `password_file` login, lakehouse template, ntfy, iPhone relay.
- **On the server:** it reached `lakehouse-alerts` at 03:58:02 CDT as "🚨 Firing: LakehouseTestAlert" at priority 4, with 0 failed notifications.
- **On the phone:** wrolfgar confirmed it arrived ("got it").
- **Still to come:** the low-priority Resolved notice follows on Alertmanager's next 5-minute group interval.

Alert delivery is done end to end.

## 2026-10-26 · Business rules in the ontology (uncommitted)

**Result.** The ontology now holds rules as well as facts: a rulebook, a deduction and SHACL constraints. A daily check feeds the new alert. All green at 20:27 CDT; not committed.

**Why.** wrolfgar asked "how do i add business rules and logic to the ontology", then said "yes" to building three examples and documenting them.

**wrolfgar's decision.** The deduction found that `sid_number` (6 tables, including the custody product's snapshot) has no sensitivity tag. The project already treats a SID as a key, not personal data, yet keeps it out of every Cube view. Asked how to model that, wrolfgar chose **"Pseudonymous key"**: a new class `lh:Pseudonymous`, allowed in tables for joining and counting, never exposed to a consumer.

**What I checked first.**

- Fuseki holds facts only: there was no reasoner in `config.ttl`.
- The Fuseki 6.2.0 jar includes SHACL (`ShaclValidator`, the `SHACL_Validation` servlet) and `GenericRuleReasoner`.
- With a new `shacl` endpoint, `graph=union` validates every graph at once.
- The shortest definition is 92 characters, so 40 is the minimum.
- No public Cube member is `sid_number`.

**What we built.**

- **Rulebook:** a `rules:` section in `glossary.yml` (5 rules). `om_to_rdf.py` publishes them as `lh:BusinessRule` in `graph/rulebook` (29 triples). Each `enforced_by` (`cube:`, `dbt:`, `prometheus:`, `shacl:`, `sparql:`, `test:`) must exist.
- **Deduction:** `ontology/rules/identifier-of-a-person-is-pseudonymous.rq`. `om_to_rdf.py` runs every rule file until nothing new appears, and writes each rule's facts to `graph/inferred/<name>`: 6 facts, one per `sid_number` column. An inferred graph whose rule file is gone gets deleted.
- **Constraints:** `ontology/shapes.ttl` with `TermShape` (one name, a definition of 40 or more characters) and `RuleShape`. Property shapes are named, so a violation can be traced to its rule.
- **Checker:** `ontology/check_rules.py` posts the shapes to Fuseki's new read-only `/shacl` endpoint (`fuseki/config.ttl`). Fuseki was restarted; its data is on `/lake`.
- **Daily run:** a non-blocking `business_rules_hold` check on `fuseki/glossary` pushes `lakehouse_business_rule_violations{shape}`. The new `BusinessRuleViolated` rule makes 21 rules.
- **Bootstrap** runs `check_rules.py` in both modes and fails on a violation.
- **Docs:** README ("Business rules in the ontology") and a new Business rules section in the ontology how-to doc.

**What verified it.** Tests first, seen red: 2 bats; the acceptance file stopped on `KeyError: 'rules'`. Then green:

- `test_business_rules.py`: 12, including a "TBD" definition in a scratch graph that broke `TermShape`, and an orphaned inferred graph that `--check` flagged and the next load removed.
- `daily_lake` 092bc7e7 succeeded, with `business_rules_hold` passing.
- Full acceptance 248, bats 55, `bootstrap.sh --check` all passed, employer guard and Tailscale scan clean.

**Found on the way.** The first violation report named its shape "?": SHACL reports the anonymous property shape, and the report doesn't say which named shape contains it. Fixed by naming the property shapes and looking up their parent in our own `shapes.ttl`.

**Next.** wrolfgar approves the commit.

## 2026-10-26 · "do all": ntfy alerts, two stale items closed, two rechecks (uncommitted)

**Result.** Alerts now reach a self-hosted ntfy on the tailnet, ready for wrolfgar's phone. Two "Up next" items turned out to be done already. DuckDB 2.0.1 and GitHub code search still have to wait. All green at 20:07 CDT; not committed.

**Why.** wrolfgar: "do all" (the what's-next list). The alert channel was wrolfgar's choice: "ntfy, self-hosted".

**Rechecks.**

- DuckDB: PyPI has only 2.0.1.dev2610211350 (2026-10-22), so 2.0.1 isn't out and the upgrade still waits.
- GitHub code search: the control word `offender_number` finds 0 hits in the repo, and `duckdb` and `README` find 0 too. The repo (created 2026-10-26 03:23 UTC) isn't indexed yet, so a banned-word search would prove nothing.
- Sessions 6 and 7 (spaCy `OverflowError`): no longer happens. `load_spacy()` loads and lemmatizes. In the latest `notebook_smoke` run (e5dd98d8), notebooks 06 and 07 ran every cell with 0 errors, spaCy cells included. It was fixed when the Phase 7 pins rebuilt the image. Ticked.
- Phase 4 slice 3 (`%sql` as `lake_ro`): already done as `lakehouse/sql_magic.py` (6 acceptance tests, used by 08\_from\_lake). Ticked.

**What I found first (ntfy, tested in throwaway containers before building).**

- Alertmanager v0.34.1 has no native ntfy receiver (amtool rejects `ntfy_configs`), so it uses its webhook.
- ntfy 2.30.0 (2026-10-12, the newest at least 2 weeks old) refuses a base URL with a path, so it gets port 8443 on the Tailscale name.
- ntfy declares users and access in config (deny-all; publish-only and read-only users verified as 403/200/401). Its built-in alertmanager template works, but **ntfy drops any priority passed with the request once a template is in use**. A named template file can set the priority, so priority comes from severity in our own template.
- Alertmanager shows webhook URLs as `<secret>` in its status API. Compose turns an `.env` variable into a `/run/secrets` file (`secrets: … environment:`) that the non-root Alertmanager can read as a `password_file`.

**What we built.**

- **`ntfy` service** (v2.30.0, uid 1000, data on `/lake/ntfy`, no host port). It is configured by `ntfy/server.yml` (deny-all, `lakehouse-*` access) and `ntfy/start.sh`, which hashes the three `.env` passwords at start: `alertmanager` publishes; `<owner-user>` and `checker` only read.
- **Caddy** serves `{$LAKE_TS_HOST}:8443` with the same Tailscale certificate.
- **Alertmanager** has three receivers: `lakehouse-alerts` (the phone), `lakehouse-heartbeat` (Watchdog, every 4 hours) and `lakehouse-selftest` (the test alert, with fast timings), all `?template=lakehouse`.
- **Template** `ntfy/templates/lakehouse.yml`: critical while firing is 4, warning 3, resolved 2, Watchdog 1.
- **Prometheus** now scrapes Alertmanager and ntfy; there is a new `AlertDeliveryFailing` rule (20 rules), and blackbox probes ntfy's health URL.
- **Bootstrap** generates `NTFY_ALERTMANAGER_PASSWORD`, `NTFY_IAN_PASSWORD` and `NTFY_CHECKER_PASSWORD`, creates `/lake/ntfy`, starts 21 services and checks `:8443/v1/health`.

**What verified it.** Tests were written first and seen red: 11 acceptance and 4 bats, for the right reasons. Then green:

- `test_ntfy.py` 7, including a Watchdog heartbeat that arrived at priority 1.
- `test_alerting.py` 9. A failed `monitoring_selftest` reached ntfy on the selftest topic at priority 4, its resolved notice at 2, and nothing reached `lakehouse-alerts`.
- Full acceptance 237, bats 53, `bootstrap.sh --check` all passed, employer guard and Tailscale scan clean.

**Found on the way.**

- One routing test assumed it could read webhook URLs from the running config (they show as `<secret>`); it now reads them from the file and checks the running config has the same routes and receivers.
- The full suite caught `silver/hero_offenders` rebuilt by a run started from the Dagster UI at 19:36 CDT (b06ab92d), after the latest daily run. I launched `daily_lake` (e0cd68d8, SUCCESS), then reran: green.

**Next.** wrolfgar sets up the phone app; then a test notification to `lakehouse-alerts`; wrolfgar approves the commit.

## 2026-10-26 · Superset Custody dashboard (uncommitted)

**Result.** A published **Custody** dashboard (`/superset/dashboard/custody/`) with four charts on the custody data products' Cube views; all checks green at 19:35 CDT; not yet committed.

**Why.** wrolfgar: "same safe way and yes" (the yes: build the Superset dashboard on the custody views next).

**What we built.**

- Cube: a new `is_latest_month_end` boolean dimension on the hidden `custody_snapshot` cube, in both `custody_population` and `custody_offenses`. Charts can show "now" without a hard-coded date, and move on by themselves when a month completes. Test first (`test_latest_month_end_flag`, seen red, then green).
- `superset/dashboards.py` made generic: each dashboard is one dict in `DASHBOARDS` (title, slug, intro, charts, rows), with chart builders `trust_table`, `monthly_line` and `latest_table`. Chart metrics are Cube's own measures written as `MEASURE(people_in_custody)`, so people stay distinct SIDs counted by Cube. The Trust Test keeps its old layout ids, so its live dashboard still compared "up to date" and was not rewritten.
- Charts: people in custody by month-end (line); people by custody level and by offense category at the latest month-end (tables); new sentences per month (line, on `custody_admissions`).
- The summary line is now short: `Superset dashboards (Trust Test, Custody): in place`, or `needs Custody (n of 12 objects)`.

**What verified it.** `test_superset.py`: 8 of 8 (the two custody tests were red before the dashboard existed). They check that the 4 charts read only the product views through the Cube database, that 2026-09 shows 81,409 people and 1,557 new sentences, and that both latest tables equal Cube's own SQL answer. `--check` exits 1 on an in-memory layout change. Full acceptance suite: 227 passed. bats 51, the employer guard and the Tailscale scan are clean. `bootstrap.sh --check` printed All checks passed.

**Found on the way.** The first full run had 1 failure: `test_run_materialized[fuseki/glossary]`. I had materialized `fuseki/glossary` by hand at 19:24 CDT, after the 19:04 `daily_lake` run, so the latest daily run no longer owned it. That was not a code bug. I launched `daily_lake` (9925a6de, SUCCESS), then reran the suite: green.

**Next.** wrolfgar approves, then a commit split the same safe way (Cube flag + its test; dashboard script + tests + docs).

**Pushed (19:38 CDT).** wrolfgar: "yes". Two commits on `duckdb-lakehouse`, made the same safe way (index staged from prepared copies, each snapshot checked, author pugwala): `64b4d4c` Cube latest month-end flag (custody.yml, its test, the README count) and `8bc899d` Superset Custody dashboard (dashboards.py, test\_superset.py, README, bats stub). Snapshot checks: compile, yaml, bats 51, docstrings 2, employer guard and Tailscale scan clean. Guard Action dispatched by hand: success on 8bc899d.

## 2026-10-26 18:56 CDT: data products, chunks 1 to 3 (person, custody mart, Cube views)

**Why.** wrolfgar: "do custody population and custody offenses. is it worth modeling what is an inmate/human/person?" Measured first: 100,000 records belong to 86,879 people (SID), 2,997 records have no SID, 8,499 people have several records, and 1,008 pairs of one person's records overlap in time, so a record-based headcount double counts. wrolfgar chose the recommended person model and month-end snapshots.

**Chunk 1, Person (test first: 8 acceptance tests, 6 dbt tests).** Glossary term Person (synonyms person, individual, inmate, offender: roles, not entities), SID Number identifies Person, Offender Record isAbout Person; `om_sync.py` registers the custom isAbout / subjectOf relation types. `gold.dim_person`: one row per known SID with derived facts only (record\_count, first and latest sentence date, is\_repeat, has\_concurrent\_records), no personal data; a dbt test checks every SID record is counted once. Reaches OpenMetadata, Fuseki and the MCP server (`define_term('Inmate')` gives Person).

**Chunk 2, the custody mart (test first: 7 acceptance tests, 3 dbt tests).** New schema `mart_custody`: `custody_snapshot_monthly`, a periodic snapshot (one row per record per open month-end, 4.24 M rows, Oct 1996 to Sep 2026), carrying the SID so people are counted distinct at query time; people counts are never stored because they don't add up. `snapshot_coverage` states what's left out (5,860 records with no sentence or release date). Both have enforced dbt contracts; a deliberate type change to `month_end` was refused by dbt. Dagster now names dbt assets by their schema (`mart_custody/...`), and `om_sync.py` reads each dbt folder's schema from `dbt_project.yml` (it had assumed every model was gold, so the mart tables first arrived without descriptions).

**Chunk 3, Cube (test first: 9 acceptance tests).** A hidden `custody_snapshot` cube and three views: `custody_population` (by unit and level), `custody_offenses` (by offense) and `custody_admissions` (new sentences, from `offender_records` with aliased `admissions` / `people_admitted`, plus a new `people` measure). On 2026-09-30: 84,106 open records, 81,409 people; by unit the people sum to 81,413, because 4 are held in two units at once, which proves the distinct count works. No view has a restricted or personal member. The MCP server's `query_metric` now picks the view that has both the metric and the dimensions asked for (`people_in_custody` is in two views). My unit test first assumed every group had a unit name; the nameless one is the 2,611 people whose unit couldn't be mapped. Uncommitted.

**Chunk 4, descriptors, OpenMetadata and Fuseki (19:02 CDT, test first: 10 acceptance tests).** One file per product in `lakehouse/products/` (custody-population, custody-offenses) holds the whole promise: domain, owner, question, the tables it delivers (none may hold a restricted or personal column), the tables its data comes from (`sources`, kept apart because admissions come from the fact table through a view that exposes none of its sensitive columns), Cube views, glossary terms, refresh and a 26-hour freshness promise; domains live in `products/domains/`. `om_sync.py` publishes them: the Custody Operations domain (Consumer-aligned), both Data Products (custom properties for question, views and terms), and a Data Contract on each delivered table with a dbt-enforced contract (dbt's columns and the SLA). `om_to_rdf.py` adds them to Fuseki as DCAT datasets (835 triples), so "which products does a change to Person touch?" is one query (both).

- What OpenMetadata 2.0.5 taught me, each from its own spec or error: SLA units are lowercase and the timezone must be its label `GMT-06:00 (America/Chicago)`; a contract's FQN hangs off its table (`<table>.dataContract_<name>`); a create body's `assets` are ignored, so assets go through the bulk add/remove endpoints; and a product's assets must sit in its domain, so `om_sync.py` now adds the domain to each delivered table (keeping any others). `--check` is in step after a sync.
- Shown to bite: a made-up Cube view in a descriptor fails the descriptor test; the governance query finds restricted columns when pointed at the source table.

**Chunk 5, product health (test first: 4 acceptance tests, 1 dashboard check).** New asset `monitoring/data_products`, right after the marts in `daily_lake`, pushes per product: refreshed time, max age from its descriptor, the snapshot's coverage (5,860 of 100,000 records undatable) and the population headline (81,409 people, 84,106 records). Rules `DataProductStale` (each product's age against its own promise, so a new product needs no new rule) and `DataProductCoverageLow` (over 10%; 5.9% today); 19 rules, promtool passes. Home Lakehouse gained a Data products row (4 panels; the every-panel-has-data test covers them). Live: a 30-hour-old refresh pushed for custody-population fired `DataProductStale`, and restoring the real time cleared it.

**Chunk 6, docs (19:15 CDT).** README: a Data products section (the promise and where each part lives, the two products, people not records, how to add a product), file and table rows (`products/`, `gold.dim_person`, the mart), the daily-run diagram, 15 glossary terms, test-status rows. The ontology how-to doc: new counts (15 terms, 194 columns, 23 tables, 2 products), a vocabulary note on products and `isAbout`, recipe 9 (which products a change touches), and recipe 6's answer re-run (now 7 columns, the mart included). Memory note `data-products`.

**Totals (19:15 CDT).** Acceptance 224 in one run, dbt 42 passing + the expected `dq_score_floor` warning, parity 19, bats 51, guard clean, no Tailscale strings, course files identical to `main`, `bootstrap.sh --check` all green (OpenMetadata, Fuseki and Cube masks in step). Uncommitted.

**Pushed (19:21 CDT).** wrolfgar: "same safe way and yes". Six commits on `duckdb-lakehouse`, one per chunk, pugwala: 0bab8ff (person), efc2d38 (custody mart), 06b14d9 (Cube views), 500e0ba (descriptors, OpenMetadata, DCAT), 8c0d594 (freshness and coverage alerts), 7a8e38d (README). This time shared files (`om_sync.py`, `definitions.py`) were split by git's own diff hunks: each hunk assigned to exactly one chunk (the script refused unassigned or doubly assigned hunks), applied to HEAD by line number, so no text was retyped; `test_products.py` split at its health section. Each snapshot checked on its own: Python compiles, YAML parses, compose valid, promtool, docstrings complete, bats 51; no `.env`, guard clean, no Tailscale strings. Working tree clean; the guard Action, started by hand, passed on 7a8e38d. Next: the Superset dashboard on the custody views.

## 2026-10-26 18:23 CDT: how-to doc for the ontology

**Why.** wrolfgar: "Create a how-to doc on how to use the Jena ontology and what it help do better". New Claude Doc, [How to Use the Lakehouse Ontology (Jena Fuseki)](https://claude.ai/artifact/QZzDB9Lp8k94cXoU7smD7S): what it is (with a flow drawing of how meaning reaches the graph), what it does better than OpenMetadata's UI, SQL or Cube, getting started (browser UI, curl from the Mac, a pandas helper in Jupyter), the vocabulary (with a drawing of one column's links), 8 recipes, how to change it, and good-to-know limits.

- Every recipe and both code samples were run against the live graph first; answers in the doc are real (e.g. 20 Restricted and 13 Personal columns; 17 fact-table columns without a glossary term, including all four race and religion columns; Conduct Note linked to no column).
- Checked the Fuseki browser UI works through Caddy: it lists datasets via `$/server` (allowed); only create, delete, backup and stats hit the blocked admin endpoints.
- Caught and fixed in my own draft: a definition quoted from memory (now the real text), and advice to edit definitions in OpenMetadata's glossary screen, which `om_sync.py` overwrites from `glossary.yml` (now says to edit the file).

## 2026-10-26 17:18 CDT: items 2 to 6 (guard trigger, code search, session history, course packages, docstrings)

**Why.** wrolfgar: "Do items 2-6".

**Item 2, why pushes don't start the guard Action.** The workflow says `on: push`, Actions is enabled, pushes authenticate as pugwala with the `repo` and `workflow` scopes, there are no rulesets, no skip phrases, and the YAML is plain ASCII; manual runs work, but GitHub has never recorded a push-triggered run. Most likely the push trigger was never registered when the repo was recreated by pushing fresh history and renaming it into place; a push that changes the workflow file should register it. That needs a push to `main` (and a merge), so it waits for wrolfgar's go-ahead.

**Item 6, GitHub code search.** Inconclusive: the repo isn't indexed at all yet (even `import` across pugwala's code returns 0, as does the control word), so zero hits for the 12 banned terms mean nothing yet. Terms were read from the guard into a variable, never typed or printed; counts only. Recheck later.

**Item 5, session history.** Listed, nothing deleted (waiting for wrolfgar): the claude-mem observer transcripts (20 files, 16 matching lines in 6), `~/.claude/file-history` (53 lines in 16 files), one line in `~/.claude/history.jsonl`; this session's transcript (460 lines) waits for the next session. claude-mem's database and its backups have no matches; the memory notes have none.

**Item 3, course packages (test first: 4 acceptance tests).** pip 26.2 has `--uploaded-prior-to`, so every PyPI install in the image now resolves as of the `PIP_CUTOFF` build arg, the base image's date (2026-10-12): the course's open-ended requirements and every transitive dependency, without touching the course file. Build-only, so notebook setup cells can still install. Found: today's rebuilds had pulled spaCy 3.8.18 and transformers 5.21.0 uploaded that morning, sentence-transformers 6.2.0 (5 days) and huggingface-hub 2.3.0; now 3.8.16, 5.19.0, 6.1.0 and 1.33.0. torch pinned to 2.14.1 (PyTorch's index has no upload times). A new test checking each `==` pin against PyPI caught `dbt-core` 1.12.6, uploaded 2026-10-14 and pinned earlier without the two-week check: now 1.12.5. On the rebuilt image `daily_lake` (58c5b518) and `notebook_smoke` (b49c19bf) succeeded, including session 7's few-shot result with the real model.

**Item 4, docstrings (test first: 2 acceptance tests).** A test now enforces the rule across all of `lakehouse/`: every Python function and class has a docstring, every shell function a comment above it. It failed first on 23 Python functions (lake.py, load\_lake.py, definitions.py, test\_parity.py, and my own `SelftestConfig` class) and 9 shell functions (bootstrap.sh's helpers, the bats `setup`); all documented.

**Totals (17:18 CDT).** Acceptance 185 in one run, parity 19, bats 51, shellcheck clean, guard clean, no Tailscale strings, course files identical to `main`, `bootstrap.sh --check` green. Uncommitted.

**wrolfgar's decisions, then done (17:26 CDT).** wrolfgar approved deleting all three and three commits.

- Deleted after looking first: 14 claude-mem observer transcripts (6 had been cleaned up by claude-mem itself since the list; none written in the last 14 hours, so none active), the 190 file-history backups of this session, and the one matching line in `~/.claude/history.jsonl` (81 lines kept, same inode, mode 600). Re-scan: 0 matching lines in all three. This session's transcript waits for the next session.
- Commits as pugwala: 2fe874e (Python packages resolve as of the cutoff; torch and dbt-core pins) and e54794d (docstring test and docstrings; existing files gained only comment and docstring lines, nothing removed) on `duckdb-lakehouse`; c5ce083 on `main` (the guard workflow's header now says what triggers it), made in a separate worktree and merged as d5fdd87, so course files and `.github` stay identical. Each snapshot checked (no `.env`, guard clean, no Tailscale strings; bats 51 on commit 1's snapshot).
- Item 2 result: my hypothesis was wrong. Changing the workflow file didn't make GitHub start it from a push. GitHub's real-time activity log records every push, including these two, yet Actions has never started a run from one and the new `main` commit has no Actions check suite at all; no webhooks, rulesets, or token problems on our side. It looks like a GitHub-side suppression (possibly automatic review of a recreated public repo), not something the repo can fix. Manual runs passed on both heads (c5ce083, d5fdd87); the pre-commit hook remains the gate on every commit.

## 2026-10-26 16:51 CDT: Phase 7 begins: nothing floats

**Why.** wrolfgar asked what's next; DuckDB 2.0.0 shipped 2026-10-21 and 2.0.1 isn't out, so the plan's DuckDB 2.0 upgrade waits. wrolfgar said yes to pinning the three floating images first.

**What I found.** The floating tags lived in `.env` (`JUPYTER_BASE_TAG=latest`, `POSTGRES_TAG=17`, `CADDY_TAG=2`), which overrides every Compose default, and the jupyter build arg defaulted to `latest` too. Matching layer IDs against quay's published builds showed the jupyter image was built on that same day's base (`2026-10-26`): today's `rdflib` and `prometheus_client` rebuilds each pulled a fresh `latest`, so Dagster and the notebooks were running on a base under a day old.

**Pins (test first: 24 acceptance tests in new `test_pins.py`, 2 bats).**

- jupyter base `2026-10-12`, the newest dated build at least two weeks old (a step back from today's; Python 3.13.17 to 3.13.16). Layer match confirms the rebuilt image sits on exactly that build.
- `postgres:17.11-trixie` (17.11 released 2026-08-13; what was running) and `caddy:2.11.7` (released 2026-10-03; what was running). Docker Hub's dates are rebuild dates, so release dates came from upstream.
- The four loose lakehouse Python requirements (`jupysql`, `duckdb-engine`, `papermill`, `pytest`) pinned with `==`, each at the installed version, which was also the newest release at least two weeks old. The course's `requirements.txt` still floats (it's a course file); a lakehouse constraints file could pin it without touching it, proposed, not done.
- One place to pin: the three lines came out of `.env.example` and, in place, out of wrolfgar's `.env` (image tags, not secrets; inode and mode 600 kept). `bootstrap.sh` now fails on a floating `*_TAG` override in `.env`.
- Caught on the way: my first pin test split image references on the wrong `:` (inside `${X:-tag}`), so it was red for the wrong reason; fixed before trusting it. And a comment after an `ARG` value, which Dockerfiles don't allow, moved to its own line.

**Proof.** Bootstrap rebuilt jupyter and recreated catalog-pg, and the chunk-7 fix restarted Dagster by itself for the first time. Postgres reports 17.11, Caddy v2.11.7. `daily_lake` (ec235f5a) and `notebook_smoke` (8b592ced, all seven course notebooks plus `08_from_lake.ipynb`) succeeded on the new image. Acceptance 179 in one run, parity 19, bats 51, guard clean, no Tailscale strings, course files identical to `main`, `bootstrap.sh --check` all green. README gained a Pinned versions table. Uncommitted.

**Pushed (16:54 CDT).** wrolfgar: "yes please". One commit, a2bf4ff on `duckdb-lakehouse`, author and committer pugwala. Before committing: only `lakehouse/` staged (8 files), no `.env`, tieback guard clean on the staged diff, no Tailscale strings or secret-looking lines, course files identical to `main`. Working tree clean afterwards; the guard Action, started by hand, passed on a2bf4ff.

## 2026-10-26 15:31 CDT: Phase 6, monitoring, chunk 1 (platform metrics)

**Why.** wrolfgar: "I am more interested in the monitoring, but if you think we should jump on the protobuf issue then do that first". I checked protobuf first: nothing installed requires `grpcio-status` (it comes with the base notebook image for PySpark's unused Spark Connect client), Dagster and dbt need `protobuf<7`, and `grpc_status` works with 6.33.6, so the warning is cosmetic and monitoring came first. Found on the way: the jupyter base image is `pyspark-notebook:latest`, unpinned; noted for the upgrades phase.

**wrolfgar's decisions.** A new monitoring stack on this VM (not an existing Prometheus elsewhere); alert destination decided later, so Alertmanager will route to a placeholder. Monitoring services go in the `core` profile, not the plan's separate `monitoring` profile, because Caddy (core) will route to them and Compose won't start a core service that depends on a disabled profile; same choice as Phase 5.

**Plan, seven chunks.** (1) Prometheus, node-exporter, cAdvisor; (2) Grafana at /grafana/; (3) Postgres exporter and blackbox probes through Caddy; (4) Pushgateway, pipeline and data-quality metrics, Dagster failure sensor; (5) nightly catalog pg\_dump with freshness; (6) Alertmanager and rules; (7) the Home Lakehouse dashboard and docs.

**Chunk 1 (test first: 8 acceptance tests, 3 bats).** Prometheus v3.15.0 (v3.15.1 was 5 days old), node-exporter v1.12.1, cAdvisor v0.60.6 (now at `ghcr.io/google/cadvisor`; the old gcr.io path has no such tag). No host ports anywhere: the tailnet reaches anything on the VM's 0.0.0.0, so the exporters stay on the Compose network and Prometheus is served only through Caddy at `/prometheus/`, behind the Dagster basic-auth login. Prometheus runs as 1000:100, 30 days of data on `/lake/prometheus`. node-exporter reads the host through `/host` with `pid: host` (without host networking its network counters are its container's; everything else is the VM's). cAdvisor needs privileged mode and the Docker socket, which makes it root-equivalent; that is the normal way to run it, and it has no port off the Compose network. All targets up; the VM's 31 GiB and `/lake` show in node metrics; every service shows in cAdvisor by its Compose name. Cost: Prometheus 54 MB, node-exporter 13 MB, cAdvisor 622 MB (VM at 6 of 31 GB). bats 38, `bootstrap.sh` all green, `/prometheus/` answers 401 through Caddy.

**Chunk 2, Grafana (15:34 CDT, test first: 5 acceptance tests, 4 bats).** Grafana 13.2.3 (13.2.4 was 13 days old, one short) at `/grafana/`, its own login: `admin` with `GRAFANA_ADMIN_PASSWORD`, new in bootstrap (read it in your own SSH session; Grafana applies it only when it first creates its database). No anonymous access, no sign-up, and no phoning home (usage reporting, update checks and news feed off). Runs as 1000:100, data on `/lake/grafana`, no host port. The Prometheus data source is provisioned from `monitoring/grafana/provisioning/` and answers its health check. bats 40, `bootstrap.sh` all green, `/grafana/` answers 302 to its login through Caddy; monitoring tests 13 of 13.

**Chunk 3, service probes (15:40 CDT, test first: 7 acceptance tests, 2 bats).** postgres-exporter v0.20.1 logs in to catalog-pg as a new `lake_monitor` role (`postgres/init/05-monitor.sh`, `LAKE_MONITOR_PASSWORD` new in bootstrap) holding only `pg_monitor`: statistics, never table data (it can't SELECT the DuckLake catalog). blackbox-exporter v0.29.0 (v0.29.1 was 5 days old) probes the same eight sites bootstrap checks, through Caddy on the Tailscale name with the certificate checked; 401 counts as up for the guarded ones (Dagster, Prometheus, MCP). Keeping the Tailscale name out of the repo: `monitoring/prometheus/sites.yml` names the host `LAKE_TS_HOST`, and a small `start.sh` fills it in at Prometheus start, writing to its data folder; containers can't resolve the name (accept-dns off), so blackbox maps it to the host with `extra_hosts: host-gateway`, where Caddy's 443 answers. Live check: stopping Fuseki dropped its `probe_success` to 0 within a scrape and restarting brought it back to 1. Certificate has more than a week left. Cost: exporters 14 MB and 22 MB, Grafana 345 MB. bats 41, monitoring tests 20 of 20, `bootstrap.sh` all green.

**Chunk 4, pipeline and data-quality metrics (15:47 CDT, test first: 8 acceptance tests, 2 bats, 1 daily-run check).** Pushgateway v1.11.4, persisted to `/lake/pushgateway`, scraped by Prometheus with `honor_labels`. New `lakehouse/metrics.py` pushes gauges with POST (so a success push keeps the last-failure time) and never raises: a failed push is a logged warning, never a failed run. What gets pushed:

- `load_lake`: rows per layer, flagged values, records with exceptions, seconds, finish time.
- New asset `monitoring/data_quality` after gold: pass rate per quality dimension and the count of rules under the 95% floor (the same condition as dbt's `dq_score_floor` test, so the two can't disagree).
- Two sensors, on by default: `push_run_success` (last success time and duration of every job) and `push_run_failure` (last failure time).
- New job `monitoring_selftest` fails on request (`fail: true`), so the failure path, and chunk 6's alert, can be exercised on demand. The test fails it, sees the failure pushed, passes it, and sees a newer success.

`prometheus_client==0.26.0` pinned (already in the image via jupyter\_server; pip check shows only the old protobuf warning). Prometheus doesn't reread `prometheus.yml` on its own and bootstrap only recreates containers whose Compose settings changed, so it needed a restart by name; to fix in chunk 7. A real `daily_lake` run (54440abb) pushed everything; 25 of 25 pipeline and daily-run tests, bats 42.

**Chunk 5, nightly catalog backup (15:57 CDT, test first: 6 acceptance tests, 3 bats).** The jupyter image has no `pg_dump`, and its Ubuntu would offer 18 against a 17.11 server (a newer dump isn't guaranteed to restore with 17's tools), so the backup is a `catalog-backup` sidecar on catalog-pg's own `postgres:17` image: an exact match. `backup/backup.sh` runs at start when the newest backup is over 23 hours old, then at 02:00 Central; it dumps `ducklake`, `dagster`, `superset` and `openmetadata_db` in custom format to `/lake/catalog-backups/<UTC stamp>/`, reads each back with `pg_restore --list`, writes `manifest.json`, keeps 14 days, and records success time, duration and sizes (or a failure time) for node-exporter's textfile collector. The healthcheck goes unhealthy when no backup has finished in 26 hours. It logs in as new `lake_backup` (`postgres/init/06-backup.sh`, `LAKE_BACKUP_PASSWORD`): `pg_read_all_data`, not a superuser, can't write; ducklake needed CONNECT by name. Roles aren't dumped (that needs a superuser; init scripts recreate them from `.env`).

- First run failed: `/lake/catalog-backups` was root-owned, because bootstrap had deliberately skipped it as a "host-side pg\_dump target". Fixing that raised who should read backups: they hold every app database including password hashes, so the sidecar runs as uid 999 (the image's postgres user), bootstrap now gives the folder to 999, and dumps are mode 600; folders, manifest and metrics stay readable. A test checks the notebook user (uid 1000) gets permission denied on a dump. (On the VM, gid 999 shows as `systemd-journal`; only a host name for the number, and the dumps grant the group nothing.)
- Restore drill: the ducklake dump restored into a scratch database and matched the live catalog row for row (snapshots 86, tables 154, data files 107, columns 1,089); scratch database dropped. bats 44, backup tests 6 of 6, `bootstrap.sh` green.

**Chunk 6, alerting (16:05 CDT, test first: 7 acceptance tests, 3 bats).** Alertmanager v0.34.1 at `/alertmanager/` behind the Dagster basic-auth login, silences on `/lake/alertmanager`. Every alert routes to `undecided`, a receiver with no integrations (wrolfgar's "decide later"), so nothing leaves the VM; the config says how to add PagerDuty with a key file kept outside the repo. 17 rules in `monitoring/prometheus/rules/lakehouse.yml` (promtool and amtool both pass), thresholds set from today's real values: platform (target or site down 5 min, certificate under 14 days, `/` or `/lake` over 85% / 95%, memory under 10%, Postgres down); pipeline (`JobFailing` when a job's last failure is newer than its last success, `daily_lake` not succeeded in 26 hours, `notebook_smoke` in 8 days); data (silver fewer rows than bronze, flagged share over 10% against about 3% today, a dimension under 95%, more than the one expected rule under the floor); backup (none in 26 hours, last one failed); and Watchdog, always firing on purpose. On the healthy stack only Watchdog fires. End to end: failing `monitoring_selftest` raised `JobFailing` in Alertmanager and a passing run resolved it (about 2 minutes). Note: `/` is 64% full today, mostly container images.

- My receiver test first assumed the receiver would show only a name; Alertmanager 0.34 also reports a `labels` field, so the test now checks what was meant: no `*_configs` integrations.
- Dagster's API answered 500 again until its pooled connections cycled; the third time this followed catalog-pg being recreated. For chunk 7: bootstrap should restart Dagster when it recreates catalog-pg, and restart Prometheus and Alertmanager when their config changes (neither rereads it, and bootstrap only recreates on Compose changes). bats 45.

**Chunk 7, bootstrap fixes, dashboard and docs (16:21 CDT, test first: 2 acceptance tests, 4 bats).**

- Bootstrap now captures what `up -d --wait catalog-pg` prints and restarts Dagster only when catalog-pg was Recreated; and on every run refills the probe targets (new `fill-targets.sh`, shared with Prometheus's `start.sh`) and sends SIGHUP to Prometheus and Alertmanager. Live: `lastConfigTime` moved, start time unchanged.
- **Home Lakehouse** dashboard, 21 panels in three rows (Platform, Pipeline, Data quality), provisioned read-only from `monitoring/grafana/dashboards/home-lakehouse.json`; a test runs every panel's query against Prometheus and requires data. Grafana's home-path setting turned out to load a hidden second copy (uid `default-home-dashboard`), so it was dropped for new `monitoring/grafana/set_home.py`, which sets the org preference to the provisioned dashboard (bootstrap runs it; `--check` compares).
- The chunk 3 test "probe exactly the sites bootstrap checks" caught that Alertmanager had joined bootstrap's checks but not the probes; added.
- README: monitoring section (sources, alert rules, the undecided receiver and how to add PagerDuty, how to test an alert, backups and a restore recipe), sites list, twenty services, bootstrap steps, file and test-status rows, Phases 0 to 6 done. Bootstrap's closing message lists `/grafana/`.

**Totals (16:21 CDT), Phase 6.** Acceptance 155 in one run (monitoring 22, pipeline metrics 8, alerting 7, backup 6 new), bats 49, parity 19, guard bats 5, tieback guard clean, no Tailscale strings, course files identical to `main`, `bootstrap.sh --check` all green. One run before that had a single Dagster 500 (its pool still stale from chunk 5's catalog-pg recreation, before the fix existed); restarting Dagster cleared it, and the next full run was clean. Phase 6 is uncommitted on `duckdb-lakehouse`.

**Pushed (16:30 CDT).** wrolfgar: "do the commits one per chunk the same safe way". Seven commits on `duckdb-lakehouse`, author and committer pugwala: 01cf003 (Prometheus and exporters), 6a33b28 (Grafana), 1685cd7 (Postgres exporter and blackbox), deb6c03 (Pushgateway, sensors, data-quality metrics), a4efa3a (catalog backup), fc31d04 (Alertmanager and rules), 4277db0 (dashboard, bootstrap reloads, docs). Shared files were split by peeling later chunks off the final files and staging with `git hash-object` / `git update-index`; peeling chunk 1 too landed byte-identical on HEAD for all five pre-existing shared files, which proves each intermediate version exact. Each snapshot was tested on its own (Python compiles, `docker compose config -q` valid, promtool passes, bats 38, 40, 41, 42, 44, 45, 49), with `.env` unstaged, the tieback guard clean and no Tailscale strings. My commit script stopped once at chunk 2, on its own bug (no Python files in that snapshot's monitoring folder yet), before committing; fixed and resumed. Working tree clean afterwards; the guard Action passed on 4277db0.

## 2026-10-26 14:25 CDT: Phase 5 extras, chunk 1 (daily om\_sync), and a secrets rotation

**Why.** wrolfgar: "do the 2 optional phase 5 pieces in chunks that are easy to manage". Four chunks: (1) daily om\_sync in Dagster, (2) the Fuseki service, (3) the glossary as RDF in Fuseki, (4) keeping Fuseki fresh, plus docs.

**Chunk 1, daily om\_sync (test first, 4 tests seen failing).** New Dagster asset `openmetadata/lake`, downstream of load\_lake and gold, so the 05:00 `daily_lake` run now runs `om_sync.py` last. A non-blocking WARN check, `cube_masks_match_openmetadata`, runs `sync_masks.py --check`: it flags a steward's new Restricted tag that the Cube model doesn't mask yet, without rewriting the model (that stays a reviewed bootstrap step). The Dagster services got `OM_ADMIN_PASSWORD` and `OM_MCP_PASSWORD`. A real `daily_lake` run (6f9c94d6) succeeded with the new asset and a passing check.

**My mistake, and the rotation.** While reading the Dagster setup I ran `docker compose config`, which resolves `.env`, and its output put `LAKE_RW_PASSWORD` (as `PGPASSWORD`) and `OM_DB_PASSWORD` in this session's transcript and claude-mem's local log; never GitHub. wrolfgar chose to rotate both now. New random values went into `.env` in place (same inode, mode 600); `ALTER ROLE lake_rw` and `ALTER ROLE openmetadata` through psql variables (first attempt failed harmlessly: `POSTGRES_USER` isn't set inside catalog-pg, so `-U "${POSTGRES_USER:-postgres}"`); `bootstrap.sh` recreated catalog-pg, jupyter, Dagster and OpenMetadata and passed every check. Proof over TCP: both old passwords rejected, both new ones accepted. The temporary `.env` backup was shredded. Memory note added: never print `docker compose config` or container env.

**Totals (14:23 CDT).** Acceptance 93 (all passed first try after the rotation), bats 34, parity 19. Chunk 1 is uncommitted.

**Chunk 2, the Fuseki service (14:36 CDT, test first: 7 acceptance tests, 4 bats).** Apache Jena Fuseki 6.2.0 (released 2026-07-27) in our own image, `lakehouse/fuseki/Dockerfile`: Apache's release tarball, its SHA-512 pinned (matched against Apache's `.sha512`) and its GPG signature checked against Apache's Jena KEYS on every build, on Eclipse Temurin `21.0.12_8-jre-noble` (Jena 6 needs Java 21; the newer 21.0.12.1 tag was only 9 days old). One dataset, `lakehouse`, TDB2 under `/lake/fuseki`, served at `/fuseki/` through Caddy. Reads are open to the tailnet (the dataset will only hold the glossary and which columns are tagged); writes need the `writer` user, whose password (`FUSEKI_WRITER_PASSWORD`, new in bootstrap) is written by `start.sh` to a mode-600 file on a tmpfs. Runs as 1000:100, about 214 MB.

- Fixed on the way: the UI build wants a writable base folder (default `/run`), now on the tmpfs; and it writes a default `shiro.ini` with a sample `user1`/`passwd1`, so `start.sh` installs our own `fuseki/shiro.ini` (no users, admin endpoints localhost-only) first. Probes: `user1` can't write, every `/$/` admin endpoint answers 403 from the network.
- Deliberate break: with the writer-only rule removed from the update endpoint, `test_writes_need_the_writer_password` failed (200 instead of 401); restored, 7 of 7. `bootstrap.sh --check` all green, `/fuseki/` answers 200 with a trusted certificate.

**Chunk 3, the glossary as RDF in Fuseki (14:40 CDT, test first: 8 acceptance tests, 1 bats).** New `openmetadata/om_to_rdf.py` reads OpenMetadata as the read-only `mcp-reader` and replaces one named graph in Fuseki (Graph Store PUT as `writer`): the Lakehouse glossary as SKOS (concepts, definitions, synonyms as altLabel; broader/narrower/relatedTo as SKOS's own relations, partOf/identifies and the rest as `lh:` properties) and every lake column with its Sensitivity tag and the term it means. IRIs sit under `lakehouse.invalid`, a reserved name that never resolves. 715 triples; `--check` compares graphs with rdflib, and a stray triple added by hand was flagged and then removed by the next load. The payoff query, "which restricted columns hold part of an offender record?", returns `stg_group` and `stg_status` in one SPARQL query, and the graph's Restricted columns equal Cube's masks. `bootstrap.sh` runs it right after `om_sync.py`.

- New pinned dependency in the image: `rdflib==7.6.0` (2026-02-13) and `pyparsing==3.3.3` (already installed; pinned). pip reports one dependency conflict (`grpcio-status` wants protobuf 7, the image has 6.33.6); building the committed requirements in a throwaway worktree showed the same warning, so it predates this change. Left as an open item.

**Chunk 4, keeping Fuseki fresh, and docs (14:44 CDT, test first: 2 acceptance tests, 1 bats).** New Dagster asset `fuseki/glossary` runs `om_to_rdf.py` right after `openmetadata/lake`, so the 05:00 `daily_lake` run now goes load → parity → gold → OpenMetadata → Fuseki; the Dagster services got `FUSEKI_WRITER_PASSWORD`. A real run (8c7e2a3c) succeeded end to end. bootstrap's closing message now lists `/fuseki/`. README: the daily-run diagram, the eleven services, a Fuseki section with the SPARQL example, file and test-status rows. Through Caddy (the VM pins its own Tailscale name with `--resolve`, since accept-dns is off) the README's query answers `stg_group`, `stg_status`; an anonymous write gets 401 and the admin endpoint 403.

**Totals (14:44 CDT), all four chunks.** Acceptance 111 (Fuseki 7, glossary RDF 10, om\_sync 12, daily run 16 among them), bats 37, parity 19, guard bats 5, tieback guard clean, no Tailscale strings in the diff, course files identical to `main`, `bootstrap.sh --check` all green. All four chunks are uncommitted on `duckdb-lakehouse`.

**Pushed (15:21 CDT).** wrolfgar: "do the commits". Four commits on `duckdb-lakehouse`, one per chunk, author and committer pugwala with the no-reply email: 24fef43 (daily om\_sync), 173686d (Fuseki at /fuseki), f8a3378 (glossary as RDF), 9735191 (daily Fuseki refresh, docs). Files touched by several chunks (compose.yaml, bootstrap.sh and .bats, definitions.py, two tests) were split by peeling later chunks' edits off the final files and staging each version with `git hash-object` / `git update-index`, so the working tree never changed; the chunk-4 versions were checked byte-identical to the tree, and the tree was clean after the last commit. Each staged snapshot was tested on its own before its commit (Python compiles, compose.yaml parses, bats 34, 36, 37, 37 all passing), with `.env` unstaged, the tieback guard clean and no Tailscale strings in added lines. The guard Action, started by hand, passed on 9735191.

## 2026-10-26 13:35 CDT: Phase 5 built: OpenMetadata decides what's restricted, Cube masks it

**Why.** wrolfgar: "start phase 5 and continue as you deem best". Four slices, each test-first (red shown for the right reason, then green). All of it is uncommitted on `duckdb-lakehouse`, waiting for wrolfgar's go-ahead.

**Slice 1, Cube masking.** The restricted columns (race, religion, STG) are now in Cube's `offender_records` model but masked: an `access_policy` gives every group `***` for them, and only the `restricted_reader` group (from a token's `groups` claim, mapped in `cube.js` by `contextToGroups`) sees real values. Works through both the SQL API (Superset) and REST (the MCP server). Gotcha: in YAML a mask must be SQL, `mask: {sql: "'***'"}`; a bare `"***"` compiles to null. Unmasking everyone on purpose made 8 tests fail.

**Slice 2, OpenMetadata 2.0.5 with OpenSearch 2.19.6** at `/openmetadata/` on the Tailscale name, with its own database on catalog-pg (`04-openmetadata.sh`). No published default survives: `bootstrap.sh` generates the Fernet key and the JWT signing keys (once, under `/lake/openmetadata/keys`), `setup_admin.py` replaces the admin password and creates a read-only `mcp-reader` (DataConsumer only), and self-signup is off. Gotchas: the image has wget, not curl; login sends the password base64-encoded but changePassword takes plain text; the password policy wants upper, lower, digit and special.

**Slice 3, `om_sync.py` and `define_term` on OpenMetadata.** `om_sync.py` pushes the Lakehouse glossary (typed relations, synonyms, columns and metrics as custom properties), a Sensitivity classification (Restricted, Personal) and every lake table with dbt's descriptions, Sensitivity tags from dbt's `meta.sensitivity` and glossary-term links. Re-running changes nothing. The MCP server's `define_term` now reads OpenMetadata as `mcp-reader`, so an edit in the UI shows up at once (proved: an edit to Escape Risk reached `define_term`, and `om_sync.py` put it back with relations intact). Gotchas: descriptions come back HTML-escaped; a glossary term's tags propagate to linked columns as Derived.

**Slice 4, the tags-to-masks loop.** dbt's tags are the floor; a steward can add `Sensitivity.Restricted` in OpenMetadata, and `om_sync.py` keeps it. New `cube/sync_masks.py` rewrites the Cube policy to mask exactly the restricted columns Cube serves (adding or dropping `mask:` lines, comments kept). `bootstrap.sh` runs it after `om_sync.py` (as the repo owner in the users group, the only way into `/home/jovyan` where the repo is mounted) and restarts Cube when the masks change; `--check` fails while the model is behind. Live proof: tagging `gender` Restricted gave `***` for all 100,000 records in Cube; removing the tag brought back F 21,288 / M 75,717 / null 2,995 and a byte-identical model file.

**Totals (13:30 CDT).** Parity 19, acceptance 89 (8 OpenMetadata, 9 om\_sync, 4 masks, 15 Cube, 13 MCP among them), bats 34, guard bats 5, tieback guard clean, no Tailscale strings in the diff, course files identical to `main`, `bootstrap.sh --check` all green. One hiccup: right after catalog-pg was recreated, Dagster's GraphQL answered 500 for a few calls (stale pooled connections), then recovered on its own; two reruns gave 23 of 23.

**Pushed (13:58 CDT).** wrolfgar: "commit and push as pugwala". Commit 3255c15 on `duckdb-lakehouse`, author and committer pugwala with the no-reply email. Before committing: only `lakehouse/` staged, no `.env`, tieback guard clean on the staged diff, no Tailscale names or 100.x addresses in added lines, course files identical to `main`; the one secret-looking line was the bats fixture's fake `om-fernet-secret`. The guard Action, started by hand (pushes still don't start it), passed on 3255c15.

## 2026-10-26 · Phase 4 finished: the MCP server

**Why.** wrolfgar: "please work on Phase 4 MCP tools." The plan said to wire his existing MCP server experiment to `query_metric` (Cube REST) and `define_term` (OpenMetadata glossary). No MCP server was on the VM and OpenMetadata is Phase 5, so I asked. wrolfgar chose a new server in this Compose stack, a glossary file in the repo until Phase 5, and Claude Code on his Mac as the first client.

**Checked before building.** In `mcp==2.3.0` (2026-10-02, the newest at least two weeks old), FastMCP was renamed `MCPServer`. Tools that return `dict` get no structured output, and ordinary exceptions reach the client masked as "Error executing tool X" (`ToolError` is for messages meant for the caller). All of it was found in a throwaway container and saved to memory.

**Built (test first).**

- `lakehouse/mcp/server.py` with two tools:
  - `query_metric` resolves a measure and dimensions by short or full name from Cube's `/meta` and calls `/load` with a 5-minute JWT signed with `CUBEJS_API_SECRET`. An unknown name lists the real ones.
  - `define_term` matches a name or synonym in any case.
- Results are Pydantic models, so clients get structured content. It serves stateless JSON at `/mcp`, with a constant-time bearer-token check in front of everything but `/healthz`, and DNS-rebinding protection allowing only `LAKE_TS_HOST` and the Compose name.
- `lakehouse/glossary/glossary.yml`: the plan's 14 terms, each with a definition, synonyms, columns, metrics and typed relations.
- The `mcp` service (python 3.13.15-slim, pinned requirements) holds no lake credentials, so Cube is its one way to the data. Caddy routes `/mcp`. `bootstrap.sh` generates `MCP_TOKEN`, builds `lnl-mcp:local`, starts nine services and checks `/mcp` answers 401 without the token.
- **Tests.** 13 acceptance tests and 4 bats tests, all seen red first. Two deliberate breaks were caught: a token check that always passes, and synonyms ignored.
- **End to end through Caddy** with the trusted certificate and the token: `query_metric total_restitution` = 1,333,587,950.77.

**Totals (08:23 CDT).** Parity 19, acceptance 59, bootstrap bats 26, guard bats 5. `bootstrap.sh --check` passes. Guard clean; the only Tailscale-looking text is an unchanged comment about the generic \*<tailnet-host> domain.

**Pushed (12:42 CDT), after wrolfgar's go-ahead:** d132983 on `duckdb-lakehouse`, as pugwala. The guard passed on GitHub (run 40371220260, dispatched by hand). Next, wrolfgar connects Claude Code with the command in the Handoff. Before that, `define_term` answered "offender number" correctly through Caddy.

**Connected from the Mac (12:48 CDT).** wrolfgar ran `claude mcp add` on his Mac (user scope; the token was fetched over SSH and never shown), then asked Claude Code "what does the offender number mean?". It called `define_term` and answered from the glossary. The server log shows 7 requests in 30 minutes, all 200, all through Caddy.

## 2026-10-26 · Session 7 fixed: few-shot now beats the rules with either model

**Why.** wrolfgar: "fix the course discrepancy please." The Facilitator Guide says few-shot scores highest, but with the real sentence-transformer few-shot scored F1 0.750 against the session 6 rules' 0.899.

**Diagnosis (experiments; nothing changed until the cause was clear).** Scored as notebook 7 scores it, on the same 9,700 held-out notes:

| 300 labels | real model | fallback (LSA) |
| --- | --- | --- |
| Few-shot, default C=1 | 0.750 | 0.947 |
| Few-shot, C=100 | 0.926 | 0.985 |
| Session 6 rules | 0.899 | 0.899 |
| Zero-shot | 0.568 | 0.588 |

The guide was right only for the fallback. The cause is in the code: `LogisticRegression` at its default C=1 on length-1 embedding vectors regularizes too hard and underfits (recall 0.676). Cross-validation on the 300 training notes alone picked C between about 20 and 1,300 across both models and sizes, so C=100 is not tuned on the test notes. `LogisticRegressionCV` was rejected: it prints three FutureWarnings in scikit-learn 1.9, and the parameters that silence them don't exist in the older scikit-learn on Databricks runtimes.

**The fix (test first).**

- Two lakehouse tests: few-shot must beat the rules with the real model (from the latest smoke run) and with the fallback (a fresh offline run with an empty model cache). The real-model test was red (0.75 < 0.899); the fallback test passed already and guards that path.
- Notebook 7: `LogisticRegression(C=100, max_iter=1000)` with a two-line comment, and a false summary sentence rewritten. It had said zero-shot is "respectable with a sentence-transformer" (0.568) and few-shot "much less sensitive" to the model.
- FACILITATOR\_GUIDE.md gives both paths' numbers, the your-turn-#2 expectations and a C=100 talking point; README.md records that session 7 was run both ways.
- notebook\_smoke run e5dd98d8 passed; both tests green; acceptance 46, parity 19, bats 25.

**Published materials.**

- Course site version 10: session 7's code cell, scoreboard table and chart, and summary sentence, on the staff and instructor pages. Rendered from a fresh fallback run, after proving the renderer reproduces the old cells exactly (the chart differs only in PNG encoding).
- Slides version 15: s7-board shows the real-model bars with the fallback numbers in the caption; s7-few shows C=100.
- Facilitator Guide doc (rev 60) and README doc (rev 43) updated.
- Student handout: no session 7 results in its text, so unchanged.

**Pushed (05:30 CDT), after wrolfgar's go-ahead.** `main` got c536880 (the three course files), committed from a separate worktree. On `duckdb-lakehouse`, the uncommitted copies were checked byte-identical to that commit, then main was merged in (73197bc, no force-push), then the two tests went in as 58d4372. Course files are identical on both branches; the guard passed on GitHub for both (runs 40308023220 and 40308039778, dispatched by hand).

## 2026-10-26 · Phase 3 finished: the notebooks on the VM

**Why.** wrolfgar: "finish phase 3 please." Four items were left: run sessions 1 to 7, stage the embedding model, a weekly notebook\_smoke job, and `08_from_lake.ipynb`. The course files stay identical to main, so every fix is in the lakehouse.

**Sessions 6 and 7.** Both now run clean; the spaCy OverflowError from the anonymization proof doesn't reproduce in the current image. Session 6's final F1 is 0.898, as the guide says. Session 7 ran with the real sentence-transformer for the first time ever (it downloaded from Hugging Face). **Course finding:** few-shot F1 0.750 against the session 6 rules' 0.899, while the Facilitator Guide says few-shot scores highest; the guide was written from the fallback run. Left for wrolfgar; course files unchanged.

**Model staged (test first).**

- `lnl/config.py` hard-codes `EMBEDDING_MODEL`, so instead of changing it, compose's shared lake-env sets `HF_HOME=/lake/models/huggingface` and `HF_HUB_OFFLINE=1`.
- `scripts/stage_model.py` downloads the pinned revision 1110a24 (2026-06-01, Apache-2.0): only the 11 files the model needs, 88 MB instead of the 1 GB repo.
- `bootstrap.sh` stages it when it's missing (3 new bats tests, 25 in total).
- Red first: offline, the course fell back to LSA.

**`08_from_lake.ipynb` (test first).** The Trust Test's eight questions in SQL over silver through `%load_ext lakehouse.sql_magic`, ending in a self-check: "8 of 8 answers match gold.trust\_test." Stored without outputs. Its test caught two bugs:

- **Module name.** From a notebook in `lakehouse/`, the extension's old name `sql.py` hid jupysql's own `sql` package, so loading recursed forever. Renamed to `sql_magic.py`, with a test that imports both from inside `lakehouse/`.
- **My typo.** A missing `s` in the check query. jupysql's error blamed `::` casts (a misleading hint it attaches to any failing query with `::`). The root cause was found by following the exception chain. A cast test that never failed was removed rather than kept as a non-test.

**`notebook_smoke` job (test first).** An op job, not an asset, so `daily_lake`'s all-asset selection never picks it up. It runs the 7 course notebooks as delivered plus 08 with papermill into `/lake/notebook-runs/<date>_<run>/`, keeps going past a failure, then fails listing which notebooks broke. Scheduled Sundays 06:00 Central, on by default.

- First run 9a4f5acc: all 7 course notebooks passed, but 08 failed in Dagster because `PYTHONPATH` and `LAKE_RO_PASSWORD` were set for Jupyter only. Both moved into lake-env, with a test over all three services (red first).
- Second run 1215d367: **SUCCESS, all 8 notebooks in 110 s.** Spot-checked against the guide: session 1 Q1 1,536 → 2,991 and exercise 1 = 22, session 2 8,499, session 3 1,633 centuries, session 4 1,086 exceptions and 228 conflicts, session 5 22 of 22 reconciled, session 6 F1 0.898. Exercise answers (554, the restitution total) only appear with the blanks filled.

**Totals (04:28 CDT).** Parity 19, acceptance 44, bootstrap bats 25, guard bats 5. `bootstrap.sh --check` passes. Guard clean, no Tailscale strings, course files identical to main. Pushed at 04:31 CDT as 2035849 (pugwala) after wrolfgar's go-ahead; the guard passed on GitHub (dispatched by hand, run 40300271608).

## 2026-10-26 · Trust Test pushed; Phase 4, slice 3: %sql in Jupyter

**Trust Test pushed (03:54 CDT).** wrolfgar asked to commit and push it. Commit 4ff076b, as pugwala, on `duckdb-lakehouse`. The pre-commit guard was clean. The push again didn't start the Action: GitHub created only the Claude app's check suite, none for Actions. Dispatched by hand, and the guard passed on 4ff076b (run 40295678177).

**%sql connection (built 04:03 CDT, uncommitted).** In any notebook, `%load_ext lakehouse.sql`, then `%sql` or `%%sql` cells query the lake read-only as `lake_ro`. The plan asked for a saved connection that runs the DuckLake attach on connect.

- **Password.** `lake.attach_lake_ro()` puts `LAKE_RO_PASSWORD` in a temporary *default* postgres secret, then attaches with only host, database and user. Tried first: a *named* secret isn't used, and DuckLake's failed-connection error printed the whole connection string, so a password in the ATTACH would show up in a notebook. Postgres confirmed the catalog session is lake\_ro (tagged `application_name=lakehouse-sql`).
- **Every connection gets the lake.** `USE lake` only reaches the connection that runs it, and jupysql runs queries on other connections. `search_path` can't be set globally. So `lakehouse/sql.py` hands jupysql a SQLAlchemy engine whose `connect` event attaches the lake on every new connection.
- **One bad query no longer breaks the session.** The test of a refused write exposed this: DuckDB aborts the transaction when a query fails while running, and jupysql didn't roll back, so every later query failed. A `handle_error` event rolls back. Autocommit isn't supported by duckdb-engine.
- **Image fix.** jupysql imports pyspark 4.2's Spark Connect code, which needs `zstandard`. Without it notebooks printed "Skipping doctests" and pytest failed. Pinned `zstandard==0.25.0` (2025-09) and rebuilt `lnl-jupyter:local`; the image build took 30 s, then jupyter and both Dagster services were recreated.
- **Compose.** Jupyter now gets `LAKE_RO_PASSWORD` and `PYTHONPATH=/home/jovyan/course`. The base image doesn't use PYTHONPATH, and pyspark comes from pip.
- **Tests.** 6 in `acceptance/test_sql.py`, all seen red first. Two deliberate breaks were caught: password in the ATTACH string, and READ\_ONLY removed. The second was only caught after adding a check of DuckDB's readonly flag, because lake\_ro's grants alone already stop writes. A real notebook kernel started in `/tmp` ran `%%sql` against `gold.trust_test`.
- **Totals.** Parity 19, acceptance 37, bootstrap bats 22, guard bats 5. `bootstrap.sh --check` passes. Guard clean, no Tailscale strings.

**Pushed (04:08 CDT).** wrolfgar approved: commit a9b8b1e, as pugwala, on `duckdb-lakehouse`. The guard was clean locally and passed on GitHub (dispatched by hand, run 40297290410).

## 2026-10-26 · claude-mem re-pinned; Phase 4: the Trust Test dashboard

**Why.** wrolfgar said "do what you think is best" about the open items. Three were done (code search is still waiting on GitHub; clearing session records waits for this session to end, and both are queued in claude-mem's work state).

**GitHub code search (03:35 CDT).** Still not indexed: the positive control `offender_number` returns 0, so a 0 for the old names proves nothing yet. The fresh-clone grep remains the real check.

**claude-mem back on 15.0.2 (03:40 CDT).**

- Safe to downgrade: 15.2.x ran no schema migrations (schema\_versions tops out at 68, all applied at the 15.0.2 install).
- Database backed up first with SQLite's backup API (integrity ok).
- Reinstalled with `npx claude-mem@15.0.2 install --provider claude`, then turned off `autoUpdate` for the thedotmack marketplace in `~/.claude/plugins/known_marketplaces.json`. Worker reports 15.0.2; provider is the Anthropic plan; cloud sync empty; telemetry disabled.
- **Finding:** reading the installer's code showed that every `npx claude-mem install` POSTs the hostname (`lakehouse`), the install state and per-day observation and token counts to cmem.ai to make a sign-in link. `CLAUDE_MEM_ONLINE_OPTIN=false` doesn't stop it, and both installs did it. No prompts, paths or project names are sent. Future installs: prefix `CMEM_PRO_ORIGIN=http://127.0.0.1:9`. The link it printed (with an instruction aimed at the agent) was not shown or used.

**Trust Test dashboard (Phase 4, built 03:50 CDT, uncommitted).** Session 1's eight questions, answered from a default load and from the cleansed data, now flow through every layer. Test first at each one; each new test was seen failing for the right reason before the code existed:

- Loader: `lake.trust_test_table()` runs the course's own `lnl.trust`, as notebook 4 does, into `silver.trust_test`. A 19th parity check (blocking in `daily_lake`) holds the Facilitator Guide's contract: 8 questions, all changed, Q1 1,536 → 2,991 and Q2 19 → 3.
- dbt: `gold.trust_test`, with unique, not-null and accepted-values tests (all 8 must have changed) at error severity.
- Cube: a `trust_test` cube (aggregates only).
- Superset: `superset/dashboards.py` creates the dataset, a table chart and the **Trust Test** dashboard through the REST API, idempotently; `bootstrap.sh` runs it (with `--check` when checking), covered by 3 new bats tests.
- Proof: `daily_lake` run 333aba1a succeeded (18.8 s; 25 dbt checks, 24 pass, 1 expected warning). Parity 19, acceptance 31, bootstrap bats 22, guard bats 5, and `bootstrap.sh --check` all pass. A second `dashboards.py` run changed nothing. The guard is clean, no Tailscale strings, course files identical to main.

**Waiting on wrolfgar:** the go-ahead to commit and push the Trust Test slice.

## 2026-10-26 · Course artifacts and the Handoff brought in line with the repo

**Why.** After the repo scrub, wrolfgar asked whether every artifact was up to date. Four weren't: the course site, the README and Facilitator Guide docs, the slides, and the Handoff. Each was fixed with the repo's own wording, test first: a counter built on the guard's PATTERN (masked output, so no banned word reaches a log) had to show hits (red) and then zero (green), and every result was checked against the live copy.

**Course site** (03:19 CDT, version 9). 275 hits went to 0.

- Code: all 152 code cells now match the repo notebooks exactly.
- Outputs: notebooks 1, 2 and supply orders were re-run under the original render's pandas 3.0.2 in a throwaway python:3.13-slim container, and every output matches the fresh run. The `df.info()` padding needed the real run, because the new name is 4 characters longer.
- Removed: the realistic-names dataset section, its Files rows and the second generator. That dataset was never in the repo, and it was built on real unit names, which the guard's list didn't cover.
- Supply orders: these pages had been built from an older CSV, so their unit names were regenerated from the current CSV. The renderer was proven first on the 80 unchanged sample cells.
- Banner: the agency banner was removed.

**README and Facilitator Guide docs** (revs 42 and 59). 8 and 16 hits went to 0. Every hit was found with a bracketed regex and replaced by its exact character range, using the repo's wording ("the Department", "an enterprise Databricks workspace", "your ticketing system"). The README's mention of the realistic-names dataset was rewritten.

**Slides** (03:24 CDT, version 14). 34 hits in 19 slides went to 0, with exactly 34 word-level edits. The cover banner and the speaker notes were included. The deck's `notes` collection is empty.

**Handoff** (rev 42). Rewritten to the present: Status, Next steps, Repo and branch (fresh history, 677eb0e and 54e0f0e), Layout, Phase tracker (Phase 4 mostly done), Decisions (Tailscale replaces LAN-only), six new Gotchas, Standing rules, Open questions and Links.

**Left over.** claude-mem recorded the old page text from these reads (20 rows), and it is scrubbed with the usual procedure after this entry.

## 2026-10-26 · Employer tie-backs removed: a fresh, public repo

Following a friend's audit, the repo no longer links back to wrolfgar's employer. It was rebuilt as fresh history (one commit per branch), the old repo was deleted, and the new one carries the original name and is public with secret scanning and push protection. The words removed are deliberately not repeated in this log.

**Step 1, stop the exposure.** Repo made private (0 forks, 0 stars) and mirrored to `~/lnl-backup.git` on the VM, the one backup kept.

**Step 2, scrub both branches.** One ordered rule set was applied to the original files: the record key is now `offender_number`, the agency is "the Department", the six real unit names are fictional cities from the course's own crosswalk, a real ticketing product became "your ticketing system (ServiceNow, Jira, ...)", a real office name in the Databricks examples became `sandbox` and `restricted-readers`, and wording implying a real organization was made generic. The student handout canvas was edited and re-exported to PDF by wrolfgar.

- **Bugs caught by tests, not by eye:** a second rename would have cut into `sid_number`, so the rules ran once from the originals with whole-word patterns; capitalizing "Offender" at line starts also capitalized code names and broke the generator with a `NameError`, caught by the course run and fixed; one "a offender" became "an offender".
- **Course proof:** generated data byte-identical apart from the header; sessions 1 to 5 and the supply-orders notebook pass; sessions 6 and 7 fail identically before and after (an existing spaCy issue).

**Step 3, fresh history.** New repo with `main` (the course) and `duckdb-lakehouse` (adds only `lakehouse/` and `.gitignore`), each one commit by `pugwala`. A fresh clone from GitHub passed the friend's search, the PDF text check and the guard. The push first failed because the `gh` login lacked the `workflow` scope; wrolfgar added `workflow` and `delete_repo`. After wrolfgar confirmed, the old repo was deleted (backup verified identical first), the new one renamed to `lunch-and-learn-data-cleansing`, made public, and secret scanning and push protection enabled.

**Step 4, keep it out.** `tools/tieback_check.sh` (words written with a bracketed letter so the file itself stays clean; `--staged` mode; reads PDF text), a pre-commit hook (`git config core.hooksPath .githooks`, set on the VM), and a GitHub Action (passed on both branches). 5 bats tests, each shown to fail when its behaviour is broken.

**The VM.** Repo switched to the new remote; lake wiped and reloaded under `offender_number`; `daily_lake` run green; acceptance 27 of 27 (a new test checks the catalog's history, Parquet, landing CSVs and the repo), parity 18, bats 19 and 5, `bootstrap.sh --check` green. The first pipeline run's history (which named the old column) was deleted, along with the local working copies; only `~/lnl-backup.git` remains.

## 2026-10-25 · Phase 4, slice 2: Superset on Cube

Superset 6.1.0 runs at `/superset` on the Tailscale name, with Cube as its only database. All 5 of its acceptance tests pass, and the only-Cube rule was shown to catch a decoy database.

**Red first.** `acceptance/test_superset.py` was written first and failed for the right reasons: no `superset` host, no config file. It checks health under `/superset`, metadata kept in Postgres, Cube as the only database, the connection going to `cube:15432`, and 100,000 records from SQL Lab. The bats suite gained tests for three new secrets, both role scripts (`02` and `03`), building both images, seven services and the `/superset/` URL; it was red on exactly those, then 19 of 19 green.

**Built.**

- `superset/Dockerfile`: the official image has no database drivers, so it adds `psycopg2-binary` 2.9.13.
- `superset/superset_config.py`: secret key and metadata database from the environment, proxy headers trusted, analytics pixel off.
- `superset/start.sh`, idempotent on every start: migrations, admin user with its password reset from `.env`, roles, and Cube registered by URI.
- `postgres/init/03-superset.sh`: gives the existing `superset` database an owner role.
- Caddy: `/superset*` passed through with the path kept, because Superset's `SUPERSET_APP_ROOT` middleware strips it itself.

**Bugs found on the way.**

- `/superset/` answered an empty 200. The container's Caddyfile had 0 Superset lines while the disk had 3: a single-file bind mount keeps the old file when an editor saves a new one. Caddy and Superset now mount their folders. Afterwards `/superset/` gives 302, the API without a login gives 401, and the login page gives 200.
- The connection test read `sqlalchemy_uri` from the wrong endpoint; Superset 6 serves it at `/database/<id>/connection`.
- One full-suite run had 4 transient Dagster 500s right after `catalog-pg` restarted; the re-run was clean.

**Also this session.** wrolfgar asked that no Tailscale URLs go to GitHub. An audit found none in any file, commit or message. The fake test name was changed to the reserved `lakehouse.example.invalid` anyway, and every commit now scans for Tailscale details first.

**Totals.** Acceptance 22 (12 daily run, 5 Cube, 5 Superset), parity 18, bats 19; `bootstrap.sh --check` passes. Uncommitted pending wrolfgar's approval. Next: the Trust Test dashboard.

## 2026-10-25 · Old lake.home.arpa names retired

wrolfgar confirmed both Tailscale URLs work from the Mac, so `jupyter.lake.home.arpa` and `dagster.lake.home.arpa` were retired. Caddy now serves only `<tailnet-host>`.

- **Red first:** a bats test that `bootstrap.sh` never touches a `lake.home.arpa` URL, and a live check that the old names do not answer. Both were red: the test failed, and the names answered 302 and 401.
- **Removed:** the two LAN sites and their internal-CA setup from the Caddyfile; `LAKE_DOMAIN` from `compose.yaml`, `.env.example`, `bootstrap.sh`, the bats fixture and the VM's `.env` (rewritten in place: still mode 600, no extra ACL entries); and the LAN patterns from the fake `curl`.
- **Green:** bats 16 of 16; on the VM, both old names give no answer, both Tailscale URLs pass with a trusted certificate, and 17 acceptance and 18 parity tests pass.
- **wrolfgar's Mac:** the old hosts entries can go. Run `grep lake.home.arpa /etc/hosts` to see them, then `sudo sed -i '' '/lake\.home\.arpa/d' /etc/hosts` to remove only those lines.

## 2026-10-25 · Sites on the Tailscale name, with a real certificate

Jupyter and Dagster now live at `<tailnet-host>` and `/dagster/`, on a Let's Encrypt certificate issued through Tailscale. Any tailnet device can open them with no hosts entries and no browser warnings.

**wrolfgar's choices.** Paths rather than ports, because MagicDNS has no subdomains, so `jupyter.lakehouse…` cannot exist. The old `*.lake.home.arpa` names are kept until the new URLs are confirmed from the Mac. Tailscale HTTPS certificates were already enabled on the tailnet.

**Tests first.** bats gained tests for filling `LAKE_TS_HOST` from Tailscale and for checking the new URLs without `-k`, so an untrusted certificate fails. Both were red, then green. The live `bootstrap.sh --check` was red on exactly those three items before any routing change.

**Built.** Jupyter runs with base URL `/jupyter/` and Dagster with path prefix `/dagster`; Dagster's healthcheck and the acceptance test's GraphQL URL followed. Caddy has a new site for the Tailscale name, the tailscaled socket mounted, and `tls internal` on the LAN sites in place of the global `local_certs`, which would have overridden Tailscale. `route` keeps basic auth ahead of the redirect on the old Dagster name. `bootstrap.sh` fills `LAKE_TS_HOST` and gains a `set_env_key` helper, extracted as a refactor while the `.env` inode test stayed green.

**What went wrong, and the fix.** Caddy did not detect the `<tailnet-host>` name automatically. It asked Let's Encrypt directly, which cannot see a private name (NXDOMAIN). An explicit `tls { get_certificate tailscale }` fixed it. The first handshake timed out while Tailscale issued the certificate; after a full Caddy restart (a reload does not stop an ACME retry loop already running) the URLs answered 302 and 401, and there were 0 Let's Encrypt attempts.

**Smaller fixes, test-first.** URL checks printed `000000` for an unreachable site; a test made it red, then `|| true` fixed it. The closing message now shows the Tailscale URLs. Its first test passed for the wrong reason, because the URLs appear earlier in the output, so it was narrowed to the closing line, seen red, then made green.

**Result.** bats 15 of 15; on the VM every check passes, with 17 acceptance and 18 parity tests. wrolfgar got a Mac one-liner for `~/.ssh/config`: `Host lakehouse`, `HostName <tailnet-ip>`, `User claude`.

## 2026-10-25 · Tailscale on the VM

The VM is on wrolfgar's tailnet as `lakehouse` at <tailnet-ip> (`<tailnet-host>`), so Jupyter and Dagster are reachable away from home, still behind their logins.

**Checklist first.** A six-point check was written before installing: installed, service running, signed in, host DNS untouched, containers still resolve internet names, LAN address unchanged. It started with 3 failing (the first three) and ended with 0.

**Install.** Tailscale 1.104.2 from Tailscale's signed Debian trixie repository; `tailscaled` is enabled at boot. wrolfgar signed in with `sudo tailscale up --accept-dns=false` and approved the machine in his browser, so no key passed through chat.

**Settings, and why.**

- `--accept-dns=false`: MagicDNS would rewrite `/etc/resolv.conf` and could stop containers looking up internet names. Cube installs its DuckDB extensions at every start.
- Routes not accepted: a peer, `main-connector`, advertises 10.8.0.98/32, which the VM does not need.
- Tailscale SSH and exit node: off.

**Exposure.** The tailnet sees what the LAN already saw: Caddy on 80/443 (Jupyter 302 to its login, Dagster 401) and SSH on 22. Postgres stays on 127.0.0.1, and Cube is on the Docker network only. Tip for wrolfgar's Mac: point the `*.lake.home.arpa` names at <tailnet-ip> so they work at home and away.

## 2026-10-25 · Phase 4, slice 1: Cube over gold, read-only

Cube v1.8.3 now serves gold through a Postgres-wire SQL API at `cube:15432`, reading DuckLake read-only as `lake_ro`. All 5 acceptance tests pass, and the governance test was shown to catch a deliberate leak.

**The decision.** The plan feared Cube could not attach DuckLake. Its DuckDB driver does have an `initSql` option, set in code (`cube/cube.js`) rather than by environment variable. Cube's 1.6 long-term line bundles DuckDB 1.4, too old for our catalog, and every 1.8 release bundles DuckDB 1.5.5. wrolfgar approved v1.8.3, the newest release at least two weeks old, as a read-only exception to "DuckDB 1.5.6 everywhere". Superset will be 6.1.0, since 7.0 is still a release candidate.

**The spike.** A throwaway container ran Cube's exact DuckDB library, `@duckdb/node-api` 1.5.5. As `lake_ro`, read-only, it attached the lake and read 100,000 gold rows and a minimum score of 94.15, and its write was refused.

**Red first.** `lakehouse/acceptance/test_cube.py` was written before any Cube code and failed for the right reasons: no `cube` host, and no `cube` service in compose.

**Built.**

- `cube/cube.js`: `driverFactory` with an `initSql` that attaches the lake `READ_ONLY` as `lake_ro`. The driver logs and skips a failing `initSql`, so the tests check real answers, not just a healthy container. Models name tables in full (`lake.gold.*`), because `initSql` runs once per DuckDB instance and a `USE` would not reach Cube's other connections.
- `cube/model/`: `offender_records`, joined to `units` and `offenses`, with record count, records with exceptions, total restitution and average disciplinary points; and `dq_scorecard`, with a pass rate rounded as gold does. Restricted columns (race, religion, STG) are left out until Phase 5 adds masking.
- `compose.yaml`: a `cube` service with the read-only password only, the data folder mounted read-only, telemetry off, and a healthcheck through Node's `fetch` (the image has no `curl`). Jupyter gets `CUBE_SQL_PASSWORD` for queries and tests.
- `bootstrap.sh`: two new secrets and a sixth service, test-first. The bats suite was red on exactly those two expectations, then 11 of 11 green. On the VM it generated only the two missing secrets, left the existing ones unchanged, and brought Cube up healthy.

**Green, and proven.** 5 of 5 Cube tests pass: read-only configuration, 100,000 records, scorecard pass rates equal to gold, the single 94.15% rule, and no personal or restricted columns. A deliberate leak of `race_code` turned the governance test red; restoring the file turned it green. Totals: 18 parity, 17 acceptance, 11 bats. README updated.

## 2026-10-25 · Handoff doc brought up to date; sudo stays

The Home Lakehouse Handoff doc now describes the lakehouse as it stands, so a new session can start from it without this log.

- **Rewritten:** Status right now and Next steps (snapshot, health check, Phase 4).
- **Corrected:** the environment table (IP confirmed, both disks with their stable names, root at 79 GB) and the access paragraph (Claude runs on the VM).
- **Added:** four commits, three files in the layout, eight gotchas from today, and the six standing rules under Working with wrolfgar.
- **Phase tracker:** phases 0, 1 and 2 now show Done.
- **Resolved:** the `/lake` open question is ticked, and dbt on DuckLake is off the not-yet-proven list.

**Decision:** wrolfgar keeps `claude`'s passwordless sudo and `docker` group membership permanently, so Claude can always work on this machine, with a request to be careful. That means read-only checks first, stable disk names, asking before anything irreversible, secrets shown only as names, and checking after every change. Saved to memory.

## 2026-10-25 · Step 5: first daily\_lake run, green

wrolfgar launched `daily_lake` from the Dagster UI. Run `12ba5af1` succeeded, and the acceptance test written before it went from 12 red to 12 green.

**The run.** `load_lake` took 7.5 s and `gold` (dbt build) 5.5 s. dbt-duckdb's create-then-rename table build, the handoff's main worry for this step, worked on DuckLake first time.

**Checks inside the run.** Dagster recorded 21 checks: the blocking parity check passed, and the only one not passing is `dq_score_floor` at WARN severity, the expected 95% alarm. Dagster shows 21 rather than dbt's 26 tests because tests spanning two tables, such as gold row count equals silver, run inside `dbt build` without their own asset check.

**Acceptance test, green.** All 12 pass: run SUCCESS; silver and both gold tables built by this run; gold built from the newest load; 100,000 records with no personal fields; dimensions populated; per-dimension scores equal to the sandbox to two decimals; and only `disciplinary_points` completeness, at 94.15%, under the floor. Committed with the README test table as `4511413`.

## 2026-10-25 · New standing rule: every function has a docstring

Every function written or changed from now on gets a docstring; in bash, where there are none, a one-line comment directly above it. Test docstrings state the promise being checked, because that is what you read when a test fails. Checked with a short Python `ast` scan before committing.

## 2026-10-25 · Step 5 acceptance test, written before the run

`lakehouse/acceptance/test_daily_run.py` defines what a successful first `daily_lake` run must prove. It is red now, for the right reasons: Dagster has no `daily_lake` run yet, and the `gold` schema has no tables.

**Why its own folder.** The pipeline's blocking parity check runs `pytest` on all of `lakehouse/tests/` during the run, before gold exists (`definitions.py`, line 88). A post-run test there would fail inside the run and block the gold build it is meant to check. After adding the file, `pytest lakehouse/tests` still collects exactly 18 tests.

**What it checks (12 tests).** The latest `daily_lake` run has status `SUCCESS`, read from Dagster's GraphQL API. That same run materialized silver and both gold tables. The scorecard's `run_id` is the newest load in `ops.load_runs`. The fact table has 100,000 rows and 100,000 distinct offenders, and none of the personal fields (names, alias, birth date, conduct notes, and their `_std` forms). All three dimensions have rows. The per-dimension pass rates match the sandbox: completeness 96.89, conformity 99.79, consistency 99.81, validity 99.99, uniqueness 100, timeliness 100. And only one rule is under the 95% floor: `disciplinary_points` completeness at 94.15.

**Red, checked.** All 12 fail: 4 with "no daily\_lake run yet" and 8 with "table does not exist" or "has no columns". The GraphQL asset query was run on its own and answers `None` (never built) rather than an error, so the red is not a typo.

**Docstrings.** A scan found 11 of 13 functions without one; after adding them it finds 0, and the test results are unchanged.

**Run it:** `docker compose --profile core exec -T jupyter pytest -q lakehouse/acceptance`

## 2026-10-25 · bootstrap.sh gets tests, and the tests find a bug

`lakehouse/tests/bootstrap.bats` holds 10 tests. All pass, every one was shown to fail when its behaviour is broken, and writing them exposed a real bug in the pushed script.

**How the tests work.** Each runs the script in a throwaway repo, with fake `docker`, `findmnt`, `blkid`, `lsblk`, `curl` and `sudo` first on `PATH`. The fakes log their arguments and return whatever the test sets up, so nothing touches real disks, `.env` or containers. Run them with `bats lakehouse/tests/bootstrap.bats` (Debian package `bats` 1.11.1).

**Red, for real: a silent exit.** The test "generates only missing secrets" failed against the pushed script. When a key is absent from `.env` altogether, `grep` exits 1, `set -o pipefail` fails the pipeline, and `set -e` ends the script with no message. That is exactly the upgrade case of an old `.env` with no `DAGSTER_PG_PASSWORD`. Green: `{ grep … || true; }` in `env_val`.

**Red, for the tests themselves.** shellcheck warned (SC2314) that in bats a line starting with `!` never fails a test; bash exempts it from `set -e`, and only a test's last line counts. To prove it, a mutation that made `--check` build and start services survived the "--check changes nothing" test. Green: a `not_called` helper function, whose failure does stop the test; the same mutation was then killed.

**Mutation proof.** For tests added to existing code, each one is proven by breaking what it guards in a temporary copy of the script (`BOOTSTRAP=<copy> bats -f <test>`) and requiring red. Final score: 14 of 14 mutations killed, including `mv` instead of an in-place rewrite of `.env`, `getfacl` without `-n`, a bare `up`, and `--check` ignored.

**Also.** The live VM still passes `bootstrap.sh --check`. The README test table now lists the bats suite and step 4's results.

## 2026-10-25 · New standing rule: TDD, red-green

From now on every change is test-first: write the test, run it and see it fail for the right reason (red), make the smallest change that passes (green), then tidy up with the tests still green. The test is committed with the change.

- Python and Dagster code: pytest in `lakehouse/tests/`. dbt: dbt tests first, then the model.
- Shell scripts: automated tests with stubs (a fake `docker` on `PATH`), never against the live stack.
- Infrastructure changes: write the check first, show it failing, make the change, show it passing.

## 2026-10-25 · bootstrap.sh: one command to set up, upgrade and verify

`lakehouse/scripts/bootstrap.sh` (commit `19fcde8`) replaces the README's manual recipes. It checks before every change, so a run on this healthy VM took 3.6 s and changed nothing: same `.env` fingerprint, same containers, same data files.

**Steps.** Tools; data disk (stops, never formats, if `/lake` isn't a mounted disk); `/lake` ownership; repo ACLs; secrets (generates only missing ones, refuses duplicate keys, keeps mode 600); image build, `dagster` role, the five services by name, Caddy reload; loader only if the lake is empty; then health checks, the 18 parity tests and both sites through Caddy. `--check` verifies only; `--reload` forces a load.

**Why it was needed.** The old upgrade recipe appended `DAGSTER_PG_PASSWORD` to `.env` with `>>`, which is how today's duplicate key appeared, and both recipes used `up -d --build`, which also starts the loader.

**Tested by hand, before the TDD rule.** Check mode on the live VM; a full run with before/after fingerprints; failure cases on a throwaway copy (unmounted disk, duplicate key, unset secrets); secret generation with a fake `docker` stub. Those tests found three bugs: `getfacl` prints user names unless given `-n`; the unmounted-disk message gave wrong advice when the disk was mounted elsewhere; and failed builds didn't stop the script. Automated tests are still to come.

**Also in the commit.** `set-dagster-ui-password.sh` now re-locks `.env` after its `sed -i`, and the default UI user is `admin` instead of a first name.

## 2026-10-25 · Step 4: Dagster up, three hidden faults fixed

Dagster's webserver and daemon are running and healthy, the loader wrote snapshot 31, and 18/18 parity tests pass on the new image. None of the three faults was among the handoff's predicted causes.

**Role.** `02-dagster.sh` created the `dagster` role; a network login as `dagster` worked. Before running it, compared SHA-256 fingerprints to confirm the `catalog-pg` container and `.env` held the same password.

**Fault 1: wrong Postgres driver.** Both containers crash-looped with `ModuleNotFoundError: No module named 'psycopg'`. SQLAlchemy was an unpinned transitive dependency, and pip took 2.1.6, which maps `postgresql://` to the psycopg 3 driver. `dagster-postgres` builds that URL but installs psycopg2. Fix: pinned `SQLAlchemy==2.0.54` in `jupyter/requirements-lake.txt` (2.0.55 was only 9 days old). Only the last image layer rebuilt, in about 15 s.

**Fault 2: dbt reads `.env`.** Code loading failed with `PermissionError` on `lakehouse/.env`. dbt 1.12 calls `load_dotenv(find_dotenv(usecwd=True))` at startup, walking up from its working folder, with no setting to stop it. Making `.env` readable would have handed every stack password to dbt. Fix: `compose.yaml` mounts `/dev/null` over `lakehouse/.env` in every container that mounts the repo (x-dagster, jupyter, load-lake). Containers now see an empty file; Compose still reads the real one on the host.

**Fault 3: false "unhealthy".** Dagster inherited the Jupyter base image's healthcheck, which can never pass without a Jupyter server. Dagster itself was fine. Fix: own healthchecks in `compose.yaml`: `curl` on `/server_info` for the webserver, `dagster-daemon liveness-check` for the daemon.

**Loader and checks.** `docker compose run --rm load-lake`: 100,000 rows, 3,288 flagged values on 3,249 records, 7 reference tables, 6.2 s, snapshot 31. `ref.null_tokens` has 5 tokens. Restarted Caddy to load the Dagster site: `dagster.lake.home.arpa` returns 401 (basic auth) and `jupyter.lake.home.arpa` returns 302.

**Worth knowing.**

- `--profile core up -d` with no service names also starts the one-shot `load-lake` loader. Name the five long-running services instead.
- Known, accepted conflict: `grpcio-status` wants `protobuf>=7.35`, but dbt and Dagster need `<7`. It comes only from `pyspark[connect]` in the course's own requirements, which can't change, and the course uses classic local PySpark, not Spark Connect.
- Installed `tmux` 3.5a at wrolfgar's request.

## 2026-10-25 · claude-mem installed, local only

claude-mem v15.0.2 now records Claude Code sessions on the VM. It summarizes them with wrolfgar's own Anthropic plan, with cloud sync and telemetry off.

**Choices wrolfgar made.** Use the Anthropic-plan provider rather than the installer's default hosted CMEM Pro service, so session content (IPs, network layout, work context) never goes to a third party. Pin v15.0.2 rather than the latest release, because the project shipped six releases in eight days and two of them on install day.

**Install steps.**

1. Node.js 20.19.2 from Debian's own repo (`apt install nodejs npm`); claude-mem needs Node 20 or newer.
2. `CLAUDE_MEM_ONLINE_OPTIN=false npx -y claude-mem@15.0.2 install --provider claude`. The first run stopped because Bun's installer needs `unzip`; installed it and re-ran.
3. Telemetry (PostHog) is on by default, and its consent prompt is skipped in non-interactive installs, so it was on. Turned off with `npx claude-mem@15.0.2 telemetry disable`; status now reads DISABLED. The `~/.local/bin/claude-mem` launcher only runs hooks, so management commands need the `npx` form.

**Verified after a Claude Code restart.** The worker answers on `127.0.0.1:37701` (this VM only) with provider `claude`. All eight hooks are registered and the session was captured. `~/.claude-mem` is mode 700. The small `claude-mem.db` is normal: SQLite WAL mode keeps new writes in `claude-mem.db-wal` until a checkpoint.

**Caveats.** The install-time telemetry events (version, OS, provider) were probably sent before the disable. A dependency (`kysely`) warns that it wants Node 22, but the worker runs on Bun and is healthy. Wrap anything sensitive in `<private>` tags to keep it out of memory.

## 2026-10-25 · Root disk grown, gh set up, image rebuilt

The OS disk's root filesystem is now 79 GB, `gh` pushes and pulls as `pugwala`, and the shared image rebuilt cleanly with CPU-only PyTorch.

**Root disk.** Proxmox had already grown the disk to 80 GB, but the partition was still 40 GB. After confirming `/` is partition 1 of the 80 GB disk, ran `sudo growpart /dev/sdb 1` (moves the partition's end; the start stays at sector 262144, so no data moves) and `sudo resize2fs /dev/sdb1` (grows ext4 into the new space while mounted). Result: 79 GB, 57 GB free.

**GitHub CLI.** Installed `gh` 2.103.2 from GitHub's signed apt repository (key in `/etc/apt/keyrings/`, source in `/etc/apt/sources.list.d/github-cli.list`). wrolfgar signed in with the device flow (`gh auth login --web`), so no token passed through chat. `gh auth setup-git` makes git use the `gh` login. The token file `~/.config/gh/hosts.yml` is mode 600; scopes are `repo`, `read:org`, `gist`.

**Image rebuild.** Cleared the build cache, pulled `8c573ad`, then ran `docker compose --profile core build`. The log shows `torch-2.14.1+cpu` and no `nvidia-*` packages. Image `lnl-jupyter:local` is 10.4 GB; the disk is 39% used afterwards.

**.env fixes.** Two found before the build:

- `DAGSTER_PG_PASSWORD` appeared twice with different values. Postgres had no `dagster` role yet, so neither was in use; removed the first line (Compose uses the last value anyway).
- Editing with `sed -i` replaced the file, and the new file inherited the repo's default ACL, giving uid 1000 (the container user) read-write access. Fixed with `setfacl -b .env && chmod 600 .env`. Rule: after any edit to `.env`, check that `stat -c %a .env` prints 600.

## 2026-10-25 · Data disk formatted and /lake moved onto it

The 200 GB data disk had never been formatted, so `/lake` was a plain folder on the 40 GB OS disk. It now holds `/lake`, and all 18 parity tests pass on it.

**What we found.** `findmnt /lake` said it was not a mountpoint. `blkid` found no filesystem and no `lake` label, and the disk's first 1 MiB was all zeros. The fstab line `LABEL=lake /lake ext4 defaults,noatime,nofail 0 2` mounts by label, and `nofail` lets boot continue when that label is missing, so every boot skipped it silently. The Phase 0 tracker entry "data disk formatted" was wrong.

**What we did.**

1. Identified the disk by its stable Proxmox name rather than `sda`/`sdb`, which swap between boots: `scsi0` is the 80 GB OS disk and `scsi1` is the 200 GB data disk.
2. With wrolfgar's approval, formatted it: `sudo mkfs.ext4 -L lake /dev/disk/by-id/scsi-0QEMU_QEMU_HARDDISK_drive-scsi1`. The command first checked the size was exactly 200 GiB.
3. Stopped the stack, renamed the old folder to `/lake.ondisk`, made an empty `/lake`, and ran `sudo mount -a`.
4. `rsync` isn't on the cloud image, so copied with `sudo cp -a --preserve=all /lake.ondisk/. /lake/`, which keeps owners, permissions, ACLs and extended attributes.
5. Verified: 100,754 KB and 46 files on both sides, and `diff -r` found no differences.
6. Restarted `catalog-pg`, `jupyter` and `caddy` and ran `pytest -q lakehouse/tests`: **18 passed**, so the Postgres catalog still matches the Parquet files.
7. Deleted `/lake.ondisk`.

**Side note.** `caddy` has `depends_on: dagster-webserver` (`compose.yaml:119`), so starting Caddy also started the Dagster webserver. It exited with code 127 (command not found) because the old image has no Dagster, so it was stopped until the rebuild.
