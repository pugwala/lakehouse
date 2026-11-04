"""dashboards.py waits and tries again when Superset says it is too busy (429), and only then.

Superset allows 50 API calls a second. Right after the acceptance suite, `dashboards.py --check` (which bootstrap.sh
runs) went over that and failed with "429 Too Many Requests" instead of waiting. These tests use a fake Superset that
answers 429 a set number of times; the sleeps are recorded, not slept.
"""
import sys
from pathlib import Path

import pytest

LAKEHOUSE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAKEHOUSE / "superset"))
import dashboards  # noqa: E402


class Reply:
    """A stand-in for a requests.Response: a status, optional headers, and a JSON body."""

    def __init__(self, status, headers=None):
        """A reply with this HTTP status and these headers."""
        self.status_code, self.headers = status, headers or {}
        self.ok = status < 400
        self.text = "Too Many Requests" if status == 429 else "boom"

    def json(self):
        """The body Superset sends on success."""
        return {"result": "fine"}


class FakeSuperset:
    """Answers each request with the next reply in its list, and counts the requests."""

    def __init__(self, *replies):
        """The replies to give, in order."""
        self.replies, self.calls = list(replies), 0

    def request(self, method, url, **kwargs):
        """The next reply."""
        self.calls += 1
        return self.replies.pop(0)


@pytest.fixture
def slept(monkeypatch):
    """The waits dashboards.py asked for, in seconds, without waiting."""
    waits = []
    monkeypatch.setattr(dashboards.time, "sleep", waits.append)
    return waits


def test_a_busy_superset_is_asked_again(slept):
    """Two 429s, then success: the call succeeds, after two waits that grow."""
    api = FakeSuperset(Reply(429), Reply(429), Reply(200))
    assert dashboards.call(api, "GET", "dashboard/") == {"result": "fine"}
    assert api.calls == 3
    assert len(slept) == 2 and 0 < slept[0] < slept[1]


def test_superset_says_how_long_to_wait(slept):
    """When the 429 carries Retry-After, that is the wait."""
    api = FakeSuperset(Reply(429, {"Retry-After": "3"}), Reply(200))
    dashboards.call(api, "GET", "chart/")
    assert slept == [3.0]


def test_it_gives_up_after_a_few_tries(slept):
    """A Superset that stays busy fails the run, with the 429 in the message, after RETRIES waits."""
    api = FakeSuperset(*[Reply(429)] * (dashboards.RETRIES + 1))
    with pytest.raises(RuntimeError, match="429"):
        dashboards.call(api, "GET", "dataset/")
    assert api.calls == dashboards.RETRIES + 1 and len(slept) == dashboards.RETRIES


def test_a_real_error_is_not_retried(slept):
    """Any other refusal fails at once: only "too busy" is worth waiting for."""
    api = FakeSuperset(Reply(500), Reply(200))
    with pytest.raises(RuntimeError, match="500"):
        dashboards.call(api, "PUT", "chart/1")
    assert api.calls == 1 and slept == []
