# 当前环境背景

患者预约挂号页面的 `doctor_id` 目前是硬编码的，导致新注册的医生无法看到自己的候诊单。

# 任务目标：实现“科室 -> 医生”的级联选择功能

请帮我修改后端 API 和前端页面，彻底修复这个逻辑断层。

## 第一步：后端新增“获取医生列表”接口

请修改 `backend/api/endpoints/auth.py`（或者创建 `users.py` 并注册路由），新增一个接口：

- `GET /api/users/doctors`
- 参数：接收一个可选的 query 参数 `department: str = None`。
- 逻辑：查询 `User` 表中 `role == 'doctor'` 的记录。如果传了 `department`，则加上过滤条件。
- 返回：返回医生的列表，包含字段 `[{"id": 1, "full_name": "张医生", "department": "消化内科"}]`。

## 第二步：前端封装新的请求接口

请在前端 `src/utils/request.ts` 或直接在页面中，实现对接 `/api/users/doctors` 的 GET 请求。

## 第三步：前端 Appointment.vue 页面重构 (级联下拉)

请大幅修改 `src/views/patient/Appointment.vue`：

1. **新增状态**：增加 `doctorsList` 数组用于存放从后端拉取的医生数据。
2. **UI 改造**：在“选择科室”的下拉框下方，新增一个“选择医生”的 `<el-select>`，绑定到 `form.doctor_id`。
3. **级联逻辑 (Watch/Change)**：
   - 监听（watch 或 @change）科室 `form.department` 的变化。
   - 当科室改变时：首先清空当前的 `form.doctor_id`，然后向后端 `GET /api/users/doctors?department=xxx` 发起请求，获取该科室下的所有真实医生，并赋值给 `doctorsList`。
   - 如果某科室下没有医生，请在下拉框提示“暂无医生排班”。
4. **修复提交逻辑**：将 `submitAppointment` 中的 `doctor_id: 1` 替换为真实的 `form.doctor_id`。并且在提交前校验是否选择了医生。

# 约束条件

- 前端必须有良好的用户体验，科室切换时医生列表要平滑更新。
- 后端查询必须使用 `AsyncSession`。
- 直接生成并覆盖相应文件。