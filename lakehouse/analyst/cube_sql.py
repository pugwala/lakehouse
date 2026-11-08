"""IPython extension: jupysql's %sql connected to Cube's SQL API, the analysts' way into the data.

In the analyst Jupyter (https://<LAKE_TS_HOST>/analyst/):

    %load_ext cube_sql
    %sql SELECT common_name, MEASURE(participations) FROM fight_participants GROUP BY 1 ORDER BY 2 DESC LIMIT 10

In the lab Jupyter it is `%load_ext lakehouse.analyst.cube_sql`. Cube serves the data products' views and cubes
over gold, so heroes and villains come back by their common names (aliases) and never by a real name; measures
are asked for with MEASURE(). Cube speaks the Postgres wire protocol as user "lake" (CUBE_SQL_PASSWORD). This
file imports nothing from the lake: the analyst container holds no lake files and no catalog password, so the
raw lake (lakehouse.sql_magic, the engineering path) is out of its reach.
"""
import os

from sqlalchemy.engine import URL

ALIAS = "cube"


def cube_url(env=None):
    """The SQLAlchemy URL for Cube's SQL API, from CUBE_SQL_PASSWORD (and CUBE_SQL_HOST, default cube)."""
    env = os.environ if env is None else env
    return URL.create("postgresql+psycopg2", username="lake", password=env["CUBE_SQL_PASSWORD"],
                      host=env.get("CUBE_SQL_HOST", "cube"), port=15432, database="cube")


def load_ipython_extension(ip):
    """Load jupysql and connect %sql to Cube under the alias "cube"."""
    from sqlalchemy import create_engine
    ip.run_line_magic("load_ext", "sql")
    ip.user_ns["_cube_engine"] = create_engine(cube_url())
    ip.run_line_magic("sql", f"_cube_engine --alias {ALIAS}")
