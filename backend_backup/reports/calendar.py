"""backend/reports/calendar.py —— 组件 2：每日日历

⚠️ 约定：无消费的日期【不返回】（不是 amount=0）。
   前端自己补零渲染。这样前端能区分「这天确实 0 支出」
   和「这天数据没导全」。
"""
from __future__ import annotations

from .. import db
from ..schemas import CalendarResp, DayPoint
from ._common import direction_of, period_bounds, round2, where_clause


def get_calendar(req) -> CalendarResp:
    clause, params = where_clause(req.period, req.value)
    sql = (
        "SELECT date, ROUND(SUM(amount),2) AS amount, COUNT(*) AS cnt "
        f"FROM v_tx_counted WHERE direction = :direction AND {clause} "
        "GROUP BY date ORDER BY date ASC"
    )
    params["direction"] = direction_of(req.type)

    conn = db.get_conn()
    try:
        rows = conn.execute(sql, params).fetchall()
    finally:
        conn.close()

    return CalendarResp(days=[
        DayPoint(date=r["date"], amount=round2(r["amount"]), count=r["cnt"])
        for r in rows
    ])
