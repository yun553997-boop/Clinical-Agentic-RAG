import { createRouter, createWebHistory } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    // ── 静态路由 ──
    {
      path: '/login',
      name: 'Login',
      component: () => import('@/views/login/Index.vue'),
      meta: { title: '登录' },
    },
    {
      path: '/register',
      name: 'Register',
      component: () => import('@/views/login/Register.vue'),
      meta: { title: '注册' },
    },
    {
      path: '/',
      redirect: '/login',
    },

    // ── 医生端路由（需医生角色）──
    {
      path: '/doctor',
      component: () => import('@/layout/MainLayout.vue'),
      meta: { roles: ['doctor'] },
      redirect: '/doctor/workspace',
      children: [
        {
          path: 'dashboard',
          name: 'DoctorDashboard',
          component: () => import('@/views/doctor/Dashboard.vue'),
          meta: { title: '今日候诊' },
        },
        {
          path: 'workspace',
          name: 'DoctorWorkspace',
          component: () => import('@/views/doctor/AiWorkspace.vue'),
          meta: { title: 'AI 辅助会诊' },
        },
        {
          path: 'knowledge',
          name: 'DoctorKnowledge',
          component: () => import('@/views/doctor/KnowledgeBase.vue'),
          meta: { title: '指南知识库管理' },
        },
        {
          path: 'schedule',
          name: 'DoctorSchedule',
          component: () => import('@/views/doctor/Schedule.vue'),
          meta: { title: '出诊排班' },
        },
        {
          path: 'report',
          name: 'DoctorReport',
          component: () => import('@/views/doctor/AiReport.vue'),
          meta: { title: 'AI 诊断报告' },
        },
      ],
    },

    // ── 患者端路由（需患者角色）──
    {
      path: '/patient',
      component: () => import('@/layout/MainLayout.vue'),
      meta: { roles: ['patient'] },
      redirect: '/patient/chatbot',
      children: [
        {
          path: 'chatbot',
          name: 'PatientChatbot',
          component: () => import('@/views/patient/Chatbot.vue'),
          meta: { title: 'AI 智能导诊' },
        },
        {
          path: 'appointment',
          name: 'PatientAppointment',
          component: () => import('@/views/patient/Appointment.vue'),
          meta: { title: '预约挂号' },
        },
        {
          path: 'records',
          name: 'PatientRecords',
          component: () => import('@/views/patient/Records.vue'),
          meta: { title: '我的预约记录' },
        },
      ],
    },

    // ── 404 兜底 ──
    {
      path: '/:pathMatch(.*)*',
      redirect: '/login',
    },
  ],
})

// ══════════════════════════ 全局前置守卫 ══════════════════════════
router.beforeEach((to, from, next) => {
  const userStore = useUserStore()

  // 白名单：无需登录即可访问的页面
  const whiteList = ['/login', '/register']

  // 1. 无 token：只允许访问白名单页面，其余全部重定向到登录页
  if (!userStore.token) {
    if (whiteList.includes(to.path)) {
      next()
    } else {
      // 重定向到登录页，携带原始目标路径以便登录后跳回
      next({ path: '/login', query: { redirect: to.fullPath } })
    }
    return
  }

  // 2. 已登录但访问 /login 或 /register：直接跳转到对应角色首页
  if (to.path === '/login' || to.path === '/register') {
    if (userStore.isDoctor) {
      next('/doctor/workspace')
    } else if (userStore.isPatient) {
      next('/patient/chatbot')
    } else {
      next()
    }
    return
  }

  // 3. 权限校验：检查目标路由的 meta.roles 是否包含当前用户角色
  //    从 to.matched 中收集所有 meta.roles，取最严格的匹配
  const requiredRoles = to.meta.roles as string[] | undefined

  if (requiredRoles && !requiredRoles.includes(userStore.role!)) {
    ElMessage.error('无权限访问该页面')
    // 根据角色重定向到其首页，避免死循环
    if (userStore.isDoctor) {
      next('/doctor/workspace')
    } else if (userStore.isPatient) {
      next('/patient/chatbot')
    } else {
      next('/login')
    }
    return
  }

  // 4. 放行
  next()
})

export default router
