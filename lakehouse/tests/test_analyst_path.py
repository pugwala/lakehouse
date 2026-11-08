"""The analyst path: aliases for everyone, real names only on the engineering path (2026-11-07).
    pytest -q lakehouse/tests/test_analyst_path.py     # no stack needed: CI runs this

wrolfgar: "everyone needs access to aliases", with real names restricted. A hero's or villain's alias (their common
name) is public; their real first and last names are not. Two doors into the data:
  - the analyst path: the analyst Jupyter at /analyst/, whose %sql (analyst/cube_sql.py) talks to Cube's SQL API
    only. Cube serves gold through views that carry common names and never a real name. The container holds no
    lake files, no catalog password, and sits on the analyst network with only Cube and Caddy;
  - the engineering path: the lab Jupyter at /jupyter/ (lakehouse.sql_magic, the raw lake as lake_ro), where the
    cleaning lessons need the names. It is restricted: real names are tagged Sensitivity.Restricted in dbt, so
    OpenMetadata, the tags tools and the agent all say so.
acceptance/test_analyst_path_live.py checks the running stack.
"""
import ast
import re
from pathlib import Path

import yaml

LAKEHOUSE = Path(__file__).resolve().parents[1]
COMPOSE = yaml.safe_load((LAKEHOUSE / "compose.yaml").read_text())
SERVICES = COMPOSE["services"]
ANALYST = SERVICES.get("analyst-jupyter", {})
CUBE_SQL = LAKEHOUSE / "analyst" / "cube_sql.py"
LAKE_SECRETS = {"LAKE_RO_PASSWORD", "LAKE_RW_PASSWORD", "PGPASSWORD", "LAKE_CATALOG", "LAKE_DATA_PATH",
                "CUBEJS_API_SECRET", "MCP_TOKEN", "OM_ADMIN_PASSWORD", "OM_MCP_PASSWORD", "JUPYTER_TOKEN"}
REAL_NAMES = {"first_name", "last_name", "first_name_std", "last_name_std"}


def dbt_columns(path, model=None, source_table=None):
    """{column: sensitivity} for one model (models file) or one source table (sources.yml)."""
    doc = yaml.safe_load(path.read_text())
    if model:
        entry = next(m for m in doc["models"] if m["name"] == model)
    else:
        schema, table = source_table.split(".")
        src = next(s for s in doc["sources"] if s["schema"] == schema)
        entry = next(t for t in src["tables"] if t["name"] == table)
    return {c["name"]: (c.get("meta") or {}).get("sensitivity") for c in entry.get("columns", [])}


# ---- The analyst container -----------------------------------------------------------------------------------

def test_analyst_jupyter_holds_only_the_cube_login():
    """Its environment has the Cube SQL password and its own token, and none of the lake's or other apps' secrets."""
    env = ANALYST["environment"]
    assert env["CUBE_SQL_PASSWORD"].startswith("${CUBE_SQL_PASSWORD")
    assert env["JUPYTER_TOKEN"].startswith("${ANALYST_JUPYTER_TOKEN")
    assert not (set(env) - {"JUPYTER_TOKEN", "CUBE_SQL_PASSWORD", "CUBE_SQL_HOST", "PYTHONPATH"}), set(env)
    assert "ANALYST_JUPYTER_TOKEN" not in SERVICES["jupyter"]["environment"]


def test_analyst_jupyter_mounts_no_lake_and_no_repo():
    """Only the read-only analyst/ folder and its own notebooks volume: no /lake, no repo (it holds .env)."""
    vols = ANALYST["volumes"]
    assert "./analyst:/home/jovyan/analyst:ro" in vols
    assert "analyst-notebooks:/home/jovyan/work" in vols
    assert len(vols) == 2, vols
    assert "analyst-notebooks" in COMPOSE["volumes"]
    assert not ANALYST.get("ports"), "reached through Caddy only"


def test_analyst_network_holds_only_cube_and_caddy():
    """The analyst network is internal (no internet, no host); only Cube and Caddy join it besides the analysts."""
    assert COMPOSE["networks"]["analyst"]["internal"] is True
    assert ANALYST["networks"] == ["analyst"]
    on_it = {name for name, s in SERVICES.items() if "analyst" in (s.get("networks") or [])}
    assert on_it == {"analyst-jupyter", "cube", "caddy"}
    for name in ("cube", "caddy"):
        assert "default" in SERVICES[name]["networks"], f"{name} must stay on the default network too"


def test_caddy_serves_the_analyst_jupyter_at_analyst():
    """https://<LAKE_TS_HOST>/analyst/ goes to analyst-jupyter, which runs with base_url /analyst/."""
    caddyfile = (LAKEHOUSE / "caddy" / "Caddyfile").read_text()
    assert re.search(r"handle /analyst\* \{\s*reverse_proxy analyst-jupyter:8888\s*\}", caddyfile)
    assert "--ServerApp.base_url=/analyst/" in ANALYST["command"]
    assert "analyst-jupyter" in SERVICES["caddy"]["depends_on"]


def test_bootstrap_and_monitoring_know_the_analyst_site():
    """bootstrap.sh makes its token, starts it and checks /analyst/; blackbox probes it; .env.example lists it."""
    boot = (LAKEHOUSE / "scripts" / "bootstrap.sh").read_text()
    assert re.search(r"^SECRETS=\([^)]*\bANALYST_JUPYTER_TOKEN\b", boot, re.M | re.S)
    assert re.search(r"^SERVICES=\([^)]*\banalyst-jupyter\b", boot, re.M)
    assert '"analyst:302"' in next(l for l in boot.splitlines() if l.startswith("for pair in"))
    assert 'site: analyst' in (LAKEHOUSE / "monitoring" / "prometheus" / "sites.yml").read_text()
    assert re.search(r"^ANALYST_JUPYTER_TOKEN=CHANGE_ME$", (LAKEHOUSE / ".env.example").read_text(), re.M)


# ---- The analyst %sql ------------------------------------------------------------------------------------------

def test_cube_sql_talks_to_cube_only():
    """analyst/cube_sql.py builds a Postgres-wire URL to cube:15432 as user lake, and imports nothing of the lake."""
    tree = ast.parse(CUBE_SQL.read_text())
    imported = {a.name.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
    imported |= {n.module.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module}
    assert not imported & {"lakehouse", "duckdb", "lnl"}, imported
    assert all(ast.get_docstring(f) for f in ast.walk(tree) if isinstance(f, ast.FunctionDef))
    import importlib.util
    spec = importlib.util.spec_from_file_location("cube_sql", CUBE_SQL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    url = mod.cube_url({"CUBE_SQL_PASSWORD": "pw"})
    assert url.drivername == "postgresql+psycopg2" and url.host == "cube" and url.port == 15432
    assert url.username == "lake" and url.database == "cube" and url.password == "pw"


# ---- Real names are restricted ---------------------------------------------------------------------------------

def test_real_names_are_restricted_and_aliases_are_not():
    """Real first and last names are Sensitivity.Restricted in all four tables that hold them; aliases stay
    personal (public as common names in gold, but not restricted)."""
    models = LAKEHOUSE / "dbt" / "models"
    tables = {"world_silver.person": dbt_columns(models / "world" / "silver" / "schema.yml", model="ws_person"),
              "world_bronze.person": dbt_columns(models / "world" / "bronze" / "schema.yml", model="wb_person"),
              "silver.hero_offenders": dbt_columns(models / "sources.yml", source_table="silver.hero_offenders"),
              "bronze.hero_offenders_raw": dbt_columns(models / "sources.yml",
                                                       source_table="bronze.hero_offenders_raw")}
    for table, cols in tables.items():
        names = {c for c in cols if c in REAL_NAMES}
        assert {"first_name", "last_name"} <= names, table
        assert all(cols[c] == "restricted" for c in names), (table, {c: cols[c] for c in names})
        assert cols.get("alias") == "personal", table


def test_the_rule_says_which_door_and_is_enforced_live():
    """The rulebook's common-name rule names both paths and is enforced by the analyst path's acceptance tests."""
    glossary = yaml.safe_load((LAKEHOUSE / "glossary" / "glossary.yml").read_text())
    rule = next(r for r in glossary["rules"] if r["name"] == "A common name is public, a real name is not")
    assert "analyst" in rule["statement"] and "engineering" in rule["statement"]
    assert "test:test_analyst_path_live.py::test_cube_sql_offers_no_real_name" in rule["enforced_by"]
    assert "test:test_analyst_path_live.py::test_real_names_are_restricted_in_openmetadata" in rule["enforced_by"]
