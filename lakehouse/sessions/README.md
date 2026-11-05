# World sessions: course 2's cleaning sessions on the expanded world

Four notebooks, one cleaning skill each. Course 1's single flat table couldn't teach these skills; the expanded
world's 16 tables and their links can. Each works on the **messy files**, as source systems delivered them
(`/lake/landing/universe/M/messy/`). Each exercise is checked against the world's **answer keys**: the generator's own
record of every mess it made. Nothing here changes the lake.

> ⚠️ **Mock data only.** Every person, place and record in the world is invented.

| Notebook | Skill | Course 1 counterpart |
| --- | --- | --- |
| `world_1_who_is_who.ipynb` | Find the people entered twice: SID first, then a match key of cleaned name and birth date | Session 2 (one record, one key) |
| `world_2_dates_that_lie.ipynb` | Read every date format, with a written two-digit-year rule; catch charges filed before their fight | Session 3 (dates) |
| `world_3_links_that_break.ipynb` | Check every link with an anti-join; re-point links to duplicates | None: course 1 had one table |
| `world_4_finding_names.ipynb` | Find SIDs, phones, birth dates and names in 200,000 free-text reports, for redaction | Sessions 6 and 7 (text) |

## Running them

Open JupyterLab at `https://<LAKE_TS_HOST>/jupyter/` and go to `lakehouse/sessions/`. Run each notebook top to bottom.
The setup cell finds the course files and opens a DuckDB connection, `con`, with one view `messy_<table>` per messy
CSV folder. The world must be built at M (`world_refresh`); the last section of each notebook reads the lake
read-only, to show how silver does the same job.

Like course 1's sessions:
- 🧪 **Your turn** cells hold a `___` blank;
- the check under each one prints ✅ or ❌ with a hint;
- answers are at the bottom.

A number is checked exactly. A result, meaning the rows you found, is graded by:
- **precision:** how many of yours are right;
- **recall:** how many of the right ones you found.

Each graded result has a bar for both. The checks live in `check.py`, which is the only code that reads the answer
keys.

## Facilitator notes: what the answers give (scale M, 2026-11-04)

| Session | Exercise | Answer |
| --- | --- | --- |
| 1 | Duplicates by SID alone | 1,760 (of 8,877 people entered twice: only villains have a SID) |
| 1 | Last names that are stand-ins (`N/A`, `UNK`, `?`, blanks ...) | 5,089; `trim()` alone gives 4,953, because 136 cells are a lone tab |
| 1 | Duplicates by SID, then cleaned last name, first name and birth date | 8,451 of 8,509 right (precision 99.3%), 95.2% of 8,877 found; bar 99% / 90% |
| 2 | Filing dates that can't be read | 8,975 |
| 2 | Every readable filing date, read as written | 891,025 of 891,025; bar 99.9% / 99.9% |
| 2 | Charges filed before their fight | 3,546 of 3,546 right, 99.0% of 3,581 found; bar 99% / 95% |
| 3 | Participants pointing at a missing fight | 11,785 |
| 3 | Participants pointing at a missing person | 12,067 |
| 3 | Links to a duplicate, re-pointed to the original | 34,965 of 35,281 right (99.1%), 95.5% of 36,610; bar 99% / 85% |
| 4 | SIDs, seven spellings | 78,634 of 78,634, all found |
| 4 | Phone numbers, three formats | 86,852 of 86,852, all found |
| 4 | Birth dates after `DOB` | 166,524, all right; 94.5% of 176,272 found; bar 99% / 90% |
| 4 | Names, by context and then repeats | 432,239 of 446,039 right (96.9%), 91.1% of 474,602; bar 95% / 85% |

**Points worth a pause:**
- **Session 1:** a key with an unknown part must match nothing. Merging two strangers is worse than missing one
  duplicate.
- **Session 2:** a readable date can still be false, and the lake flags it rather than swapping in a guess.
- **Session 3:** orphans are kept and flagged; the event happened even if its parent row was lost.
- **Session 4:** names have no shape, so a finder misses some. That's why the lake still treats its redacted copy
  (`world_gold.incident_report_redacted`) as personal.

## Tests

- `pytest lakehouse/tests/test_sessions_check.py`: the grading itself, with no world needed; CI runs it.
- `pytest lakehouse/acceptance/test_world_sessions.py`: each notebook runs top to bottom in a real kernel, twice:
  - as delivered, every check asks for its answer;
  - with the Answers section filled in, every check passes against the keys.

  It takes about 40 seconds.
