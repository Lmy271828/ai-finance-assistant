# 功能三：MCP 接入

> 代码位置：`mcp/server.py`（**未写**）
> 当前状态：⬜ 未开始
> 依赖：功能一（导入）、功能二（报告）、`overrides.py` 全部就绪后才写

---

## 一、设计目的

**AI 不在应用内部，在用户自己的 AI 里。**

传统做法是把 AI 嵌进 App，AI 和数据库、界面绑死。用户只能用这个 App 预设的问法，想换个角度问都做不到。

我们的做法：

```
┌─────────────────────┐
│ 用户的 AI            │  Claude / 豆包 / 任何 MCP 客户端
│ （不在我们应用里）    │
└──────────┬──────────┘
           │ MCP
┌──────────▼──────────┐
│  mcp/server.py      │
└──────────┬──────────┘
           │ 调用同一批 Python 函数
     ┌─────┴─────┐
     ▼           ▼
  reports/*   overrides.py
```

**用户换 AI、换问法、换角度，账本不用动。**

---

## 二、11 个工具

### 只读（9 个）

| 工具 | 调用的后端 | 说明 |
|---|---|---|
| `query_summary` | `reports/summary.py` | 周期总额 |
| `query_calendar` | `reports/calendar.py` | 每日明细 |
| `query_trend` | `reports/trend.py` | 趋势 + 均值 |
| `query_by_category` | `reports/category.py` | 分类统计 |
| `query_by_method` | `reports/method.py` | 支出方式 |
| `query_income_rank` | `reports/income_rank.py` | 收入排行 |
| `query_transactions` | `reports/transactions.py` | 明细查询 |
| `get_tx_detail` | `overrides.get_tx_detail` | 单笔原始+修正全貌 |
| `list_pending_classification` | `v_tx` 查询 | 未被人工分类过的笔 |

### 可写（2 个）

| 工具 | 写入目标 | 说明 |
|---|---|---|
| `import_bill` | `transactions_raw`（INSERT） | 唯一允许的原始层写入 |
| `set_override` | `tx_overrides`（UPSERT） | 唯一允许的修正层写入 |

> **11 个工具里只有 2 个能写。** AI 面对 50 个工具会懵，面对 11 个会用。

---

## 三、写权限的硬边界

这是整个项目的核心卖点，也是第一轮最重要的验证点。

### 三道防线

```
① 协议层   OverrideIn 里根本没有原始字段名
           ↓ AI 读 schema 生成工具定义，看不到 amount

② 运行时   overrides.py 里的 FORBIDDEN_FIELDS 黑名单

③ 结构层   overrides.py 中不存在任何 UPDATE/DELETE transactions_raw 的代码路径
           ↓ 前两道是约定，第三道是物理事实
```

### 最硬的那条

```python
# overrides.py 里只有这一条 SQL 涉及写操作：
"INSERT INTO tx_overrides (...) VALUES (...) ON CONFLICT(tx_id) DO UPDATE ..."

# 全项目 grep "UPDATE transactions_raw" → 零命中（已实测 ✅）
```

**即使前两道被绕过，代码里也没有那条路径。**

### 可追溯

每次写入记录 `updated_by`：

```
updated_by = 'ui'    前端改的
updated_by = 'mcp'   AI 改的
```

三个月后你查一眼就知道这笔是人改的还是 AI 改的。**可追溯不是靠注释，是靠字段。**

---

## 四、AI 怎么用

### 用户问「9月花了多少」

```
AI → query_summary(type=expense, period=month, value=2026-09)
    ← {"total": 1900.00, "prev": 2800.00, "delta": -884.58,
       "rate": -31.7, "count": 61}
AI → "9月支出 1900.00 元，共 81 笔，比 8 月少花了 884.58 元（降 31.7%）。"
```

**注意最后一步**：措辞是 AI 决定的，**数字是后端算的**。

AI 可以换说法、换语气、加上下文，但**改不了数字**——数字来自 SQL，不是来自 AI 的记忆或推理。

### AI 发现分类太粗

```
AI → query_by_category(...)
    ← {"majors": [{"major": "商户消费", "count": 707, ...}]}

AI（对话）→ "商户消费占 55%，太粗了，能拆细吗？"
用户 → "把美团、某快餐、某快餐归到餐饮美食"

AI → set_override(tx_id=1, manual_category="餐饮美食")
    ← {"tx_id": 1, "manual_category": "餐饮美食", "updated_by": "mcp"}
```

**原始的 `tx_type` 仍然是「商户消费」，一个字节没动。**

### AI 帮你做批量修正

```
AI → list_pending_classification(limit=50)
    ← [30 笔没有被人工分类过的交易]

AI → 对每笔调 set_override(manual_category=...)
```

---

## 五、工具 schema 的来源

**不手写。** MCP 工具的 input schema 直接从 `backend/schemas.py` 派生：

```python
from mcp.server.fastmcp import FastMCP
from backend import schemas

mcp = FastMCP("ai-finance-assistant")

@mcp.tool()
def set_override(tx_id: int, data: schemas.OverrideIn) -> schemas.OverrideResp:
    """修改一笔交易的分类/豁免/备注。原始字段不可修改。"""
    return overrides.set_override(tx_id, data, updated_by="mcp")
```

**这样保证了 MCP 的 schema 和 HTTP 的 schema 永远一致**——因为它们本来就是同一个 Pydantic 模型。

---

## 六、两个入口必须走同一条路

```
前端点"改分类"    → PATCH /api/tx/1/override → overrides.set_override(..., 'ui')
AI 说"这笔改零食"  → tool: set_override        → overrides.set_override(..., 'mcp')
        ↓
    同一份代码、同一个校验、同一张表
```

**如果不这样，会出现「前端显示 A，AI 算出 B」，口径立刻分裂。**

MCP Server 里**不自己拼 SQL**，只调后端函数。

---

## 七、实现要点

### 7.1 密码问题（导入时）

支付宝账单 ZIP 是加密的，AI 调 `import_bill` 时拿不到密码怎么办？

**第一轮方案**：`import_bill` 的 `password` 是可选参数，用户在前端导入页自己填。AI 调导入时如果不带密码，返回明确错误提示用户在前端操作。

**不要让 AI 去猜密码。**

### 7.2 上下文窗口

AI 调 `query_transactions` 时不能一次拉 5000 条。`TxQuery` 的 `size` 上限 200，返回时带 `total`，让 AI 自己决定要不要分页。

### 7.3 错误信息要能指导 AI 下一步

```python
# ❌ "error"
# ✅ "9月没有数据。先确认是否已导入：调用 list_import_batches()"
```

**AI 靠错误信息决定下一步做什么**，所以错误信息必须可操作。

### 7.4 别一次给太多

`query_by_category` 返回的 `tx_ids` 上限 200 个，超出时 AI 应该改用 `query_transactions(category=...)` 而不是拿到截断的 ID 列表。

---

## 八、验收标准

- [ ] AI 客户端能列出 11 个工具
- [ ] 每个工具的 schema 与 HTTP 契约一致
- [ ] `query_summary` 返回的数字与前端页面完全一致
- [ ] `set_override` 成功后 `tx_overrides.updated_by == 'mcp'`
- [ ] `set_override` 传原始字段 → 403
- [ ] `grep -r "UPDATE transactions_raw" mcp/` → 零命中
- [ ] 全项目 `grep -r "UPDATE transactions_raw" backend/` → 零命中（除 importer）
- [ ] AI 改一笔后，刷新前端页面，**数字变化仍在**

> 最后一条最重要——它证明 AI 的修改真的落库了，不是只在它自己的对话里生效。

---

## 九、给队友的一句话

**不要给 MCP 写自己的数据访问代码。**

```
❌ 在 mcp/server.py 里直接 conn.execute("UPDATE ...")

✅ 在 mcp/server.py 里调 overrides.set_override(...)
```

理由：`overrides.py` 是唯一有 403 校验的地方。BYPASS 它写 SQL，等于把整个项目的核心约束作废。
