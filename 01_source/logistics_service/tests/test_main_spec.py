import importlib
import pathlib

import pytest


def test_maybe_mtls_middleware_path_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    import app.main as mm

    monkeypatch.setenv("MTLS_ENFORCE", "1")
    orig = pathlib.Path.is_file

    def is_file(self):
        s = str(self)
        if "mtls" in s and s.endswith("middleware.py"):
            return False
        return orig(self)

    monkeypatch.setattr(pathlib.Path, "is_file", is_file)
    importlib.reload(mm)
    monkeypatch.setenv("MTLS_ENFORCE", "0")
    importlib.reload(mm)


def test_maybe_mtls_spec_none(monkeypatch: pytest.MonkeyPatch) -> None:
    import app.main as mm

    monkeypatch.setenv("MTLS_ENFORCE", "1")
    monkeypatch.setattr(mm.importlib.util, "spec_from_file_location", lambda *a, **k: None)
    importlib.reload(mm)
    monkeypatch.setenv("MTLS_ENFORCE", "0")
    importlib.reload(mm)
