"""Acceptance test: aliases for everyone, real names only on the engineering path (2026-11-07).
    docker compose --profile core exec -T jupyter pytest -q lakehouse/acceptance/test_analyst_path_live.py

Needs the stack after om_sync.py has run with the new sensitivity tags. Analysts query through Cube's SQL API (the
analyst Jupyter's %sql, Superset, the agent): every table it serves is a view or cube over gold, and none offers a
real name, a birth date or a SID, while common names are there to group by. The real names that silver and bronze
keep for the cleaning lessons are tagged Sensitivity.Restricted in OpenMetadata, and no longer Personal (the
classification is mutually exclusive). The analyst container's own walls (no lake files, no catalog, no secrets)
are checked from inside it by analyst/selfcheck.py, which bootstrap.sh runs.
"""
import importlib.util
from pathlib import Path

import psycopg2
import pytest
from sqlalchemy import create_engine, text

from test_cube import CUBE_SQL, rows
from test_products import get, om  # noqa: F401  (om: fixture)

LAKEHOUSE = Path(__file__).resolve().parents[1]
PRIVATE = {"first_name", "last_name", "first_name_std", "last_name_std", "birth_date", "date_of_birth",
           "sid_number", "alias"}
REAL_NAME_TABLES = ["world_silver.person", "world_bronze.person", "silver.hero_offenders",
                    "bronze.hero_offenders_raw"]


def cube_sql_module():
    """analyst/cube_sql.py, loaded from its file (the analyst Jupyter imports it as cube_sql)."""
    spec = importlib.util.spec_from_file_location("cube_sql", LAKEHOUSE / "analyst" / "cube_sql.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def cube():
    """A connection to Cube's Postgres-wire SQL API, as the analysts' %sql makes it."""
    conn = psycopg2.connect(**CUBE_SQL, connect_timeout=10)
    conn.autocommit = True
    yield conn
    conn.close()


def test_cube_sql_offers_no_real_name(cube):
    """No table Cube's SQL API serves has a real name, birth date, SID or raw alias column; common_name is there."""
    cols = rows(cube, "SELECT table_name, column_name FROM information_schema.columns "
                      "WHERE table_schema = 'public'")
    assert cols, "Cube's SQL API listed no columns"
    leaks = sorted((t, c) for t, c in cols if c in PRIVATE)
    assert not leaks, leaks
    assert ("fight_participants", "common_name") in cols
    tables = {t for t, _ in cols}
    assert not tables & {"person", "hero_offenders", "hero_offenders_raw"}, tables


def test_the_analyst_sql_answers_with_common_names():
    """The analysts' engine (analyst/cube_sql.py) ranks the busiest villains by common name."""
    engine = create_engine(cube_sql_module().cube_url())
    with engine.connect() as conn:
        top = conn.execute(text("SELECT common_name, MEASURE(participations) FROM fight_participants "
                                "WHERE person_role = 'villain' AND common_name IS NOT NULL "
                                "GROUP BY 1 ORDER BY 2 DESC LIMIT 3")).fetchall()
    assert len(top) == 3 and all(isinstance(n, str) and n for n, _ in top), top


def test_real_names_are_restricted_in_openmetadata(om):  # noqa: F811  (om: fixture)
    """first_name and last_name carry Sensitivity.Restricted, and not Personal, in every table that keeps them."""
    for table in REAL_NAME_TABLES:
        t = get(om, f"tables/name/lakehouse.lake.{table}", fields="columns,tags")
        tags = {c["name"]: {x["tagFQN"] for x in c.get("tags") or []} for c in t["columns"]}
        for col in ("first_name", "last_name"):
            assert "Sensitivity.Restricted" in tags[col], (table, col, tags[col])
            assert "Sensitivity.Personal" not in tags[col], (table, col, tags[col])
        assert "Sensitivity.Restricted" not in tags["alias"], table
