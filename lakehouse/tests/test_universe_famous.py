"""The expanded world's famous cast (common names, chunk 2, 2026-11-07): the heroes and villains everyone knows.
    pytest lakehouse/tests/test_universe_famous.py     # inside the jupyter container; needs the lake (silver)

Ian: queries are only meaningful for teaching if they answer with names people know. So the world casts famous
heroes (SUPERMAN, WONDER WOMAN, WOLVERINE, ...) and villains (JOKER, MAGNETO, LOKI, ...) as regulars: each is one new
hero or new villain (the first of each block, so every scale has them), born 1955-1980 so most are active by the
late 1990s, kept out of the uniform draws and placed instead as the lead hero or lead villain of a share of fights,
the better known more often. One scale-S build is made into a temporary folder and checked:
  - the cast lists hold the names Ian asked for, each once, in the world's upper-case style;
  - each famous name is exactly one new person of the right role (course 1's offenders keep their aliases, so a
    copycat SUPERMAN among today's villains is still there), born 1955-1980, holding a power;
  - every famous person fights, the famous heroes go on missions too, and the famous top the charts: the ten heroes
    and the ten villains in the most fights are all famous.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from lakehouse import lake  # noqa: E402
from lakehouse.universe import build, world  # noqa: E402

ASKED = {"hero": {"SUPERMAN", "WONDER WOMAN", "WOLVERINE"}, "villain": {"JOKER", "MAGNETO", "LOKI"}}


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    """A scale-S build without the mess, and a DuckDB connection with a view per built table."""
    out = tmp_path_factory.mktemp("universe") / "S"
    con = lake.lake_connect(read_only=True)
    build.build(out, scale_name="S", seed=2026, workers=4, chunk_rows=250_000, with_mess=False)
    for t in build.ORDER:
        con.execute(f"CREATE OR REPLACE TEMP VIEW u_{t} AS SELECT * FROM read_parquet('{out}/{t}/*.parquet')")
    con.execute("CREATE OR REPLACE TEMP TABLE famous AS SELECT * FROM (VALUES "
                + ", ".join(f"('{a}', '{r}', {i})" for r in ("hero", "villain") for i, a in enumerate(world.FAMOUS[r]))
                + ") t(alias, cast_role, fame_rank)")
    return con


def rows(con, sql):
    """All rows of a query."""
    return con.execute(sql).fetchall()


def test_the_cast_lists_hold_the_names_asked_for():
    """Heroes and villains, each list of distinct upper-case names, with Ian's six, and no name on both lists."""
    for role in ("hero", "villain"):
        cast = world.FAMOUS[role]
        assert len(cast) >= 20 and len(set(cast)) == len(cast), role
        assert all(a == a.upper() and a.strip() == a for a in cast), role
        assert ASKED[role] <= set(cast), role
    assert not set(world.FAMOUS["hero"]) & set(world.FAMOUS["villain"])


def test_each_famous_name_is_one_new_person_of_its_role(built):
    """Among the new people, each famous alias belongs to exactly one person, of the cast's role, born 1955-1980."""
    got = rows(built, """SELECT f.alias, f.cast_role, count(p.person_id), min(p.role), max(p.role),
                                min(p.birth_date), max(p.birth_date)
                         FROM famous f LEFT JOIN u_person p ON p.alias = f.alias AND NOT p.is_core
                         GROUP BY 1, 2""")
    for alias, cast_role, n, lo_role, hi_role, born_lo, born_hi in got:
        assert n == 1 and lo_role == hi_role == cast_role, (alias, n, lo_role, hi_role)
        assert 1955 <= born_lo.year and born_hi.year <= 1980, (alias, born_lo)


def test_todays_copycats_keep_their_aliases(built):
    """Course 1's people are untouched: today's villains still include their own SUPERMAN (a copycat now)."""
    assert rows(built, "SELECT count(*) FROM u_person WHERE is_core AND alias = 'SUPERMAN'")[0][0] >= 1


def test_every_famous_person_holds_a_power_and_fights(built):
    """Each famous person holds at least one power and is in at least one fight."""
    missing = rows(built, """SELECT f.alias FROM famous f JOIN u_person p ON p.alias = f.alias AND NOT p.is_core
                             WHERE p.person_id NOT IN (SELECT person_id FROM u_person_power)
                                OR p.person_id NOT IN (SELECT person_id FROM u_participant)""")
    assert missing == []


def test_famous_heroes_go_on_missions(built):
    """At least half the famous heroes are on a mission."""
    on = rows(built, """SELECT count(DISTINCT f.alias) FROM famous f
                        JOIN u_person p ON p.alias = f.alias AND NOT p.is_core AND f.cast_role = 'hero'
                        JOIN u_mission_member m USING (person_id)""")[0][0]
    assert on >= len(world.FAMOUS["hero"]) / 2


@pytest.mark.parametrize("side", ["hero", "villain"])
def test_the_famous_top_the_fight_charts(built, side):
    """The ten people of a side in the most fights are all famous."""
    top = rows(built, f"""SELECT p.alias FROM u_participant pa JOIN u_person p USING (person_id)
                          WHERE pa.side = '{side}' GROUP BY p.person_id, p.alias ORDER BY count(*) DESC, 1 LIMIT 10""")
    assert {a for (a,) in top} <= set(world.FAMOUS[side]), top
