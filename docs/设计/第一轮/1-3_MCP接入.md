# 1-3 · 功能三：MCP 接入

> 状态：⬜ 未实现（依赖的 ①② 均已就绪，可随时开工）
> 边界与安全的设计思路见 `04_MCP.md`

---

## 一、已有的是什么

后端是一套完整的 HTTP API，12 个接口。

## 二、存在什么问题没解决

**AI 只能通过 HTTP 自己抓，但这样它看不到工具说明。**

AI 拿到一个 URL 不知道该传什么参数，返回的 JSON 也不知道每个字段什么意思。让 AI 去猜参数名，它会猜错，然后基于错误数据给出错误答案——**而且看起来很合理。**

---

## 三、提出的设计

### 11 个工具

**只读 9 个：**

| 工具 | 调用的后端 |
|---|---|
| `query_summary` | `reports.summary` |
| `query_calendar` | `reports.calendar` |
| `query_trend` | `reports.trend` |
| `query_by_category` | `reports.category` |
| `query_by_method` | `reports.method` |
| `query_income_rank` | `reports.income_rank` |
| `query_transactions` | `reports.transactions` |
| `get_tx_detail` | `overrides.get_tx_detail` |
| `list_pending_classification` | 未被人工分类过的笔 |

**可写 2 个：**

| 工具 | 写入目标 |
|---|---|
| `import_bill` | `transactions_raw`（只 INSERT） |
| `set_override` | `tx_overrides` |

**11 个里只有 2 个能写。** 理由见 `04_MCP.md`。

---

## 四、AI 实际怎么用

### 场景 1：普通查询

```
用户：9月花了多少

AI → query_summary(type=expense, period=month, value=2026-09)
    ← {"total": 1900.00, "prev": 2800.00, "delta": -900.00,
       "rate": -32.1, "count": 82}

AI → "9月支出 1900.00 元，共 82 笔，比 8 月少花了 900.00 元（降 32.1%）。"
```

**注意最后一步：措辞是 AI 决定的，数字是后端算的。**

AI 可以换说法、换语气、加上下文，但**改不了数字**——数字来自 SQL，不是来自 AI 的记忆或推理。

### 场景 2：分类太粗

```
用户：商户消费占 60%，太粗了，能拆细吗？

AI → 查询数据，发现 707 笔都是「商户消费」
AI → "其中美团 312.00、麦当劳 185.50，能归到餐饮美食吗？"

用户：可以

AI → set_override(tx_id=1, manual_category="餐饮美食")
    ← {"tx_id": 1, "manual_category": "餐饮美食", "updated_by": "mcp"}
```

**原始的 `tx_type` 仍然是「商户消费」，一个字节没动。**

### 场景 3：批量修正

```
AI → list_pending_classification(limit=50)
    ← [30 笔没有被人工分类过的交易]

AI → 对每笔调 set_override(manual_category=...)
```

---

## 五、实现要点

### 5.1 工具定义直接用现有 Pydantic 模型

```python
from mcp.server.fastmcp import FastMCP
from backend import schemas, overrides, reports

mcp = FastMCP("ai-finance-assistant")

@mcp.tool()
def set_override(tx_id: int, data: schemas.OverrideIn) -> schemas.OverrideResp:
    """修改一笔交易的分类/豁免/备注。原始字段不可修改。"""
    return overrides.set_override(tx_id, data, updated_by="mcp")
```

**不要在 MCP 里重新定义一遍参数模型。** 用 `schemas.OverrideIn`，MCP 的 schema 和 HTTP 的 schema 就永远不会对不上。

### 5.2 支付宝密码问题

支付宝 ZIP 是加密的。AI 调 `import_bill` 时拿不到密码。

**第一轮方案**：`password` 是可选参数，用户在前端导入页自己填。AI 调导入时不带密码，返回明确提示让用户在前端操作。

**不要让 AI 去猜密码。**

### 5.3 别一次给太多

`TxQuery.size` 上限 200，返回时带 `total`，让 AI 自己决定要不要分页。

`query_by_category` 的 `tx_ids` 超过 200 会截断，AI 应该改用 `query_transactions(category=...)` 而不是拿到截断的 ID 列表。

### 5.4 错误信息要能指导 AI 下一步

```python
# ❌ "error"
# ✅ "9月没有数据。先确认是否已导入：调用 list_import_batches() 查看"
```

**AI 靠错误信息决定下一步做什么**，错误信息必须可操作。

---

## 六、验收标准

- [ ] AI 客户端能列出 11 个工具
- [ ] 每个工具的 schema 与 HTTP 契约一致
- [ ] `query_summary` 返回的数字与前端页面完全一致
- [ ] `set_override` 成功后 `tx_overrides.updated_by == 'mcp'`
- [ ] AI 改一笔后，**刷新前端页面数字变化仍在**（证明真落库了）
- [ ] `grep -r "sqlite3\|conn.execute" mcp/` → 零命中
- [ ] `grep -r "UPDATE transactions_raw" mcp/` → 零命中

---

## 七、给实现者的一句话

**不要给 MCP 写自己的数据访问代码。**

```
❌ 在 mcp/server.py 里直接 conn.execute("UPDATE ...")
✅ 在 mcp/server.py 里调 overrides.set_override(...)
```

`overrides.py` 是唯一有 403 校验的地方。绕过它写 SQL，等于把整个项目的核心约束作废。

---

## 延伸

`04_MCP.md`（边界与安全）· `02_后端.md` · `1-1_导入.md`
