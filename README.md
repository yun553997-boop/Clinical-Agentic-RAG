# Clinical Agentic RAG

智能临床诊疗辅助系统 —— 基于 LangChain Agent + 通义千问 + ChromaDB。

支持**医生**和**患者**两种角色，涵盖 AI 辅助会诊、预约挂号、排班管理、知识库、电子处方筏等完整诊疗流程。

---

## 技术栈

| 层级 | 技术 |
|---|---|
| 后端框架 | Python 3.11 / FastAPI / SQLAlchemy 2.0 (Async) |
| 数据库 | PostgreSQL 16 + asyncpg |
| AI 引擎 | LangChain Agent + 通义千问 (Qwen-plus) |
| 向量存储 | ChromaDB |
| 前端 | Vue 3 (Composition API) / Vite / Element Plus / Tailwind CSS |
| 部署 | Docker + Docker Compose |

---

## 功能模块

### 医生端

| 功能 | 说明 |
|---|---|
| 今日候诊 | 查看当日待就诊患者列表 |
| AI 辅助会诊 | 输入患者症状，AI Agent 调用 RAG 检索 + 历史病例 + 药物禁忌检查，生成诊疗建议 |
| AI 诊断报告 | 查看/生成完整的 AI 诊断报告（Markdown） |
| 出诊排班 | 按日期管理可预约时段，支持添加/删除 |
| 指南知识库管理 | 上传医学 PDF 指南，自动切片存入 ChromaDB |
| 个人信息 | 头像上传（Base64）、职称、专业领域等资料编辑 |
| 电子处方筏 | 为患者开具处方药品 |

### 患者端

| 功能 | 说明 |
|---|---|
| AI 智能导诊 | 对话式症状描述，AI 推荐就诊科室 |
| 预约挂号 | 按科室选医生 → 选排班时段 → 模拟支付 |
| 我的预约记录 | 查看预约状态、取消预约、查看处方筏 |

---

## 核心架构：多工具 Agent

Agent 配备三个自定义 Tool，在 `backend/services/agent_service.py` 中实现：

1. **MedicalGuidelinesRAGTool** — 接收病症关键词，检索 ChromaDB 中的医学指南切片
2. **HistoricalCaseSQLTool** — Text-to-SQL 查询历史相似病例的常见用药
3. **DrugInteractionAPITool** — 检查多种药物配伍禁忌（内置 Mock 字典）

---

## 快速启动

### 前置要求

- Docker Desktop（或 Docker + Docker Compose）

### 一键启动

```bash
# 克隆项目
git clone <repo-url>
cd Clinical-Agentic-RAG

# 启动所有服务（前端 + 后端 + 数据库）
docker compose up -d --build
```

### 访问地址

| 服务 | 地址 |
|---|---|
| 前端页面 | http://localhost |
| 后端 API 文档 (Swagger) | http://localhost:8000/docs |
| 后端健康检查 | http://localhost:8000/ |

### 停止服务

```bash
docker compose down
```

---

## 配置说明

环境变量通过 `docker-compose.yml` 注入后端容器，无需手动创建 `.env` 文件。

| 变量 | 说明 | 默认值 |
|---|---|---|
| `LLM_API_KEY` | 大模型 API Key（通义千问 / DeepSeek） | 必填 |
| `LLM_BASE_URL` | LLM 服务端点 | `https://dashscope.aliyuncs.com/compatible-mode/v1` |
| `LLM_MODEL_NAME` | 模型名称 | `qwen-plus` |
| `DATABASE_URL` | PostgreSQL 连接字符串 | `postgresql+asyncpg://user:password@postgres:5432/agentic_db` |

> 如需更换 LLM_API_KEY，编辑 `docker-compose.yml` 中 `backend.environment.LLM_API_KEY` 的值，然后 `docker compose up -d` 重新启动。

本地开发时，可在 `backend/` 目录下创建 `.env` 文件（会被 `.dockerignore` 排除），直接运行 `uvicorn main:app --reload`。

---

## 项目结构

```
Clinical-Agentic-RAG/
├── backend/
│   ├── api/endpoints/       # FastAPI 路由（auth, users, appointment, schedule, chat, knowledge, payment, prescription）
│   ├── core/                # 配置、数据库引擎、安全模块
│   ├── models/              # SQLAlchemy ORM 模型
│   ├── services/            # LangChain Agent 服务
│   ├── tools/               # Agent 工具（RAG, SQL, API）
│   ├── scripts/             # 数据库初始化脚本
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── views/doctor/    # 医生端页面
│   │   ├── views/patient/   # 患者端页面
│   │   ├── components/      # 公共组件
│   │   ├── stores/          # Pinia 状态管理
│   │   ├── router/          # Vue Router 配置
│   │   └── utils/           # 工具函数（Axios 封装等）
│   ├── Dockerfile
│   └── nginx.conf
├── docker-compose.yml
└── plan/                    # 开发计划与总结文档
```

---

## 容器架构

```
浏览器 → frontend (nginx:80)
           ├── /          → 静态文件 (Vue SPA)
           └── /api/*     → backend (uvicorn:8000) → postgres:5432
```

nginx 反向代理使前后端同源，无需配置 CORS。
