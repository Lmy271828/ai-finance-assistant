"""backend/reports/trend.py —— 组件 3：柱状图 + 均值线

注意 avg 的口径
================
avg = bars 里各期 amount 的算术平均，【不是】 total / n。
某个 bar 为 0 也参与平均 —— 它是真实存在的一个区间。
"""
from __future__ import annotations

from datetime import date, timedelta

from .. import db
from ..schemas import TrendBar, TrendResp
from ._common import direction_of, period_bounds, round2


def _shift(period: str, value: str, delta: int) -> str:
    """把周期标识往前/往后推 delta 期。"""
    if period == "month":
        y, m = int(value[:4]), int(value[5:7])
        total = y * 12 + (m - 1) + delta
        return f"{total // 12:04d}-{total % 12 + 1:02d}"
    if period == "year":
        return str(int(value) + delta)
    y, w = value.split("-W")
    iso = date.fromisocalendar(int(y), int(w), 1) + timedelta(weeks=delta)
    r = iso.isocalendar()
    return f"{r[0]}-W{r[1]:02d}"


def _bounds(period: str, value: str) -> tuple[str, str]:
    if period == "month":
        return f"{value}-01", f"{value}-31"
    return period_bounds(period, value)


def get_trend(req, n: int = 5) -> TrendResp:
    n = max(1, min(n, 24))
    direction = direction_of(req.type)

    bars: list[TrendBar] = []
    for i in range(n - 1, -1, -1):          # 从最早到当期
        label = _shift(req.period, req.value, -i)
        start, end = _bounds(req.period, label)
        sql = (
            "SELECT COALESCE(SUM(amount),0) AS total, COUNT(*) AS cnt "
            "FROM v_tx_counted "
            "WHERE direction = :d AND date BETWEEN :s AND :e"
        )
        conn = db.get_conn()
        try:
            row = conn.execute(
                sql, {"d": direction, "s": start, "e": end}
            ).fetchone()
        finally:
            conn.close()
        bars.append(TrendBar(label=label, amount=round2(row["total"]),
                             count=row["cnt"]))

    avg = round2(sum(b.amount for b in bars) / len(bars)) if bars else 0.0
    return TrendResp(bars=bars, avg=avg, n=len(bars))
