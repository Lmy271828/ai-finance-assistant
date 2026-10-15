<script setup lang="ts">
/**
 * BillView —— 报告主页骨架
 *
 * ┌─────────────────────────────────────────────────┐
 * │ 【你做】TimeSelector / TypeToggle —— 顶部切换器   │
 * ├─────────────────────────────────────────────────┤
 * │ 【队友】以下区块内部渲染                          │
 * │   支出：summary / calendar / trend / category    │
 * │         method                                    │
 * │   收入：summary / calendar / trend / rank        │
 * └─────────────────────────────────────────────────┘
 *
 * 每个区块的 data-component 就是它对应的后端接口：
 *   summary    → GET /api/report/summary
 *   calendar   → GET /api/report/calendar
 *   trend      → GET /api/report/trend
 *   category   → GET /api/report/by-category
 *   method     → GET /api/report/by-method
 *   rank       → GET /api/report/income-rank
 *
 * ⚠️ 本文件用假数据演示。队友接真实接口时：
 *    1. 删掉 MOCK_* 常量
 *    2. 每个区块自己 fetch 对应接口
 *    3. 请求路径写 '/api/report/xxx'（相对路径，靠 vite proxy 转发）
 *    4. 参数用 router 传进来的 type / period / value
 *
 * 数值约定（照抄 docs/设计/06_API契约.md 第 2 节）：
 *    - amount 是「元」，两位小数
 *    - rate / pct 是百分数，17.2 表示 17.2%，不是 0.172
 *    - rate 为 null 时显示「—」
 */

const props = defineProps<{
  type: string
  period: string
  value: string
  tab: string
}>()

// ── 假数据，接真实接口后删掉 ──────────────────────────
const MOCK_SUMMARY = {
  total: 3573.67,
  prev: 3050.2,
  delta: 523.47,
  rate: 17.2,
  count: 180,
}
const MOCK_CALENDAR = [
  { date: '2026-09-01', amount: 720.5, count: 8 },
  { date: '2026-09-02', amount: 100.1, count: 2 },
  { date: '2026-09-05', amount: 300.74, count: 4 },
  // ⚠️ 9/3、9/4 无消费 → 后端不会返回它们，前端自己补零
]
const MOCK_TREND = {
  bars: [
    { label: '2026-05', amount: 2382.17 },
    { label: '2026-06', amount: 4425.08 },
    { label: '2026-07', amount: 3052.2 },
    { label: '2026-08', amount: 3031.57 },
    { label: '2026-09', amount: 3573.67 },
  ],
  avg: 3292.94,
}
const MOCK_CATEGORY = {
  total: 3573.67,
  majors: [
    {
      major: '餐饮',
      amount: 892.5,
      pct: 25.0,
      minors: [
        { minor: '美团', amount: 312.0, pct: 8.7 },
        { minor: '麦当劳', amount: 185.5, pct: 5.2 },
      ],
    },
    // ⚠️ minors 为空数组时，前端必须容错，不能 .map 崩掉
    { major: '购物', amount: 210.0, pct: 5.9, minors: [] },
  ],
}
const MOCK_METHOD = [
  { pay_method: '花呗', amount: 598.45, count: 6 },
  { pay_method: '[银行]储蓄卡', amount: 298.53, count: 1 },
  { pay_method: '亲情卡', amount: 299.99, count: 11 },
]
const MOCK_RANK = [
  { tx_id: 7, amount: 360.0, tx_time: '2026-09-06 14:49', counterparty: '[亲友A]', tx_type: '转账红包' },
  { tx_id: 19, amount: 200.0, tx_time: '2026-09-12 23:24', counterparty: '[亲友B]', tx_type: '转账红包' },
]

const isIncome = () => props.type === 'income'
const fmt = (n: number) => n.toFixed(2)
</script>

<template>
  <div class="bill-view">
    <!-- ===== 顶部切换器（待实现组件）===== -->
    <div class="toolbar card">
      <span data-component="type-toggle">支出 / 收入 切换</span>
      <span data-component="time-selector">周 / 月 / 年 选择</span>
      <span class="current">{{ value }}</span>
    </div>

    <!-- ==================== 支出 ==================== -->
    <template v-if="!isIncome()">
      <!-- GET /api/report/summary -->
      <section class="card" data-component="summary" data-api="/api/report/summary">
        <h3>小结</h3>
        <div class="summary">
          <div class="amount">¥{{ fmt(MOCK_SUMMARY.total) }}</div>
          <div class="meta">
            <span :class="{ up: MOCK_SUMMARY.delta > 0 }">
              {{ MOCK_SUMMARY.delta > 0 ? '↑' : '↓' }}
              ¥{{ fmt(Math.abs(MOCK_SUMMARY.delta)) }}
            </span>
            <!-- ⚠️ rate 为 null 时显示「—」，不要显示 0% -->
            <span v-if="MOCK_SUMMARY.rate !== null">
              {{ MOCK_SUMMARY.rate > 0 ? '+' : '' }}{{ MOCK_SUMMARY.rate }}%
            </span>
            <span v-else>—</span>
            <span>共 {{ MOCK_SUMMARY.count }} 笔</span>
          </div>
        </div>
      </section>

      <!-- GET /api/report/calendar -->
      <section class="card" data-component="calendar" data-api="/api/report/calendar">
        <h3>每日日历</h3>
        <div class="grid">
          <div v-for="d in MOCK_CALENDAR" :key="d.date" class="day">
            <b>{{ d.date.slice(8) }}</b>
            <small>¥{{ fmt(d.amount) }}</small>
          </div>
        </div>
      </section>

      <!-- GET /api/report/trend -->
      <section class="card" data-component="trend" data-api="/api/report/trend">
        <h3>趋势（近5期）</h3>
        <div class="bars">
          <div v-for="b in MOCK_TREND.bars" :key="b.label" class="bar-item">
            <div class="bar" :style="{ height: (b.amount / 4425.08) * 100 + 'px' }" />
            <small>{{ b.label.slice(5) }}</small>
          </div>
        </div>
        <div class="avg-line">月均 ¥{{ fmt(MOCK_TREND.avg) }}</div>
      </section>

      <!-- GET /api/report/by-category -->
      <section class="card" data-component="category" data-api="/api/report/by-category">
        <h3>分类</h3>
        <ul class="cat-list">
          <li v-for="m in MOCK_CATEGORY.majors" :key="m.major">
            <div class="cat-row">
              <span>{{ m.major }}</span>
              <span>¥{{ fmt(m.amount) }}</span>
              <span class="pct">{{ m.pct }}%</span>
            </div>
            <!-- ⚠️ minors 可能是空数组 -->
            <ul v-if="m.minors && m.minors.length" class="sub-list">
              <li v-for="s in m.minors" :key="s.minor">
                {{ s.minor }} · ¥{{ fmt(s.amount) }} · {{ s.pct }}%
              </li>
            </ul>
          </li>
        </ul>
      </section>

      <!-- GET /api/report/by-method -->
      <section class="card" data-component="method" data-api="/api/report/by-method">
        <h3>支出方式</h3>
        <ul class="cat-list">
          <li v-for="m in MOCK_METHOD" :key="m.pay_method" class="cat-row">
            <span>{{ m.pay_method }}</span>
            <span>¥{{ fmt(m.amount) }}</span>
            <span class="pct">{{ m.count }}笔</span>
          </li>
        </ul>
      </section>
    </template>

    <!-- ==================== 收入 ==================== -->
    <template v-else>
      <section class="card" data-component="summary" data-api="/api/report/summary">
        <h3>小结</h3>
        <div class="summary">
          <div class="amount income">¥{{ fmt(MOCK_SUMMARY.total) }}</div>
        </div>
      </section>

      <section class="card" data-component="calendar" data-api="/api/report/calendar">
        <h3>每日日历</h3>
      </section>

      <section class="card" data-component="trend" data-api="/api/report/trend">
        <h3>趋势（近5期）</h3>
      </section>

      <!-- GET /api/report/income-rank -->
      <section class="card" data-component="rank" data-api="/api/report/income-rank">
        <h3>收入排行</h3>
        <ul class="rank-list">
          <li v-for="(r, i) in MOCK_RANK" :key="r.tx_id">
            <span class="no">{{ i + 1 }}</span>
            <span class="amt">¥{{ fmt(r.amount) }}</span>
            <span class="time">{{ r.tx_time.slice(5) }}</span>
            <!-- ⚠️ counterparty 可能是空字符串，不要显示空白占位 -->
            <span class="cp" v-if="r.counterparty">{{ r.counterparty }}</span>
          </li>
        </ul>
      </section>
    </template>
  </div>
</template>

<style scoped>
.toolbar { display: flex; gap: var(--space-3); align-items: center; }
.current { margin-left: auto; color: var(--color-muted); }
h3 { font-size: var(--font-md); margin-bottom: var(--space-3); }
.summary .amount { font-size: var(--font-xl); font-weight: 700; color: var(--color-expense); }
.summary .amount.income { color: var(--color-income); }
.meta { display: flex; gap: var(--space-3); color: var(--color-muted); margin-top: var(--space-1); }
.meta .up { color: var(--color-expense); }
.grid { display: grid; grid-template-columns: repeat(7, 1fr); gap: var(--space-1); }
.day { background: var(--color-bg); border-radius: var(--radius-sm); padding: var(--space-1); text-align: center; }
.day small { color: var(--color-muted); }
.bars { display: flex; gap: var(--space-2); align-items: flex-end; height: 120px; }
.bar-item { display: flex; flex-direction: column; align-items: center; }
.bar { width: 32px; background: var(--chart-1); border-radius: var(--radius-sm) var(--radius-sm) 0 0; }
.avg-line { color: var(--color-muted); margin-top: var(--space-2); }
.cat-list, .sub-list, .rank-list { list-style: none; }
.cat-row { display: flex; gap: var(--space-2); padding: var(--space-2) 0; border-bottom: 1px solid var(--color-border); }
.cat-row .pct { margin-left: auto; color: var(--color-muted); }
.sub-list { padding-left: var(--space-3); color: var(--color-muted); }
.sub-list li { padding: var(--space-1) 0; }
.rank-list li { display: flex; gap: var(--space-3); padding: var(--space-2) 0; border-bottom: 1px solid var(--color-border); }
.rank-list .no { width: 20px; color: var(--color-muted); }
.rank-list .amt { font-weight: 600; color: var(--color-income); }
.rank-list .time, .rank-list .cp { color: var(--color-muted); }
</style>
