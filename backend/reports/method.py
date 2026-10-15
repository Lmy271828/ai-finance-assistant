"""backend/reports/method.py —— 组件 5：支出方式分组

⚠️ 按 pay_method 【原始字符串】分组，不做归并。
   「储蓄卡(1234)」和「储蓄卡(5678)」是两组 —— 卡号后缀是有意义的信息，
   合并掉反而丢失信息。前端要做视觉归并，自己在客户端处理。
"""
from __future__ import annotations

from .. import db
from ..schemas import MethodGroup, MethodResp
from ._common import round2, where_clause


def get_by_method(req) -> MethodResp:
    clause, params = where_clause(req.period, req.value)
    sql = (
        "SELECT pay_method, ROUND(SUM(amount),2) AS amount, COUNT(*) AS cnt "
        "FROM v_tx_counted "
        f"WHERE direction = :direction AND {clause} "
        "GROUP BY pay_method ORDER BY amount DESC"
    )
    params["direction"] = "支出"   # 支出方式只对支出有意义

    conn = db.get_conn()
    try:
        rows = conn.execute(sql, params).fetchall()
    finally:
        conn.close()

    return MethodResp(groups=[
        MethodGroup(pay_method=r["pay_method"] or "", amount=round2(r["amount"]),
                    count=r["cnt"])
        for r in rows
    ])
