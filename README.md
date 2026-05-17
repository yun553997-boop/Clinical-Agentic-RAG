# 📚 Clinical Agentic RAG

智能临床诊疗辅助工作流 —— 基于 LangChain Agent + 通义千问 + ChromaDB。

该项目主要用于医生在诊疗时输入患者症状，AI Agent 会自动规划任务，调用多个外部工具（RAG、数据库SQL查询、API调用），最后汇总输出专业的诊疗建议。

## 🛠️ 技术栈 (Tech Stack)

- **后端**：Python 3.11, FastAPI, SQLAlchemy 2.0 (Async), PostgreSQL, LangChain
- **前端**：Vue 3 (Composition API), Vite, Element Plus, Tailwind CSS
- **AI 模型**：通义千问 (Qwen) 或 DeepSeek (通过 OpenAI API 格式兼容)
- **向量存储**：ChromaDB (本地轻量级向量库)
- **部署与工程化**：Docker + Docker Compose

## ✨ # 核心架构设计：多工具 Agent (Tool Calling)

在 `backend/services/agent_service.py` 中，你需要实现一个基于 LangChain 的 Tool Calling Agent。Agent 必须配备以下三个自定义 Tool：

1. **MedicalGuidelinesRAGTool (医学指南检索工具)**
   - 功能：接收病症关键词，去本地 ChromaDB 检索长篇临床指南 PDF 的切片（Chunk）。
   - 实现提示：使用 `vectorstore.as_retriever()` 封装为 Tool。
2. **HistoricalCaseSQLTool (历史相似病例查询工具)**
   - 功能：接收 SQL 提取的特征（如年龄段、病种），使用 Text-to-SQL 技术查询 PostgreSQL 数据库中的 `patients` 表和 `medical_records` 表，统计历史相似病例的常见用药。
3. **DrugInteractionAPITool (药物禁忌 API 工具)**
   - 功能：接收两种以上药物名称，判断是否存在配伍禁忌。
   - 实现提示：不需要真实调用外部 API，请在代码里 hardcode（硬编码）一个 Mock 字典（例如输入“阿司匹林”和“布洛芬”返回“存在胃肠道出血风险”）来模拟外部 API 调用。

## 🚀 快速启动 (Quick Start)

1. 克隆本项目到本地
2. 在 `backend` 目录下创建 `.env` 文件，填入你的 API Key：
   
   ```env
   DASHSCOPE_API_KEY="你的通义千问API密钥"
   ```
4. 在项目根目录执行一键启动命令：
   ```Bash
   docker-compose up -d --build
   ```
   
访问前端页面：http://localhost

访问后端接口文档：http://localhost:8000/docs
