# 当前环境背景

我的前端是一个基于 Vue3 + Element Plus 的项目。目前所有的 UI 和大模型 SSE 流式对话逻辑都堆积在 `src/App.vue` 单页面中。

现在，我需要将这个单页应用重构为“包含多角色（医生、患者）权限控制的企业级单体 SPA”。

# 任务目标：引入 Vue Router 与 Pinia，搭建 RBAC 动态路由骨架

请在 `frontend` 目录下严格按照以下步骤帮我修改和创建代码：

## 第一步：依赖配置与基础设置

1. 确保安装 `vue-router@4` 和 `pinia`。
2. 修改 `src/main.ts`（或 `main.js`），引入并挂载 router 和 pinia。

## 第二步：状态管理 (Pinia)

创建 `src/store/user.ts`。

- 定义 `useUserStore`，包含状态：`token` (字符串), `role` (字符串，可能值为 'doctor', 'patient' 或 null), `userInfo` (对象)。
- 提供一个 mock 的 `login` 方法：接收账号密码，如果账号是 'admin' 则角色设为 'doctor'；如果是 'user' 则设为 'patient'。模拟保存 token 到 localStorage。
- 提供 `logout` 方法：清除状态和 localStorage。

## 第三步：安全迁移现有问诊页面

1. 创建目录 `src/views/doctor/`。
2. 将当前 `src/App.vue` 中的**全部业务代码**（包括左侧表单、右侧终端、SSE fetch 逻辑和相关样式）**完整地、原封不动地**移动到新建的 `src/views/doctor/AiWorkspace.vue` 文件中。确保不丢失任何核心逻辑。

## 第四步：创建 Layout 骨架与公共视图

1. 创建 `src/layout/MainLayout.vue`。这是系统登录后的主壳子。
   - 顶部导航栏 (Header)：包含系统 Logo 和右侧的用户头像/退出登录按钮。
   - 左侧边栏 (Aside)：使用 `el-menu`。核心逻辑：需要读取 Pinia 中的 `role` 状态。
     - 如果 `role === 'doctor'`，显示菜单项：“今日候诊”(路由 `/doctor/dashboard`) 和 “AI 辅助会诊”(路由 `/doctor/workspace`)。
     - 如果 `role === 'patient'`，显示菜单项：“AI 智能导诊”(路由 `/patient/chatbot`) 和 “预约挂号”(路由 `/patient/appointment`)。
   - 右侧主体区 (Main)：使用 `<router-view />` 渲染子路由内容。
2. 创建 `src/views/login/Index.vue`。实现一个简单的 Element Plus 居中登录卡片。包含账号、密码输入框和登录按钮。点击登录时调用 Pinia 的 mock login 方法，并跳转到对应角色的首页。
3. 创建三个极其简单的占位组件（只需包含一个标题证明路由通了即可）：
   - `src/views/doctor/Dashboard.vue` (医生：今日候诊列表)
   - `src/views/patient/Chatbot.vue` (患者：AI 智能导诊)
   - `src/views/patient/Appointment.vue` (患者：在线预约挂号)

## 第五步：路由配置与全局守卫

1. 创建 `src/router/index.ts`。
2. 配置静态路由：
   - `/login`: 渲染 `Login/Index.vue`。
   - `/`: 重定向到 `/login`。
3. 配置动态权限路由 (使用 MainLayout 作为父组件)：
   - `path: '/doctor'`, `meta: { roles: ['doctor'] }`，包含子路由 `dashboard` 和 `workspace` (指向刚才迁移的 AiWorkspace.vue)。
   - `path: '/patient'`, `meta: { roles: ['patient'] }`，包含子路由 `chatbot` 和 `appointment`。
4. 编写全局前置守卫 `router.beforeEach`：
   - 判断是否有 token。如果没有且去的不是 `/login`，强行重定向到 `/login`。
   - 如果有 token，判断前往的路由 `meta.roles` 是否包含当前用户的角色。如果不包含，给出无权限提示（可以使用 Element Plus 的 ElMessage）并拦截跳转。

## 第六步：重写 App.vue

将 `src/App.vue` 清空，只保留最简单的路由出口：

```
<template>
  <router-view />
</template>
```

# 约束条件

- **安全警告**：在执行第三步迁移时，绝对不能破坏原有的流式对话 fetch 逻辑和 markdown 渲染，这非常重要。
- 代码必须包含清晰的中文注释，特别是路由守卫和权限判断的部分。
- 请直接生成并覆盖文件。