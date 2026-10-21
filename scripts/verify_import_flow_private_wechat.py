# -*- coding: utf-8 -*-
"""使用个人微信真实账单 + 虚构支付宝账单验证完整导入流程。

此脚本不会访问 127.0.0.1:8000；使用 TestClient 直接调用后端应用。
所有导入（包括真实微信记录）均写入独立临时 SQLite 数据库，结束自动删除。
不在终端输出任何真实交易金额、商户、单号或原始 JSON。
"""
from __future__ import annotations

import sys
from pathlib import Path
from tempfile import TemporaryDirectory

from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
from backend import db  # noqa: E402
from backend.main import app  # noqa: E402

PRIVATE_DIR = PROJECT_ROOT / "private_input"
DEMO_DIR = PROJECT_ROOT / "sample_data"


def ensure(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def upload(client: TestClient, endpoint: str, path: Path) -> dict:
    with path.open("rb") as stream:
        response = client.post(endpoint, files={"file": (path.name, stream)})
    # 特意不打印 response.text/json；预览响应可能含真实个人交易明细。
    ensure(response.status_code == 200,
           f"{endpoint} 请求失败（HTTP {response.status_code}），请检查服务器日志，勿公开原始交易内容。")
    return response.json()


def main() -> None:
    wechat_files = sorted(PRIVATE_DIR.glob("*.xlsx"))
    ensure(len(wechat_files) == 1,
           "private_input 中必须恰好有一份微信 XLSX 账单；请检查是否复制到了正确位置。")
    wx = wechat_files[0]
    ali_csv = DEMO_DIR / "支付宝模拟账单.csv"
    ali_zip = DEMO_DIR / "支付宝模拟账单.zip"
    bad = DEMO_DIR / "支付宝异常账单_模拟.csv"
    for f in (ali_csv, ali_zip, bad):
        ensure(f.is_file(), f"找不到演示样本：{f.name}")

    original_path = db.DB_PATH
    try:
        with TemporaryDirectory(prefix="finance_v3_private_isolated_") as tmp:
            db.DB_PATH = Path(tmp) / "isolated_test.db"
            # 本地 TestClient，绝不访问当前正在运行的 Uvicorn 或正式 bills.db。
            with TestClient(app) as client:
                init = client.get("/health").json()
                ensure(init["transactions"] == 0, "临时数据库必须为空")
                print("1/8  独立临时数据库已创建，正式 bills.db 不参与测试")

                p = upload(client, "/api/import/preview", wx)
                wx_total = p["total"]
                ensure(p["platform_id"] == "wechat" and wx_total > 0,
                       "微信账单预览未正确识别平台或有效记录")
                ensure(client.get("/health").json()["transactions"] == 0,
                       "预览期间不应写入数据库")
                print(f"2/8  微信真实账单预览通过：{wx_total} 笔有效交易，预览未写库")

                first = upload(client, "/api/import/commit", wx)
                ensure(first["inserted"] + first["skipped"] == wx_total,
                       "微信首次提交的新增数与跳过数之和不等于预览有效数")
                ensure(first["failed"] == 0, "微信真实账单存在校验失败的行，请单独排查")
                ensure(first["inserted"] > 0, "微信首次导入没有写入有效交易")
                print(f"3/8  微信真实账单首次导入通过：新增 {first['inserted']} 笔，去重 {first['skipped']} 笔")

                again = upload(client, "/api/import/commit", wx)
                ensure((again["inserted"], again["skipped"], again["failed"]) == (0, wx_total, 0),
                       "微信相同账单重复导入未被完全去重")
                print(f"4/8  微信重复导入通过：新增 0 笔，跳过 {wx_total} 笔")

                ap = upload(client, "/api/import/preview", ali_csv)
                ensure(ap["platform_id"] == "alipay" and ap["total"] == 2,
                       "支付宝演示账单预览数量异常")
                ac = upload(client, "/api/import/commit", ali_csv)
                ensure((ac["inserted"], ac["skipped"], ac["failed"]) == (2, 0, 0),
                       "支付宝 CSV 首次导入结果不正确")
                print("5/8  支付宝模拟 CSV 预览与首次导入通过：新增 2 笔")

                az = upload(client, "/api/import/commit", ali_zip)
                ensure((az["inserted"], az["skipped"], az["failed"]) == (0, 2, 0),
                       "支付宝 CSV 与 ZIP 之间的跨文件去重不正确")
                print("6/8  支付宝模拟 ZIP 去重通过：新增 0 笔，跳过 2 笔")

                bp = upload(client, "/api/import/preview", bad)
                ensure(bp["total"] == 1 and len(bp["warnings"]) >= 1,
                       "支付宝模拟异常金额未被识别")
                bc = upload(client, "/api/import/commit", bad)
                ensure((bc["inserted"], bc["skipped"], bc["failed"]) == (0, 1, 1),
                       "异常金额与重复交易未被分别正确统计")
                print("7/8  异常数据测试通过：错误 1 笔、重复 1 笔")

                health = client.get("/health").json()
                history = client.get("/api/import/history").json()
                expected = first["inserted"] + ac["inserted"]
                ensure(health["transactions"] == expected,
                       "临时数据库总交易数与实际新增笔数不符")
                ensure(len(history["batches"]) == 5,
                       "导入批次历史条数不符")
                conn = db.get_conn()
                try:
                    counts = {r["platform_id"]: r["n"] for r in conn.execute(
                        "SELECT platform_id, COUNT(*) AS n FROM transactions_raw GROUP BY platform_id"
                    )}
                finally:
                    conn.close()
                ensure(counts == {"wechat": first["inserted"], "alipay": 2},
                       "统一数据库按平台统计的笔数不正确")
                print(f"8/8  统一数据库与历史核对通过：共 {expected} 笔，5 个导入批次")
                print("\n8/8 检查通过！所有记录只写入临时数据库，正式 db/bills.db 未修改。")
    finally:
        db.DB_PATH = original_path


if __name__ == "__main__":
    main()
