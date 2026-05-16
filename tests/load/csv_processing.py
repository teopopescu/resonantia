"""Locust tasks for CSV upload plus from-file curve fitting."""

from __future__ import annotations

from io import BytesIO

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


DOSE_RESPONSE_CSV = (
    b"concentration,response\n"
    b"0.001,99\n"
    b"0.01,94\n"
    b"0.1,72\n"
    b"1,44\n"
    b"10,17\n"
    b"100,5\n"
)


class CSVProcessingUser(HttpUser):
    """Exercise upload + direct processing endpoint latency."""

    wait_time = between(1, 5)
    abstract = False

    @task
    def upload_and_fit(self):
        with self.client.post(
            "/api/v1/files/upload",
            files={"files": ("dose.csv", BytesIO(DOSE_RESPONSE_CSV), "text/csv")},
            headers={"X-Org-Id": "org_load"},
            catch_response=True,
            name="csv.upload",
        ) as upload:
            if upload.status_code != 201:
                upload.failure(f"upload failed: {upload.status_code}")
                return
            file_id = upload.json()[0]["id"]

        with self.client.post(
            "/api/v1/processing/dose-response/from-file",
            json={"file_id": file_id},
            headers={"X-Org-Id": "org_load"},
            catch_response=True,
            name="csv.dose_response.from_file",
        ) as response:
            if response.status_code != 200:
                response.failure(f"fit failed: {response.status_code}: {response.text[:200]}")
                return
            if not response.json().get("processing_result_id"):
                response.failure("missing processing_result_id")
