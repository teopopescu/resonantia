"""Locust entrypoint for Resonantia staging load tests.

Run examples:

    locust -f tests/load/locustfile.py --host https://staging.example.com
    locust -f tests/load/locustfile.py --headless -u 10 -r 2 --run-time 5m
"""

from __future__ import annotations

try:
    from locust import HttpUser, between, task
except ImportError:  # pragma: no cover
    class HttpUser:  # type: ignore[no-redef]
        pass

    def between(*args, **kwargs):  # type: ignore[no-redef]
        return None

    def task(weight=1):  # type: ignore[no-redef]
        def _decorator(fn):
            return fn
        return _decorator

from csv_processing import CSVProcessingUser
from voice_turn import VoiceTurnUser


class ChatAndApprovalUser(HttpUser):
    """Chat message and approval flow load tasks."""

    wait_time = between(1, 4)
    abstract = False

    @task(4)
    def chat_message(self):
        with self.client.post(
            "/api/v1/chat/message",
            json={"message": "Where is staurosporine?"},
            headers={"X-Org-Id": "org_load"},
            catch_response=True,
            name="chat.message",
        ) as response:
            if response.status_code != 200:
                response.failure(f"chat failed: {response.status_code}: {response.text[:200]}")

    @task(1)
    def approval_poll_missing_token(self):
        # Lightweight approval endpoint exercise. Full approve/reject requires
        # a live pending token created by gated tools in staging data.
        response = self.client.post(
            "/api/v1/chat/reject/load-test-missing-token",
            headers={"X-Org-Id": "org_load"},
            name="approval.reject.missing",
        )
        if response.status_code not in (403, 410):
            response.failure(f"unexpected approval status: {response.status_code}")


__all__ = ["VoiceTurnUser", "CSVProcessingUser", "ChatAndApprovalUser"]
