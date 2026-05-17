import { ref, computed } from 'vue'
import { defineStore } from 'pinia'

export const useUserStore = defineStore('user', () => {
  // ── 状态 ──
  const token = ref<string>(localStorage.getItem('token') || '')
  const role = ref<'doctor' | 'patient' | null>(null)
  const userInfo = ref<Record<string, unknown>>({})

  // ── 计算属性 ──
  const isLoggedIn = computed(() => !!token.value)
  const isDoctor = computed(() => role.value === 'doctor')
  const isPatient = computed(() => role.value === 'patient')

  // ── Mock 登录 ──
  async function login(account: string, password: string): Promise<void> {
    // 模拟网络延迟
    await new Promise((resolve) => setTimeout(resolve, 300))

    // 统一密码校验
    const VALID_PASSWORD = '111111'
    if (password !== VALID_PASSWORD) {
      throw new Error('密码错误')
    }

    // Mock 角色分配逻辑
    if (account === 'admin') {
      role.value = 'doctor'
      userInfo.value = { name: '张医生', department: '内科', title: '主任医师' }
    } else if (account === 'user') {
      role.value = 'patient'
      userInfo.value = { name: '患者李某', age: 45 }
    } else {
      throw new Error('账号不存在')
    }

    // 模拟 token 并持久化
    const mockToken = `mock_token_${account}_${Date.now()}`
    token.value = mockToken
    localStorage.setItem('token', mockToken)
    localStorage.setItem('role', role.value!)
  }

  // ── 登出 ──
  function logout() {
    token.value = ''
    role.value = null
    userInfo.value = {}
    localStorage.removeItem('token')
    localStorage.removeItem('role')
  }

  return { token, role, userInfo, isLoggedIn, isDoctor, isPatient, login, logout }
})
