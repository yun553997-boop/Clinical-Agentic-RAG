# 当前环境背景

我们的全栈智慧医疗平台已具备预约挂号、患者导诊、医生接诊和动态知识库功能。

目前存在体验断层：医生端的 Agent 执行日志太占空间；且生成的 AI 报告医生无法修改、无法下发给患者；患者也无法查看最终的诊断结果。

# 任务目标：优化医生工作台 UX，并打通医患诊断报告反馈闭环 (Doctor-in-the-loop)

请协同修改前后端代码，完成以下任务：

## 第一步：后端数据库模型与 API 升级

1. **修改数据库模型** `backend/models/appointment.py`：
   - 在 `Appointment` 表中新增两个字段：`ai_report` (Text, 存储 AI 生成的初稿或整合后的报告) 和 `doctor_advice` (Text, 存储医生补充的自定义医嘱)。
2. **新增“完成会诊”接口**：
   - 在 `backend/api/endpoints/appointment.py` 中新增 `PUT /api/appointments/{id}/complete`。
   - 接收 JSON 请求体：`{"ai_report": "...", "doctor_advice": "..."}`。
   - 逻辑：更新对应预约记录的上述两个字段，并将 `status` 更新为 `'已完成'`，然后 commit。

## 第二步：优化医生端 AI 会诊工作台 (`src/views/doctor/AiWorkspace.vue`)

1. **获取当前处理的挂号单 ID**：
   - 确保从 Dashboard 跳转过来时（通过 Vue Router 的 query 或 Pinia），能获取到当前正在处理的 `appointment_id`。如果获取不到，给予明确的 UI 提示。
2. **UI 改造：折叠执行日志**：
   - 使用 Element Plus 的 `<el-collapse>` 将“Agent 执行日志”区域包裹起来。标题可以设为“⚙️ 查看 AI 思考与工具调用过程”。默认收起，使其不占用过多垂直空间。
3. **UI 改造：增加医生复核与发报告功能**：
   - 在 AI 生成的 Markdown 报告下方，新增一个区域：“👨‍⚕️ 医生补充医嘱 (可选)”。放置一个 `<el-input type="textarea">` 供医生输入。
   - 新增一个主要操作按钮：“结束会诊并发送报告给患者”。
   - 点击该按钮时，调用 `PUT /api/appointments/{id}/complete`，将当前的 markdown 报告内容和医生补充的医嘱发送给后端。成功后提示并跳转回候诊列表 (Dashboard)。

## 第三步：优化患者端“我的预约记录” (`src/views/patient/Records.vue`)

1. **增加查看报告交互**：
   - 在表格的操作列，如果该行的状态 `status === '已完成'`，显示一个主要按钮“查看诊疗报告”。
   - 点击该按钮，弹出一个 `<el-dialog>`（对话框）或 `<el-drawer>`（抽屉）。
2. **渲染报告内容**：
   - 在弹窗中，优雅地展示该挂号记录的 `ai_report` (最好能使用 markdown-it 渲染) 以及 `doctor_advice` (如果有的话)。

# 约束条件

- 确保所有的前后端交互都有 loading 状态和 ElMessage 的成功/失败提示。
- 后端新增字段如果涉及 Alembic 迁移，请在提示我手动执行，或者在代码中确保 `Base.metadata.create_all(bind=engine)` 能自动更新表结构（如果使用的是轻量级同步）。为了稳定，可以直接让我手动重启后端或删表重建（仅测试环境可用）。
- 直接覆盖相关代码文件。