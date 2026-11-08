"""om_sync.py can change a column's sensitivity, not only add one (2026-11-07).
    pytest -q lakehouse/tests/test_om_sensitivity_change.py     # no stack needed: CI runs this

Real names went from Sensitivity.Personal to Sensitivity.Restricted. OpenMetadata's PUT merges tags, and the
Sensitivity classification is mutually exclusive, so a plain PUT is refused ("Tag labels Sensitivity.Personal and
Sensitivity.Restricted are mutually exclusive"). om_sync first removes the old Sensitivity tag with a JSON Patch:
stale_sensitivity() works out those removals from the table as OpenMetadata holds it and the columns wanted.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "openmetadata"))
import om_sync  # noqa: E402


def tag(fqn, label="Manual"):
    """An OpenMetadata tag label."""
    return {"tagFQN": fqn, "source": "Classification", "labelType": label, "state": "Confirmed"}


CURRENT = {"columns": [
    {"name": "person_id", "tags": []},
    {"name": "last_name", "tags": [tag("Sensitivity.Personal"), tag("PIIType.PersonName", "Automated")]},
    {"name": "first_name", "tags": [tag("PIIType.PersonName", "Automated"), tag("Sensitivity.Personal")]},
    {"name": "alias", "tags": [tag("Sensitivity.Personal")]},
]}
WANTED = [{"name": "person_id", "tags": []},
          {"name": "last_name", "tags": [tag("Sensitivity.Restricted")]},
          {"name": "first_name", "tags": [tag("Sensitivity.Restricted")]},
          {"name": "alias", "tags": [tag("Sensitivity.Personal")]}]


def test_a_changed_sensitivity_is_removed_first():
    """The old Sensitivity tag goes from each column whose sensitivity changes; nothing else is touched."""
    ops = om_sync.stale_sensitivity(CURRENT, WANTED)
    assert ops == [{"op": "remove", "path": "/columns/2/tags/1"}, {"op": "remove", "path": "/columns/1/tags/0"}]


def test_removals_run_from_the_end_so_indexes_hold():
    """JSON Patch applies in order, so later array positions are removed first."""
    paths = [op["path"] for op in om_sync.stale_sensitivity(CURRENT, WANTED)]
    keys = [tuple(int(p) for p in path.split("/")[2::2]) for path in paths]
    assert keys == sorted(keys, reverse=True)


def test_a_derived_sensitivity_tag_is_left_to_openmetadata():
    """A Sensitivity tag a glossary term passes on (labelType Derived) isn't ours to remove."""
    current = {"columns": [{"name": "last_name", "tags": [tag("Sensitivity.Personal", "Derived")]}]}
    assert om_sync.stale_sensitivity(current, [{"name": "last_name", "tags": [tag("Sensitivity.Restricted")]}]) == []


def test_nothing_to_remove_when_unchanged_or_new():
    """Same sensitivity, no sensitivity wanted (a steward's tag stays), or a table OpenMetadata doesn't hold yet."""
    assert om_sync.stale_sensitivity(CURRENT, [{"name": "alias", "tags": [tag("Sensitivity.Personal")]}]) == []
    assert om_sync.stale_sensitivity(CURRENT, [{"name": "last_name", "tags": []}]) == []
    assert om_sync.stale_sensitivity(None, WANTED) == []
