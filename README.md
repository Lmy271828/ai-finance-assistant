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
| **② 生成 preset 报告** | ⬜ 未开始 | 数据已就位，契约已定义 |
| **③ MCP 接入** | ⬜ 未开始 | 依赖 ① ② 与 `overrides.py` |

### 已落地的文件

```
db/
├── schema.sql              ✅ 3 表 + 2 视图 + 5 索引（多平台版）
└── bills.db                ✅ 1058 笔微信真实数据

backend/
├── db.py                   ✅ 连接 / 事务 / 建表 / 统计
├── schemas.py              ✅ 11 接口契约 + 样例数据
├── importer/
│   ├── __init__.py         ✅ 编排 + 全事务 + 平台自动注册
│   ├── base.py             ✅ 归一化 + dedupe_key
│   ├── wechat.py           ✅ 实测通过
│   └── alipay.py           ⚠️ 已写未验证
└── main.py / overrides.py / reports/   ⬜ 未写

frontend/
├── vite.config.ts          ✅ 含 proxy（前端不出现 localhost:8000）
└── src/                    ✅ 3 页骨架 + data-component 标记
```

### 已验证的事实

```
✅ 微信解析 1058 笔，支出/收入/中性 与账单自报数字分毫不差
✅ 重复导入 0 写入 / 1058 跳过
✅ 解析失败 → 整体回滚，一条都没写进去
✅ 脏值归一化：168 笔 pay_method='/'、大量 remark='/' 处理正确
✅ 约束生效：CHECK 拦得住负数金额与非法 direction
✅ 原始层不可变：除 importer/ 外无任何写 transactions_raw 的代码
```

---

## 下一步

| 优先级 | 事项 | 谁做 |
|---|---|---|
| 1 | `backend/overrides.py` —— 修正唯一入口，核心卖点 | 你 |
| 2 | `backend/main.py` —— 11 路由返回假数据 | 你 |
| 3 | `backend/reports/*.py` —— 7 个组件 | 分工 |
| 4 | `mcp/server.py` —— 11 个工具 | 你 |
| 5 | 支付宝导入验证 | 需要密码 |

---

## 文档结构

```
docs/
├── 设计/
│   ├── 系统设计.md              ← 核心理念与问题定义，长期有效
│   └── 第一轮/
│       ├── 核心设计说明.md        ← 每个文件为什么存在
│       ├── 导入.md               ← 功能一：跨平台账单导入
│       ├── 生成报告.md           ← 功能二：preset 报告
│       └── MCP.md                ← 功能三：AI 接入
│
└── 归档/
    └── v0/                       ← 上一版设计文档，保留参考
        ├── 01_原始账单格式.md
        ├── 02_账单页面设计.md
        ├── 03_功能审计.md
        ├── 04_后端设计.md
        ├── 05_核心设计说明.md
        ├── 06_API契约.md
        └── 系统架构_第一轮.md
```

---

## 三条不可动摇的约束

### 1. 原始凭证不可涂改

```
transactions_raw   导入时 INSERT，之后永不 UPDATE
tx_overrides       所有修正落这里
```

已用代码级证据验证：`grep -r "UPDATE transactions_raw"` 全项目零命中（除 importer）。

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

## 相关资源

`E:/Ufolder/Current/ActionSys/Hgclass/CSSE/proj/正式方案/` 下有：
- `调研/` —— 三份调研报告（平台功能 / AI产品 / 学术文献）
- `归档/` —— 队友交付的 webapp 原型、demo 代码、PPT 文档
