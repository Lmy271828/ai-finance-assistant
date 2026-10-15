# ai-finance-assistant

AI 个人财务助手 —— 围绕用户自己的算账逻辑打造的财务工具。

---

## 当前进度

**2026-10-15**

### 三个目标功能的完成度

| 功能 | 状态 | 说明 |
|---|---|---|
| **① 跨平台账单导入** | 🟡 **微信已实测通过** | 1058 笔真实数据，与账单自报汇总**分毫不差** |
| | ⚠️ 支付宝未验证 | 代码已写，卡在 ZIP 密码，**未跑过一次** |
| | ⬜ 第三方平台 | 架构已设计（YAML 配置驱动），未实现 |
| **② 生成 preset 报告** | ✅ **7 个接口全部跑通** | 真起 uvicorn 实测，排序/精度/空值约定逐条验证 |
| **③ MCP 接入** | ⬜ 未开始 | 依赖 ①②，均已就绪 |

### 四个核心后端文件（已交付，可直接跑）

```
backend/
├── db.py          连接管理 / 事务边界 / 建表 / 统计
├── schemas.py     12 接口契约 + 字段语义 + 样例数据
├── overrides.py   ★ 写修正的唯一入口（三道 403 防线）
└── main.py        FastAPI 入口（12 个路由，零业务逻辑）
```

**跑起来：**

```bash
pip install -r requirements.txt
python -m uvicorn backend.main:app --reload
# 打开 http://localhost:8000/docs —— 12 个接口可点 Try it out
```

### 已落地的文件

```
db/schema.sql       ✅ 3 表 + 2 视图 + 5 索引（多平台版）
db/bills.db         ✅ 1058 笔微信真实数据（已对账）

backend/
├── db.py           ✅
├── schemas.py      ✅
├── overrides.py    ✅ 三道 403 防线
├── main.py         ✅ 12 路由
├── importer/       ✅ wechat 实测 / alipay 待验
└── reports/        ✅ 7 个组件 + _common.py

frontend/           ✅ 3 页骨架 + data-component 标记
requirements.txt    ✅
```

### 已验证的事实

```
✅ 微信解析 1058 笔，支出/收入/中性 与账单自报数字分毫不差
✅ 重复导入 0 写入 / 1058 跳过
✅ 解析失败 → 整体回滚，一条都没写进去
✅ 脏值归一化：168 笔 pay_method='/'、大量 remark='/' 处理正确
✅ 约束生效：CHECK 拦得住负数金额与非法 direction
✅ 原始层不可变：除 importer/ 外无任何写 transactions_raw 的代码

✅ 7 个报告接口全部 200，排序/精度/空值约定逐条验证
✅ avg = bars 的算术平均（不是 total/n）
✅ pct 之和 ≤ 100（差额是未分类部分）
✅ 日历不返回 amount=0 的空日期，按日期升序
✅ 脏参数在入口被挡 → 400

✅ 403 防线：amount / tx_time / direction / raw_json 全部 403
✅ 混传「修正+原始」也 403
✅ 改一笔 → 视图分类变化，transactions_raw 一个字节没动
✅ updated_by 正确记录入口（ui / mcp）
✅ 撤销修正 → 报告恢复原状
```

### 运行中发现并修掉的两个真 bug

| bug | 症状 | 修法 |
|---|---|---|
| `TxItem.direction` 声明英文枚举但库里存中文 | 明细接口 500 | `_common.type_of()` 映射 |
| Pydantic 默认**静默丢弃**未知字段 | 传 `amount` 返回 **200** 而非 403 | `OverrideIn` 加 `extra="forbid"` + 入口识别原始字段名返回 403 |

第二个不真跑一次绝对发现不了 —— 数据没被改（安全底线还在），但**招牌行为没发生**，调用方还会收到误导的成功响应。

---

## 数据通路的形状（重要，别理解错）

**不是「所有请求先过 schemas.py 再过 overrides.py 才能查数据库」。**
`schemas.py` 不碰数据库，它只是 HTTP/MCP 边界的类型校验。

真实的结构是**三条独立通道，各有唯一的门**：

| 通道 | 唯一入口 | 管什么 | 谁能走 |
|---|---|---|---|
| **写原始层** | `backend/importer/` | 只能 INSERT，绝不 UPDATE | 导入账单 |
| **写修正层** | `backend/overrides.py` | UPSERT + 三道 403 | 前端改分类 / AI 改分类 |
| **读** | `backend/reports/*.py` | 纯 SELECT，查 `v_tx` 视图 | 所有查询 |

查询**不经过** `overrides.py` —— 它只管「改」，不管「读」。

---

## 三条不可动摇的约束

### 1. 原始凭证不可涂改

```
transactions_raw   导入时 INSERT，之后永不 UPDATE
tx_overrides       所有修正落这里
```

代码级证据：`grep -r "UPDATE transactions_raw"` 全项目零命中（除 importer）。

### 2. 前端和 AI 走同一条路

```
前端 PATCH ─┐
            ├─→ overrides.set_override()
MCP tool ───┘
```

否则会出现「前端显示 A，AI 算出 B」，口径立刻分裂。

### 3. 数字由后端算，措辞由 AI 决定

```
MCP → query_summary() → {"total": 1900.00, ...} → AI 决定怎么措辞
```

AI 改不了数字，因为数字来自 SQL。

---

## 下一步

| 优先级 | 事项 | 谁做 |
|---|---|---|
| 1 | `mcp/server.py` —— 11 个工具 | 你 |
| 2 | 支付宝导入验证 | 需要密码 |
| 3 | 第三方平台 YAML 适配器 | 分到导入功能的人 |
| 4 | `frontend/components/` 9 个组件 | 队友 |

---

## 文档结构

```
docs/
├── 设计/
│   ├── 系统设计.md              ← 核心理念与问题定义，长期有效
│   └── 第一轮/
│       ├── 核心设计说明.md        ← 每个文件为什么存在
│       ├── 导入.md               ← 功能一
│       ├── 生成报告.md           ← 功能二
│       └── MCP.md                ← 功能三
│
└── 归档/
    └── v0/                       ← 上一版设计文档
```

---

## 相关资源

`E:/Ufolder/Current/ActionSys/Hgclass/CSSE/proj/正式方案/` 下有：
- `调研/` —— 三份调研报告（平台功能 / AI产品 / 学术文献）
- `归档/` —— 队友交付的 webapp 原型、demo 代码、PPT 文档
