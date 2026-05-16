"""Smoke tests for Locust load-test definitions."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
LOAD_DIR = ROOT / "tests" / "load"


def _load_module(name: str, path: Path):
    sys.path.insert(0, str(LOAD_DIR))
    try:
        spec = importlib.util.spec_from_file_location(name, path)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        sys.path.remove(str(LOAD_DIR))


def test_load_test_modules_import_without_locust_installed():
    for filename in ("voice_turn.py", "csv_processing.py", "locustfile.py"):
        module = _load_module(filename.removesuffix(".py"), LOAD_DIR / filename)
        assert module is not None


def test_load_tests_cover_planned_paths():
    combined = "\n".join(path.read_text() for path in LOAD_DIR.glob("*.py"))

    for expected in (
        "/api/v1/voice/turn",
        "/api/v1/files/upload",
        "/api/v1/processing/dose-response/from-file",
        "/api/v1/chat/message",
        "/api/v1/chat/reject",
        "10 concurrent",
    ):
        assert expected in combined
