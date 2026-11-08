"""Check the analyst Jupyter's walls from inside it: Cube answers with common names, and nothing else is in reach.
    docker compose --profile core exec -T analyst-jupyter python /home/jovyan/analyst/selfcheck.py

bootstrap.sh runs this after the stack is up. It prints one line per check and exits 1 if any fails:
  - no lake files (/lake) and no repo (/home/jovyan/course) are mounted;
  - no secret but CUBE_SQL_PASSWORD (and the container's own JUPYTER_TOKEN) is in its environment;
  - the catalog, the lab Jupyter, Dagster, OpenMetadata and the MCP server don't even resolve (the analyst network
    holds only Cube and Caddy), and the internet is out of reach;
  - Cube's SQL API answers, and ranks villains by common name.
"""
import os
import socket
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cube_sql import cube_url  # noqa: E402

ALLOWED_SECRETS = {"CUBE_SQL_PASSWORD", "JUPYTER_TOKEN"}
UNREACHABLE = ["catalog-pg", "jupyter", "dagster-webserver", "openmetadata-server", "mcp", "superset"]


def mount_points():
    """Every mount point in this container, from /proc/mounts."""
    return {line.split()[1] for line in Path("/proc/mounts").read_text().splitlines() if line.strip()}


def no_lake_mounted():
    """Neither the lake's files nor the repo (whose lakehouse/.env holds every secret) is here: nothing is mounted
    at /lake or /home/jovyan/course, and nothing is in them (the image makes an empty course folder, its WORKDIR)."""
    mounts = mount_points()
    present = [p for p in ("/lake", "/home/jovyan/course")
               if p in mounts or (Path(p).is_dir() and any(Path(p).iterdir()))]
    return not present, f"present: {present}" if present else "no /lake, no repo"


def no_other_secrets():
    """No environment variable that looks like a secret, other than the two this container needs."""
    words = ("PASSWORD", "TOKEN", "SECRET", "KEY", "CATALOG")
    extra = sorted(k for k in os.environ if any(w in k for w in words) and k not in ALLOWED_SECRETS)
    return not extra, f"extra secrets: {extra}" if extra else "only the Cube login and its own token"


def resolves(host):
    """True when a host name resolves from here."""
    try:
        socket.getaddrinfo(host, None)
        return True
    except socket.gaierror:
        return False


def other_services_out_of_reach():
    """The lake's other services don't resolve on the analyst network, and neither does the internet."""
    seen = [h for h in UNREACHABLE + ["pypi.org"] if resolves(h)]
    return not seen, f"reachable: {seen}" if seen else "only Cube and Caddy on this network"


def cube_answers_with_common_names():
    """Cube's SQL API ranks the busiest villains by common name."""
    from sqlalchemy import create_engine, text
    with create_engine(cube_url()).connect() as conn:
        top = conn.execute(text("SELECT common_name, MEASURE(participations) FROM fight_participants "
                                "WHERE person_role = 'villain' AND common_name IS NOT NULL "
                                "GROUP BY 1 ORDER BY 2 DESC LIMIT 3")).fetchall()
    ok = len(top) == 3 and all(isinstance(n, str) and n for n, _ in top)
    return ok, "top villains: " + ", ".join(n for n, _ in top) if ok else f"unexpected answer: {top}"


def main():
    """Run every check, print one line each, and exit 1 if any failed."""
    failed = 0
    for check in (no_lake_mounted, no_other_secrets, other_services_out_of_reach, cube_answers_with_common_names):
        try:
            ok, detail = check()
        except Exception as e:   # a check that crashes has failed
            ok, detail = False, f"{type(e).__name__}: {e}"
        print(f"{'ok ' if ok else 'BAD'} {check.__name__}: {detail}")
        failed += not ok
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
