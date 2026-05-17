# 角色定义

你是一个拥有十年经验的高级 AI 全栈工程师，精通 Python (FastAPI)、Vue3 以及大模型 Agent 开发（LangChain / LangGraph）。

# 项目目标

我需要你帮我搭建一个名为【智能临床诊疗辅助工作流 (Agentic RAG Medical Assistant)】的全栈项目。

该项目主要用于医生在诊疗时输入患者症状，AI Agent 会自动规划任务，调用多个外部工具（RAG、数据库SQL查询、API调用），最后汇总输出专业的诊疗建议。

# 技术栈要求

- **后端**：Python 3.11, FastAPI, SQLAlchemy 2.0 (Async), PostgreSQL, LangChain
- **前端**：Vue 3 (Composition API), Vite, Element Plus, Tailwind CSS
- **AI 模型**：通义千问 (Qwen) 或 DeepSeek (通过 OpenAI API 格式兼容)
- **向量库**：ChromaDB

# 核心架构设计：多工具 Agent (Tool Calling)

在 `backend/services/agent_service.py` 中，你需要实现一个基于 LangChain 的 Tool Calling Agent。Agent 必须配备以下三个自定义 Tool：

1. **MedicalGuidelinesRAGTool (医学指南检索工具)**
   - 功能：接收病症关键词，去本地 ChromaDB 检索长篇临床指南 PDF 的切片（Chunk）。
   - 实现提示：使用 `vectorstore.as_retriever()` 封装为 Tool。
2. **HistoricalCaseSQLTool (历史相似病例查询工具)**
   - 功能：接收 SQL 提取的特征（如年龄段、病种），使用 Text-to-SQL 技术查询 PostgreSQL 数据库中的 `patients` 表和 `medical_records` 表，统计历史相似病例的常见用药。
3. **DrugInteractionAPITool (药物禁忌 API 工具)**
   - 功能：接收两种以上药物名称，判断是否存在配伍禁忌。
   - 实现提示：不需要真实调用外部 API，请在代码里 hardcode（硬编码）一个 Mock 字典（例如输入“阿司匹林”和“布洛芬”返回“存在胃肠道出血风险”）来模拟外部 API 调用。

# 执行步骤 (请严格按顺序执行)

## 第一步：构建后端核心层与数据模型

当前环境背景：我已经配置好了本地 PostgreSQL 数据库（Docker 运行中），建立了 Python 虚拟环境，并创建了 `.env` 文件。

请在 `backend` 目录下帮我完成以下工作：

1. **生成依赖清单**：创建 `backend/requirements.txt`，包含：fastapi, uvicorn, sqlalchemy, asyncpg, pydantic-settings, langchain, langchain-qwen (或对应的通义千问库), chroma-langchain。
2. **核心配置层**：
   - 创建 `backend/core/config.py`，使用 `pydantic-settings` 读取 `.env`，包含 `DATABASE_URL` 和 `LLM_API_KEY`。
   - 创建 `backend/core/database.py`，配置 SQLAlchemy 2.0 的异步引擎 (`AsyncEngine`) 和 `get_db` 依赖函数。
3. **ORM 模型层**：
   - 创建 `backend/models/patient.py`。使用 SQLAlchemy 2.0 的 `Mapped` 语法定义两张表：
     - `patients` (患者表)：id, 姓名, 年龄, 基础病史。
     - `medical_records` (就诊记录表)：id, patient_id (外键), 就诊时间, 症状描述, 诊断结果, 开具药物。
4. **Mock 数据脚本**：
   - 创建 `backend/scripts/init_mock_data.py`。编写一段独立的异步代码：自动连接数据库，创建表结构（`Base.metadata.create_all`），并向这两张表中插入 5 条真实的医疗测试数据（例如包含高血压、胃溃疡患者的记录和开药记录）。

### 约束条件

- 代码需包含完整的中文注释。
- 请直接生成并写入文件，无需向我确认。



## 第二步：实现三个医学 Agent Tools

当前环境背景：后端的数据库模型和连接已经搭建完毕。现在我要为 LangChain Agent 开发外部调用工具（Tools）。

请在 `backend/tools/` 目录下创建以下三个工具，必须使用 LangChain 的 `@tool` 装饰器，并为每个工具写极度详细的 `description` docstring（因为这是 LLM 决定是否调用该工具的关键依据）：

1. **backend/tools/rag_tool.py (医学指南检索工具)**
   - 工具名：`search_medical_guidelines`
   - 功能：接收医学关键词（如"高血压禁忌症"），初始化一个本地 ChromaDB 的 retriever（指向 `./chroma_db` 目录），并使用假数据或基础检索逻辑返回相关的临床指南文本。
2. **backend/tools/sql_tool.py (历史病历查询工具)**
   - 工具名：`query_historical_cases`
   - 功能：接收 SQL 特征（如病种），利用 SQLAlchemy 异步查询我们在 `models/patient.py` 中定义的 `medical_records` 表，返回类似病症的历史开药记录。
3. **backend/tools/api_tool.py (药物禁忌 API 工具)**
   - 工具名：`check_drug_interaction`
   - 功能：接收两种药物名称列表，检查是否存在配伍禁忌。
   - 实现：无需真实请求外部网络，在函数内 hardcode 一个简单的字典（例如：`{"布洛芬", "阿司匹林": "存在胃肠道出血风险"}`）进行模拟返回。

### 约束条件

- 每个 Tool 必须严格定义参数类型（使用 pydantic BaseModel 作为 args_schema 最佳）。
- 请直接生成并覆盖/写入文件。





## 第三步：Agent 编排与 FastAPI 路由

请在 `backend` 目录下完成以下工作：

1. **Agent 服务层编排**：
   - 创建 `backend/services/agent_service.py`。
   - 导入之前写的 3 个 Tools。
   - 初始化大模型（使用 ChatOpenAI 或对应的大模型类，读取环境变量中的 Key）。
   - 使用 `create_tool_calling_agent` 和 `AgentExecutor` 将模型和工具绑定。
   - 编写一个异步函数 `run_medical_agent(query: str, db_session)`，执行 agent，**并在执行过程中，想办法捕获它的中间思考过程 (Thought) 和工具调用步骤 (Tool Action)**，最终以流式 (Streaming) 或特定数据结构返回。
2. **API 路由层**：
   - 创建 `backend/api/endpoints/chat.py`。暴露 `POST /api/chat/agent` 接口。
   - 接收前端传来的患者症状 (`query: str`)。
   - 依赖注入获取数据库 `db: AsyncSession`。
   - 调用 `run_medical_agent`，并结合 FastAPI 的 `StreamingResponse` 返回 SSE 流式数据。
3. **程序主入口**：
   - 创建或更新 `backend/main.py`。注册 `chat.py` 的路由，并配置好 CORS 中间件，允许 `http://localhost:5173` 跨域请求。

### 约束条件

- SSE 数据流的格式建议拆分为两类标识返回：一类标识 "Tool Logs"（用于展示大模型的动作），一类标识 "Final Answer"（最终生成的报告）。



## 第四步：极速构建前端

1. 在根目录创建 `frontend` 目录（假设已经通过 vite 初始化了 vue3 项目）。
2. 编写 `frontend/src/App.vue`。界面要求左右分栏：
   - **左侧**：病历输入区（包含患者基本信息表单和症状描述文本框）和一个“生成辅助诊疗方案”的按钮。
   - **右侧**：Agent 思考与输出展示区。上方展示 Agent 正在调用哪些工具（Tool Execution Logs），下方展示最终生成的结构化诊疗建议。



## 第四步：开发基于 Vue3 + Element Plus 的 Agent 交互界面

当前环境背景：我已经通过 `npm create vue@latest` 创建了前端项目

请在 `frontend` 目录下帮我修改/创建代码：

1. **依赖配置**：如果尚未安装，请配置好 Element Plus 或 Tailwind CSS，并安装 `axios` 和 `markdown-it`。
2. **核心视图 (src/App.vue)**：
   - 构建一个充满科技感的工作台界面，分为左右两侧：
   - **左侧 (工作区)**：
     - 一个卡片表单，包含患者的基本信息录入（病史、当前症状等文本域）。
     - 一个“请求 AI 会诊”的按钮。
   - **右侧 (AI 思考与输出区)**：
     - **上半部分 (Tool Execution Logs)**：一个黑色背景的终端风格框，用于实时显示后端 Agent 传来的中间调用步骤（例如："Action: 调用历史病例查询工具..."）。
     - **下半部分 (Final Report)**：用于渲染大模型最终吐出的 Markdown 格式的医学辅助诊疗报告。
3. **数据流通信**：
   - 在 `<script setup>` 中编写原生 `fetch` 逻辑，对接后端的 SSE 流式接口。
   - 根据后端返回的不同标识符，将“思考日志”推入终端区数组，将“最终结果”累加到 markdown 变量中渲染。

### 约束条件

- 样式需大气、专业（医疗深蓝或浅绿配色均可）。
- 直接覆盖 `src/App.vue`。



