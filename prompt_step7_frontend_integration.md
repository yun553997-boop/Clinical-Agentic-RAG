# 当前环境背景

我的前端 Vue3 项目已经完成了多角色路由骨架和注册页面的 UI。后端已经完成了 JWT 鉴权 (`/api/auth/login`, `/api/auth/register`) 和挂号业务 API (`/api/appointments/`, `/api/appointments/today`)。

目前前端的登录、注册和业务页面仍然是 Mock 假数据。

# 任务目标：打通前端与真实的后端 API，实现真实鉴权与医患数据流转

请在 `frontend` 目录下帮我完成以下工作：

## 第一步：封装 Axios 请求与拦截器

创建 `src/utils/request.ts`：

1. 创建 axios 实例，`baseURL` 设置为 `http://localhost:8000`。
2. 添加**请求拦截器**：如果 Pinia 的 userStore 中有 `token`，则在请求头自动带上 `Authorization: Bearer <token>`。
3. 添加**响应拦截器**：统一处理网络错误，特别是 401 错误（Token 过期或未登录），触发退出登录逻辑并跳转回 `/login`。使用 Element Plus 的 `ElMessage` 提示错误。

## 第二步：重构状态管理 (Pinia)

修改 `src/store/user.ts`：

1. 引入刚才封装的 `request`。
2. 编写真实的 `login` Action：
   - 注意：FastAPI 的 `OAuth2PasswordRequestForm` 要求登录接口必须是 `application/x-www-form-urlencoded` 格式，请用这种格式向 `/api/auth/login` 发送 `username` 和 `password`。
   - 登录成功后，将返回的 `access_token` 和用户信息 (`role`, `full_name` 等) 保存到 state 和 `localStorage`。
3. 编写 `logout` Action：清空 state 和缓存，跳转 `/login`。

## 第三步：对接登录与注册页面

修改 `src/views/login/Index.vue`：

1. **注册逻辑对接**：前端点击注册时，向 `POST /api/auth/register` 发送 JSON 数据。如果角色是医生，必须带上 `employee_id` 和 `department`。注册成功后 `ElMessage.success` 提示，并切换回登录 Tab。
2. **登录逻辑对接**：调用 Pinia 的真实 `login` Action，成功后通过 Vue Router 动态跳转到该角色的首页（医生去 `/doctor/dashboard`，患者去 `/patient/chatbot`）。

## 第四步：完善患者预约挂号页面

修改 `src/views/patient/Appointment.vue`：

1. 编写一个 Element Plus 表单，包含：科室选择 (department)、预约时间 (appointment_time，使用 el-date-picker)、症状描述 (symptoms_desc，文本域)。
2. 提交表单时，调用 `POST /api/appointments/`。提交成功后提示用户，并清空表单。

## 第五步：完善医生今日候诊页面

修改 `src/views/doctor/Dashboard.vue`：

1. 在 `onMounted` 钩子中调用 `GET /api/appointments/today` 获取今日挂号列表。
2. 使用 `el-table` 展示数据（包含患者姓名、科室、预约时间、症状描述）。
3. **核心联动**：在表格右侧加一个“操作”列，放一个“开始 AI 会诊”的按钮。点击该按钮时，通过 Vue Router 跳转到 `/doctor/workspace`，**并想办法将该患者的姓名、症状描述通过路由参数或 Pinia 传递过去**，以便在 AI 工作台中直接带入患者信息！

# 约束条件

- 前端所有网络请求必须使用封装好的 `src/utils/request.ts`。
- 请妥善处理所有 API 调用的 try-catch 异常，并用 ElMessage 优雅报错。
- 请直接生成并覆盖相应文件。