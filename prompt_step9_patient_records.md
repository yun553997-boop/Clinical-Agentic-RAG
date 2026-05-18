# 当前环境背景

患者目前可以通过 `/patient/appointment` 成功预约挂号（科室级联选择医生已完成），但前端缺少一个查看“我的预约记录”的页面。

# 任务目标：实现患者端“我的预约记录”功能

请帮我修改前后端代码，在患者侧边栏新增一个菜单，并实现历史预约记录的表格展示。

## 第一步：后端新增“获取我的预约记录”接口

请修改 `backend/api/endpoints/appointment.py`，新增一个接口：

- **路由**：`GET /api/appointments/my`
- **依赖**：注入 `current_user: User = Depends(get_current_user)` 以确保只有登录患者可访问。
- **逻辑**：使用 `AsyncSession` 查询 `Appointment` 表，条件为 `patient_id == current_user.id`。按预约时间 (`appointment_time`) 倒序排列。
- **关键点 (JOIN 查询)**：由于前端需要展示“预约的医生姓名”，请在 SQLAlchemy 查询时关联 `User` 表（代表医生），将医生的 `full_name` 一并返回。
- **返回格式**：返回一个列表，结构大致为 `[{"id": 1, "department": "消化内科", "doctor_name": "张医生", "appointment_time": "2026-05-20T10:00:00", "status": "待就诊", "symptoms_desc": "..."}]`。

## 第二步：前端路由与侧边栏改造

1. **修改路由表**：打开 `src/router/index.ts`，在 `path: '/patient'` 的 `children` 数组中，新增一个路由：
   - `path: 'records'`
   - `name: 'PatientRecords'`
   - `component: () => import('@/views/patient/Records.vue')`
2. **修改侧边栏**：打开 `src/layout/MainLayout.vue`，在患者 (`role === 'patient'`) 的 `el-menu` 渲染逻辑中，在“预约挂号”下方新增一项：
   - `<el-menu-item index="/patient/records">我的预约记录</el-menu-item>`

## 第三步：开发“我的预约记录”前端页面

新建文件 `src/views/patient/Records.vue`：

1. **网络请求**：在 `onMounted` 生命周期中，使用我们封装好的 `request.get('/api/appointments/my')` 拉取数据，存入 `records` 响应式数组中。
2. **UI 布局**：
   - 顶部加一个标题：“我的预约记录”。
   - 使用 `<el-table>` 展示 `records` 数组。
   - 包含的列：预约时间 (格式化为 YYYY-MM-DD HH:mm)、预约科室、主治医生 (`doctor_name`)、症状描述、状态 (`status`)。
   - **细节优化**：对“状态”列使用 `<el-tag>` 渲染。例如，“待就诊”使用 `type="warning"` 或 `type="primary"`。
3. 如果 `records` 为空，使用 `<el-empty description="暂无预约记录" />` 进行缺省展示。

# 约束条件

- 保证前后端代码无缝衔接。
- 前端时间格式化可以使用简单的纯 JS 函数处理（如 `new Date(dateStr).toLocaleString()`）。
- 请直接生成并覆盖/写入相应文件。