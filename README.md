# ai-finance-assistant

AI 个人财务助手 —— 围绕用户自己的算账逻辑打造的财务工具。

---

## 跑起来

**第一次 / 换电脑：**

```powershell
.\scripts\setup.ps1
```

**以后每次：**

```powershell
.\scripts\start-all.ps1     # 前端 + 后端各开一个窗口
```

| 地址 | 是什么 |
|---|---|
| <http://localhost:5173> | 前端页面 |
| <http://localhost:8000/docs> | 接口文档，可直接 Try it out |
| <http://localhost:8000/health> | 存活探针 |

单独启动 / 出问题：

```powershell
.\scripts\start-backend.ps1     # 只起后端 (8000)
.\scripts\start-frontend.ps1    # 只起前端 (5173)
.\scripts\check.ps1             # 自检：缺什么、哪个服务没起来
```

### 三个坑（都是实测踩出来的，别改回去）

**1. 必须用 `.venv`。** `fastapi` 会拽着 `starlette` 一起装。直接 `pip install` 到全局 Anaconda 会把全局 starlette 降级，弄坏别的项目。所有脚本已强制走项目 venv。

**2. 前端必须在后端跑着的时候开。** 前端写相对路径 `/api/xxx`，靠 `vite.config.ts` 的 proxy 转发到 8000。**代码里不允许硬编码 `http://localhost:8000`** —— 开发能跑，部署必挂。

**3. Windows 编码。** 本项目所有 `.ps1` 必须是 **UTF-8 with BOM**（PowerShell 5.1 按 GBK 读，无 BOM 会乱码）；`requirements.txt` 同理。改脚本时别把 BOM 弄丢。

---

## 当前进度（2026-10-15）

| 功能 | 状态 |
|---|---|
| ① 跨平台账单导入 | 🟡 微信已实测通过（1058 笔，与账单自报汇总分毫不差）；支付宝已写未验证（缺 ZIP 密码）；其他平台未开始 |
| ② 生成 preset 报告 | ✅ 7 个接口全部跑通 |
| ③ MCP 接入 | ⬜ 未开始，依赖 ①② |

---

## 必须先看懂的一件事：三条通道

**不是「请求先过 schemas.py 再过 overrides.py 才能查库」。**
`schemas.py` 不碰数据库，它只是 HTTP/MCP 边界的类型校验。

真实结构是**三条独立通道，各有唯一的门**：

| 通道 | 唯一入口 | 能做什么 |
|---|---|---|
| 写原始层 | `backend/importer/` | 只能 INSERT，**绝不 UPDATE** |
| 写修正层 | `backend/overrides.py` | UPSERT + 三道 403 防线 |
| 读 | `backend/reports/*.py` | 纯 SELECT，查 `v_tx` 视图 |

查询**不经过** `overrides.py` —— 它只管「改」，不管「读」。

### 由此推出的三条硬约束

**1. 原始凭证不可涂改。**

```
transactions_raw   导入时 INSERT，之后永不 UPDATE
tx_overrides       所有修正落这里
```

`grep -r "UPDATE transactions_raw"` 全项目零命中。想改分类，走 `overrides.py`。

**2. 前端和 AI 必须走同一条路。** 否则会出现「前端显示 A，AI 算出 B」，口径立刻分裂。

**3. 数字由后端算，措辞由 AI 决定。** MCP 拿到的数字来自 SQL，AI 改不了它，只能决定怎么措辞。

---

## 目录

```
db/schema.sql          3 表 + 2 视图 + 5 索引
backend/
  db.py                连接管理 / 事务边界 / 建表
  schemas.py           13 个接口的契约 + 字段语义 + 样例
  overrides.py         ★ 写修正的唯一入口
  main.py              FastAPI 入口（零业务逻辑）
  importer/            账单解析（wechat 已验证 / alipay 待验）
  reports/             7 个报告组件
frontend/src/views/    3 页骨架（账单 / 导入 / 改单）
scripts/               setup / start-all / start-*-* / check
docs/设计/             设计文档
```

`db/bills.db` 是各自的本地账本，不入库（gitignored）。

---

## 文档

| 文档 | 什么时候看 |
|---|---|
| `docs/设计/系统设计.md` | 长期愿景与问题定义 |
| `docs/设计/第一轮/00_整体架构.md` | 三条通道为什么这么分 |
| `01_数据库.md` | 表结构与去重、事务设计 |
| `02_后端.md` | 三个核心文件各自解决什么 |
| `03_前端.md` | 骨架结构与分工边界 |
| `04_MCP.md` | MCP 层的边界与安全 |
| `1-1_导入.md` / `1-2_生成报告.md` / `1-3_MCP接入.md` | 三个功能各自的目标与进度 |

---

## 下一步

| 事项 | 谁做 |
|---|---|
| `mcp/server.py` —— 11 个工具 | 你 |
| 支付宝导入验证 | 需要解压密码 |
| 第三方平台适配（美团 / 银行卡 / 电商） | 分到导入功能的人 |
| `frontend/components/` 9 个组件 | 队友 |
