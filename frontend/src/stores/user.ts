import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import request from '@/utils/request'

export const useUserStore = defineStore('user', () => {
  const token = ref<string>(localStorage.getItem('token') || '')
  const role = ref<'doctor' | 'patient' | null>(
    (localStorage.getItem('role') as 'doctor' | 'patient') || null,
  )
  const fullName = ref<string>(localStorage.getItem('fullName') || '')
  const username = ref<string>(localStorage.getItem('username') || '')

  const isLoggedIn = computed(() => !!token.value)
  const isDoctor = computed(() => role.value === 'doctor')
  const isPatient = computed(() => role.value === 'patient')

  async function login(account: string, password: string): Promise<void> {
    const formData = new URLSearchParams()
    formData.append('username', account)
    formData.append('password', password)

    const response = await request.post('/api/auth/login', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    })

    const { access_token, user } = response.data

    token.value = access_token
    role.value = user.role as 'doctor' | 'patient'
    fullName.value = user.full_name
    username.value = user.username

    localStorage.setItem('token', access_token)
    localStorage.setItem('role', user.role)
    localStorage.setItem('fullName', user.full_name)
    localStorage.setItem('username', user.username)
  }

  function logout() {
    token.value = ''
    role.value = null
    fullName.value = ''
    username.value = ''
    localStorage.removeItem('token')
    localStorage.removeItem('role')
    localStorage.removeItem('fullName')
    localStorage.removeItem('username')
  }

  return { token, role, fullName, username, isLoggedIn, isDoctor, isPatient, login, logout }
})
