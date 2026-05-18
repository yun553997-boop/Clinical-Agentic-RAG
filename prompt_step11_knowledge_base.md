# 当前环境背景

系统已具备完善的 RBAC 权限、医生工作台和患者导诊等业务流。后端的 Agent 已经能够调用 `rag_tool` 查询本地的 ChromaDB。

目前缺少一个动态的知识库管理页面，允许用户通过前端界面上传新的医疗指南（PDF），并自动向量化注入到大模型的知识库中。

# 任务目标：实现动态 RAG 知识注入流水线与管理后台

请在 `backend` 和 `frontend` 目录下协同修改/创建以下文件：

## 第一步：后端新增依赖与数据库模型

1. 更新 `backend/requirements.txt`：补充 `pypdf`（用于解析PDF文档） 和 `python-multipart`（如果之前未安装，用于接收文件上传）。
2. 在 `backend/models/` 下新建 `knowledge.py`：
   - 使用 SQLAlchemy 创建 `KnowledgeDoc` 表：`id`, `filename` (文件名), `upload_time` (上传时间), `uploader_id` (关联 User 表的上传者), `status` (状态，如 '已向量化')。
   - （请记得在 `backend/core/database.py` 的 Base.metadata 中确保它能被创建）。

## 第二步：开发后端知识库 API (RAG Pipeline)

创建 `backend/api/endpoints/knowledge.py`，实现以下接口（需要注入 `get_current_user` 确保只有医生可操作）：

1. **获取文档列表 GET /api/knowledge/**：
   - 从 `KnowledgeDoc` 表中查询所有已上传的文档记录，并关联查询出上传者的 `full_name`，按时间倒序返回。
2. **上传并向量化文档 POST /api/knowledge/upload**：
   - 接收 `file: UploadFile = File(...)`。
   - **核心流水线**：
     1. 将文件临时保存到本地磁盘（如 `backend/data/uploads/` 目录）。
     2. 在数据库 `KnowledgeDoc` 中创建一条新记录。
     3. 使用 LangChain 的 `PyPDFLoader` 加载该 PDF。
     4. 使用 `RecursiveCharacterTextSplitter` 进行文本切分（如 chunk_size=500, chunk_overlap=50）。
     5. 获取之前在 `rag_tool` 中使用的同一个 ChromaDB 实例和 Embedding 模型。
     6. 将切分后的文档片段存入 ChromaDB，并在 metadata 中打上 `{"doc_id": db_doc.id, "source": filename}` 的标签。
     7. 返回上传成功的响应。
3. **删除文档 DELETE /api/knowledge/{doc_id}**：
   - 从 PostgreSQL 中删除该记录。
   - （进阶选做：如果 ChromaDB API 支持，根据 metadata 里的 `doc_id` 删除对应的向量数据）。

## 第三步：前端路由与侧边栏改造

1. 修改 `src/router/index.ts`：在 `path: '/doctor'` 的 `children` 数组中，新增子路由：
   - `path: 'knowledge'`
   - `name: 'DoctorKnowledge'`
   - `component: () => import('@/views/doctor/KnowledgeBase.vue')`
2. 修改 `src/layout/MainLayout.vue`：在角色为 `doctor` 的左侧 `el-menu` 中，在“AI 辅助会诊”下方新增一项：
   - `<el-menu-item index="/doctor/knowledge">指南知识库管理</el-menu-item>`

## 第四步：开发前端“指南知识库管理”页面

新建文件 `src/views/doctor/KnowledgeBase.vue`：

1. **界面布局**：
   - 顶部：一个带有 `<el-upload>` 组件的操作区。配置其采用自定义上传行为（覆盖默认的 action），在用户选择文件后，使用 `FormData` 和封装好的 `request.post` 提交到 `/api/knowledge/upload`。
   - 底部：使用 `<el-table>` 展示从 `GET /api/knowledge/` 获取的文档列表（包含字段：文件名、上传者、上传时间、状态、操作列）。
2. **交互逻辑**：
   - 上传时需要有 `el-button` 的 loading 状态，因为向量化大文件可能需要几秒钟。上传成功后提示 `ElMessage.success` 并重新拉取表格数据。
   - 在表格操作列增加“删除”按钮，绑定 DELETE 接口并刷新列表。

# 约束条件

- 后端保存上传文件时，请确保 `backend/data/uploads/` 目录存在，如果不存在请用代码 `os.makedirs` 自动创建。

- 确保 ChromaDB 的初始化逻辑与 `rag_tool.py` 中保持绝对一致（同一个持久化路径，同一个 Embedding 模型），否则 Agent 将检索不到新上传的知识！

- 请直接生成并覆盖写入文件。

  ​