"""The Vercel entry point (engine_server.py at the repo root) loads the engine app."""

import importlib.util
from pathlib import Path

from fastapi.testclient import TestClient


def test_entry_point_serves_the_engine() -> None:
    path = Path(__file__).resolve().parents[2] / "engine_server.py"
    spec = importlib.util.spec_from_file_location("engine_server", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    response = TestClient(module.app).get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
