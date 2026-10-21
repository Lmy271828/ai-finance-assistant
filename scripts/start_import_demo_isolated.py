"""从项目根目录运行：python scripts/start_import_demo_isolated.py

启动 FastAPI 的独立演示实例：所有 HTTP 导入只写入临时 SQLite 数据库。
退出服务时删除临时目录。不要与另一个占用 8000 端口的后端同时运行。
"""
from __future__ import annotations

import sys
from pathlib import Path
from tempfile import TemporaryDirectory

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend import db  # noqa: E402
from backend.main import app  # noqa: E402


def main() -> None:
    import uvicorn

    with TemporaryDirectory(prefix="finance_import_frontend_demo_") as directory:
        db.DB_PATH = Path(directory) / "isolated_demo.db"
        print("[SAFE DEMO] 临时数据库：", db.DB_PATH)
        print("[SAFE DEMO] 正式 db/bills.db 不会被此演示服务使用")
        print("[SAFE DEMO] 按 Ctrl+C 停止服务并清理临时数据库")
        uvicorn.run(app, host="127.0.0.1", port=8000, reload=False)


if __name__ == "__main__":
    main()
