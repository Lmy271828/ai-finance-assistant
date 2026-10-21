"""backend/reports/income_rank.py —— 组件 6：收入排行

只查 direction='收入'，按 amount 降序，最多 50 条。
counterparty 可能为空字符串（有些交易拿不到对方名）—— 不丢，只是不显示。
"""
from __future__ import annotations

from .. import db
from ..schemas import IncomeRankResp, RankItem
from ._common import round2, where_clause

TOP_N = 50


def get_income_rank(req) -> IncomeRankResp:
    clause, params = where_clause(req.period, req.value)
    sql = (
        "SELECT id, amount, date, tx_time, counterparty, tx_type, source "
        "FROM v_tx_counted "
        f"WHERE direction = :direction AND {clause} "
        "ORDER BY amount DESC LIMIT :limit"
    )
    params["direction"] = "收入"
    params["limit"] = TOP_N

    conn = db.get_conn()
    try:
        rows = conn.execute(sql, params).fetchall()
    finally:
        conn.close()

    return IncomeRankResp(items=[
        RankItem(
            tx_id=r["id"], amount=round2(r["amount"]), date=r["date"],
            tx_time=r["tx_time"], counterparty=r["counterparty"] or "",
            tx_type=r["tx_type"] or "", source=r["source"],
        )
        for r in rows
    ])
