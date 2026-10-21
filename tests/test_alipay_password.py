"""支付宝密码 ZIP 的 HTTP 集成测试——纯模拟数据，不需真实账单或外部 zip 命令。"""
from __future__ import annotations

import base64
import io
import zipfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend import db
from backend.main import app

# 模拟支付宝 CSV，经传统 ZIP 加密；测试密码：demo123。
# 在源码中固定压缩包，避免 Windows/CI 环境额外依赖 zip 命令。
ENCRYPTED_ZIP_B64 = (
    "UEsDBBQACQAIAAsiUF0Jl0PG0gAAANEAAAAZABwA5pSv5LuY5a6d5qih5ouf6LSm5Y2VLmNzdlVUCQADFaXRahWl0Wp1eAsAAQQAAAAABAAAAAA2wnyNFyf5uPQhCII3+czSVLXq/hJcq8x2uIbAuiEz9UJ5C/JRzmq1Pv74PxN0fEinURT7MnfkEPSiW+f5H0ic0DhBNCYUZhhqZ9wFKg4ZL4LvCPFYMk3naATO77IlutYiGqBOC17zQ0znbIUGv5LjItxo832LFLH5sv8wUjnfMpJREVrRkaGUI1QGHeGdTR9mfiiJg1+qWc3MdyViMT1IvS+J0XJRJEMG9zKIhgek8o1Iwoq/gtCWvuElm3f24f2fxlF+l/4oOioNqxhmX1RZ4QxQSwcICZdDxtIAAADRAAAAUEsBAh4DFAAJAAgACyJQXQmXQ8bSAAAA0QAAABkAGAAAAAAAAQAAAKSBAAAAAOaUr+S7mOWuneaooeaLn+i0puWNlS5jc3ZVVAUAAxWl0Wp1eAsAAQQAAAAABAAAAABQSwUGAAAAAAEAAQBfAAAANQEAAAAA"
)


@pytest.fixture
def db_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setattr(db, "DB_DIR", tmp_path)
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
    db.init_db(db.DB_PATH)
    return tmp_path


def transaction_count() -> int:
    conn = db.get_conn()
    try:
        return conn.execute("SELECT COUNT(*) FROM transactions_raw").fetchone()[0]
    finally:
        conn.close()


def upload_zip(client: TestClient, url: str, *, password: str | None,
               data: bytes | None = None, filename: str = "支付宝账单.zip"):
    fields = {"alipay_password": password} if password is not None else {}
    return client.post(
        url,
        data=fields,
        files={"file": (filename, data if data is not None else base64.b64decode(ENCRYPTED_ZIP_B64), "application/zip")},
    )


def test_encrypted_zip_preview_commit_and_duplicate(db_root: Path):
    with TestClient(app) as client:
        r = upload_zip(client, "/api/import/preview", password="demo123")
        assert r.status_code == 200, r.text
        assert r.json()["total"] == 1
        assert transaction_count() == 0  # 预览必须只读

        r = upload_zip(client, "/api/import/commit", password="demo123")
        assert r.status_code == 200, r.text
        assert (r.json()["inserted"], r.json()["skipped"]) == (1, 0)
        assert transaction_count() == 1

        again = upload_zip(client, "/api/import/commit", password="demo123")
        assert again.status_code == 200, again.text
        assert (again.json()["inserted"], again.json()["skipped"]) == (0, 1)
        assert transaction_count() == 1


def test_encrypted_zip_missing_password_is_400(db_root: Path):
    with TestClient(app) as client:
        for endpoint in ("/api/import/preview", "/api/import/commit"):
            r = upload_zip(client, endpoint, password=None)
            assert r.status_code == 400, r.text
            assert "密码" in r.json()["detail"]
        assert transaction_count() == 0


def test_encrypted_zip_wrong_password_is_400(db_root: Path):
    with TestClient(app) as client:
        for endpoint in ("/api/import/preview", "/api/import/commit"):
            r = upload_zip(client, endpoint, password="bad-secret-4444")
            assert r.status_code == 400, r.text
            assert "密码" in r.json()["detail"]
            assert "bad-secret-4444" not in r.text
        assert transaction_count() == 0


def test_corrupt_zip_is_400(db_root: Path):
    with TestClient(app) as client:
        for endpoint in ("/api/import/preview", "/api/import/commit"):
            r = upload_zip(client, endpoint, password="demo123", data=b"not a zip")
            assert r.status_code == 400, r.text
            assert "ZIP" in r.json()["detail"]
        assert transaction_count() == 0


def test_zip_without_csv_is_400(db_root: Path):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as zf:
        zf.writestr("README.txt", "empty")
    with TestClient(app) as client:
        r = upload_zip(client, "/api/import/preview", password=None, data=stream.getvalue())
        assert r.status_code == 400, r.text
        assert "CSV" in r.json()["detail"]


def test_windows_style_filename_is_sanitized(db_root: Path):
    with TestClient(app) as client:
        r = upload_zip(client, "/api/import/commit", password="demo123",
                       filename=r"C:\somewhere\支付宝账单.zip")
        assert r.status_code == 200, r.text
    conn = db.get_conn()
    try:
        stored_name = conn.execute("SELECT filename FROM import_batches").fetchone()[0]
    finally:
        conn.close()
    assert stored_name == "支付宝账单.zip"


def test_reject_empty_and_wrong_extension(db_root: Path):
    with TestClient(app) as client:
        r = upload_zip(client, "/api/import/preview", password=None, data=b"", filename="支付宝账单.zip")
        assert r.status_code == 400
        r = upload_zip(client, "/api/import/preview", password=None, data=b"abc", filename="账单.txt")
        assert r.status_code == 400


def test_file_size_limit_is_413(db_root: Path, monkeypatch: pytest.MonkeyPatch):
    import backend.main as main_mod
    monkeypatch.setattr(main_mod, "MAX_UPLOAD_BYTES", 100)
    with TestClient(app) as client:
        r = upload_zip(client, "/api/import/commit", password="demo123")
        assert r.status_code == 413, r.text
    assert transaction_count() == 0
