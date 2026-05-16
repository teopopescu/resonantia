"""Staging integration test for audit-log completeness.

This test is skipped unless these environment variables are present:

- RESONANTIA_BASE_URL
- RESONANTIA_AUTH_TOKEN
- RESONANTIA_ORG_ID
- RESONANTIA_DATABASE_URL
"""

from __future__ import annotations

from datetime import datetime, timezone
from io import BytesIO
import os
import uuid

import pytest


pytest.importorskip("httpx")
pytest.importorskip("psycopg2")


BASE_URL = os.getenv("RESONANTIA_BASE_URL", "").rstrip("/")
AUTH_TOKEN = os.getenv("RESONANTIA_AUTH_TOKEN", "")
ORG_ID = os.getenv("RESONANTIA_ORG_ID", "")
DATABASE_URL = os.getenv("RESONANTIA_DATABASE_URL", "")


pytestmark = pytest.mark.skipif(
    not all([BASE_URL, AUTH_TOKEN, ORG_ID, DATABASE_URL]),
    reason="staging integration environment variables are not configured",
)


def test_full_wedge_produces_complete_audit_trail():
    import httpx
    import psycopg2

    started_at = datetime.now(timezone.utc)
    headers = {"Authorization": f"Bearer {AUTH_TOKEN}", "X-Org-Id": ORG_ID}

    with httpx.Client(base_url=BASE_URL, headers=headers, timeout=30.0) as client:
        upload = client.post(
            "/api/v1/files/upload",
            files={
                "files": (
                    "audit-dose.csv",
                    BytesIO(
                        b"concentration,response\n"
                        b"0.001,99\n0.01,94\n0.1,72\n1,44\n10,17\n100,5\n"
                    ),
                    "text/csv",
                )
            },
        )
        upload.raise_for_status()
        file_id = upload.json()[0]["id"]

        fit = client.post("/api/v1/processing/dose-response/from-file", json={"file_id": file_id})
        fit.raise_for_status()
        processing_result_id = fit.json()["processing_result_id"]

        draft = client.post(
            "/api/v1/eln/draft-from-result",
            json={
                "processing_result_id": processing_result_id,
                "file_id": file_id,
                "title": f"Audit wedge {uuid.uuid4()}",
            },
        )
        draft.raise_for_status()
        assert draft.json()["status"] == "draft"

    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                select action
                from audit_log
                where org_id = %s
                  and created_at >= %s
                  and action in (
                    'file.upload',
                    'processing.from_file',
                    'eln.draft_from_result'
                  )
                """,
                (ORG_ID, started_at),
            )
            actions = {row[0] for row in cur.fetchall()}

    assert {"file.upload", "processing.from_file", "eln.draft_from_result"}.issubset(actions)
