"""The handoff between the two courses: course 1's cleansed output, published as pinned files for course 2.

Course 2 starts where course 1 ends (the boundary document, 2026-11-02), so it never runs course 1's code or reads
its live tables. The two meet through files:

    course 1     publishes (course1/lnl/publish.py, python -m lnl.publish --out DIR): runs its own code, checks the
                 19 Facilitator Guide numbers (course1/lnl/parity.py), and only then writes one Parquet file per table
                 plus a manifest of fingerprints. Both moved to course 1 at course1-v1.2 (2026-11-03).
    receive.py   course 2's side: what it accepts (contract.yml: tables, keys, column types), adopting a version
                 that keeps it (course1.lock.json), the check that the files on disk are exactly that version, where
                 that version lives (receive where), and a DuckDB connection that reads them; lake.run() lands them
                 in the lake
"""
