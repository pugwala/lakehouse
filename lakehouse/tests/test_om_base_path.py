"""OpenMetadata at /openmetadata/ (fix, 2026-11-07): BASE_PATH must end in a slash, or the UI loads blank.

    pytest lakehouse/tests/test_om_base_path.py     # inside the jupyter container (or the CI sandbox)

OpenMetadata 2.0.5 builds its page by gluing BASE_PATH straight onto file names: its index.html says
`${basePath}assets/index-....js`. With BASE_PATH=/openmetadata the browser asks for /openmetadataassets/...,
gets 404 for every script, and shows an empty page, while the page itself still answers 200 (so the site probe
stayed green). The tests check that Compose gives the server and its migration step a BASE_PATH that, glued onto
the template's file names, lands under /openmetadata/.
"""
from pathlib import Path

import yaml

COMPOSE = Path(__file__).resolve().parents[1] / "compose.yaml"
TEMPLATE_FILES = ["assets/index-BMZSQlJM.js", "favicon.png", "favicons/apple-icon-57x57.png"]


def om_base_paths():
    """Return {service: BASE_PATH} for every Compose service that runs the OpenMetadata server image."""
    services = yaml.safe_load(COMPOSE.read_text())["services"]
    return {name: svc.get("environment", {}).get("BASE_PATH")
            for name, svc in services.items() if "openmetadata/server" in str(svc.get("image", ""))}


def test_every_om_service_sets_base_path():
    """The server and om-migrate both get BASE_PATH (they share the x-om-env block)."""
    paths = om_base_paths()
    assert len(paths) >= 2, paths
    assert all(paths.values()), paths


def test_base_path_ends_in_a_slash():
    """BASE_PATH is /openmetadata/, with the slash the 2.0.5 template needs."""
    for name, base in om_base_paths().items():
        assert base == "/openmetadata/", f"{name}: BASE_PATH={base!r}"


def test_template_paths_land_under_openmetadata():
    """Glued the way index.html glues them, the UI's files resolve under /openmetadata/."""
    for base in om_base_paths().values():
        for f in TEMPLATE_FILES:
            assert f"{base}{f}".startswith("/openmetadata/"), f"{base}{f}"
