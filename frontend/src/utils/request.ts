import axios from 'axios'
import { ElMessage } from 'element-plus'

const request = axios.create({
  timeout: 30000,
})

request.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

request.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('role')
      localStorage.removeItem('fullName')
      localStorage.removeItem('username')
      window.location.href = '/login'
      ElMessage.error('登录已过期，请重新登录')
    } else {
      const msg = error.response?.data?.detail || error.message || '网络错误'
      ElMessage.error(msg)
    }
    return Promise.reject(error)
  },
)

export default request
