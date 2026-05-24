import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import request from '@/utils/request'

export interface UserProfile {
  id: number
  username: string
  role: string
  full_name: string
  employee_id: string | null
  department: string | null
  title: string | null
  specialty: string | null
  bio: string | null
  phone: string | null
  email: string | null
  gender: string | null
  avatar_url: string | null
  security_question: string | null
}

export const useUserStore = defineStore('user', () => {
  const token = ref<string>(localStorage.getItem('token') || '')
  const role = ref<'doctor' | 'patient' | null>(
    (localStorage.getItem('role') as 'doctor' | 'patient') || null,
  )
  const fullName = ref<string>(localStorage.getItem('fullName') || '')
  const username = ref<string>(localStorage.getItem('username') || '')
  const userId = ref<number | null>(
    localStorage.getItem('userId') ? Number(localStorage.getItem('userId')) : null,
  )
  const avatarUrl = ref<string | null>(localStorage.getItem('avatarUrl') || null)
  const profile = ref<UserProfile | null>(null)
  const profileLoading = ref(false)

  const isLoggedIn = computed(() => !!token.value)
  const isDoctor = computed(() => role.value === 'doctor')
  const isPatient = computed(() => role.value === 'patient')

  async function login(account: string, password: string, rememberMe: boolean = false): Promise<void> {
    const formData = new URLSearchParams()
    formData.append('username', account)
    formData.append('password', password)

    const response = await request.post(`/api/auth/login?remember_me=${rememberMe}`, formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    })

    const { access_token, user } = response.data

    token.value = access_token
    role.value = user.role as 'doctor' | 'patient'
    fullName.value = user.full_name
    username.value = user.username
    userId.value = user.id
    avatarUrl.value = user.avatar_url ?? null

    localStorage.setItem('token', access_token)
    localStorage.setItem('role', user.role)
    localStorage.setItem('fullName', user.full_name)
    localStorage.setItem('username', user.username)
    localStorage.setItem('userId', String(user.id))
    if (user.avatar_url) {
      localStorage.setItem('avatarUrl', user.avatar_url)
    } else {
      localStorage.removeItem('avatarUrl')
    }

    if (rememberMe) {
      localStorage.setItem('rememberedUsername', account)
    } else {
      localStorage.removeItem('rememberedUsername')
    }
  }

  async function fetchProfile(): Promise<void> {
    profileLoading.value = true
    try {
      const res = await request.get<UserProfile>('/api/users/me')
      profile.value = res.data
      fullName.value = res.data.full_name
      avatarUrl.value = res.data.avatar_url
      localStorage.setItem('fullName', res.data.full_name)
      if (res.data.avatar_url) {
        localStorage.setItem('avatarUrl', res.data.avatar_url)
      } else {
        localStorage.removeItem('avatarUrl')
      }
    } finally {
      profileLoading.value = false
    }
  }

  async function updateProfile(update: Partial<UserProfile>): Promise<void> {
    const res = await request.put<UserProfile>('/api/users/me', update)
    profile.value = res.data
    fullName.value = res.data.full_name
    avatarUrl.value = res.data.avatar_url
    localStorage.setItem('fullName', res.data.full_name)
    if (res.data.avatar_url) {
      localStorage.setItem('avatarUrl', res.data.avatar_url)
    } else {
      localStorage.removeItem('avatarUrl')
    }
  }

  function logout() {
    token.value = ''
    role.value = null
    fullName.value = ''
    username.value = ''
    userId.value = null
    avatarUrl.value = null
    profile.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('role')
    localStorage.removeItem('fullName')
    localStorage.removeItem('username')
    localStorage.removeItem('userId')
    localStorage.removeItem('avatarUrl')
    // 保留 rememberedUsername 以便下次登录预填
  }

  return {
    token, role, fullName, username, userId, avatarUrl, profile, profileLoading,
    isLoggedIn, isDoctor, isPatient,
    login, logout, fetchProfile, updateProfile,
  }
})
