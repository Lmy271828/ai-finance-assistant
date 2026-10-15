"""backend/reports/summary.py —— 组件 1：周期总览"""
from __future__ import annotations

from .. import db
from ..schemas import SummaryResp
from ._common import direction_of, period_bounds, round2, where_clause


def _aggregate(conn, period: str, value: str, direction: str) -> tuple[float, int]:
    clause, params = where_clause(period, value)
    sql = (
        "SELECT COALESCE(SUM(amount),0) AS total, COUNT(*) AS cnt "
        f"FROM v_tx_counted WHERE direction = :direction AND {clause}"
    )
    params["direction"] = direction
    row = conn.execute(sql, params).fetchone()
    return round2(row["total"]), row["cnt"]


def get_summary(req) -> SummaryResp:
    """本期合计 / 上期合计 / 环比。

    上期基准：week→上一周，month→上一月，year→上一年。
    上期为 0 时 rate 返回 None（不是 0）。
    """
    direction = direction_of(req.type)

    # 上期值
    if req.period == "month":
        y, m = int(req.value[:4]), int(req.value[5:7])
        pm = f"{y - 1}-12" if m == 1 else f"{y}-{m - 1:02d}"
        prev_key = ("month", pm)
    elif req.period == "year":
        prev_key = ("year", str(int(req.value) - 1))
    else:  # week
        from datetime import date, timedelta
        year_s, week_s = req.value.split("-W")
        d = date.fromisocalendar(int(year_s), int(week_s), 1) - timedelta(days=7)
        iso = d.isocalendar()
        prev_key = ("week", f"{iso[0]}-W{iso[1]:02d}")

    conn = db.get_conn()
    try:
        total, count = _aggregate(conn, req.period, req.value, direction)
        prev, _ = _aggregate(conn, prev_key[0], prev_key[1], direction)
    finally:
        conn.close()

    delta = round2(total - prev)
    rate = None if prev == 0 else round((total - prev) / prev * 100, 1)

    return SummaryResp(
        period=req.value, total=total, prev=prev,
        delta=delta, rate=rate, count=count,
    )
