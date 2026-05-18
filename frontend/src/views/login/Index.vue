<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()

const activeTab = ref<'doctor' | 'patient'>('patient')
const doctorForm = reactive({ account: 'admin', password: '' })
const patientForm = reactive({ account: 'user', password: '' })
const loading = ref(false)
const rememberMe = ref(false)

const currentForm = computed(() => (activeTab.value === 'doctor' ? doctorForm : patientForm))

async function handleLogin() {
  const form = currentForm.value
  if (!form.account.trim() || !form.password.trim()) {
    ElMessage.warning('请输入账号和密码')
    return
  }

  loading.value = true
  try {
    await userStore.login(form.account, form.password)
    if (userStore.isDoctor) {
      router.push('/doctor/workspace')
    } else if (userStore.isPatient) {
      router.push('/patient/chatbot')
    }
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : '未知错误'
    ElMessage.error(`登录失败：${msg}`)
  } finally {
    loading.value = false
  }
}

function handleTabChange() {
  doctorForm.password = ''
  patientForm.password = ''
}

function goRegister(role: 'doctor' | 'patient') {
  router.push({ path: '/register', query: { role } })
}
</script>

<template>
  <div class="h-screen flex items-center justify-center bg-gradient-to-br from-slate-100 via-blue-50 to-slate-200">
    <el-card class="w-[440px] shadow-xl">
      <template #header>
        <div class="text-center">
          <div
            class="w-12 h-12 rounded-lg bg-gradient-to-br from-blue-700 to-blue-500 flex items-center justify-center shadow-md mx-auto mb-2"
          >
            <span class="text-white text-xl font-bold">+</span>
          </div>
          <h2 class="text-lg font-bold text-slate-800">智能临床诊疗系统</h2>
          <p class="text-xs text-slate-400 mt-1">选择登录身份</p>
        </div>
      </template>

      <!-- 登录选项卡 -->
      <div class="flex mb-5">
        <div
          class="flex-1 text-center py-3 cursor-pointer text-base font-bold transition-colors select-none"
          :class="activeTab === 'patient'
            ? 'tab-active'
            : 'text-slate-400 hover:text-slate-600'"
          @click="activeTab = 'patient'; handleTabChange()"
        >
          🙋 用户登录
        </div>
        <div
          class="flex-1 text-center py-3 cursor-pointer text-base font-bold transition-colors select-none"
          :class="activeTab === 'doctor'
            ? 'tab-active'
            : 'text-slate-400 hover:text-slate-600'"
          @click="activeTab = 'doctor'; handleTabChange()"
        >
          👨‍⚕️ 医生登录
        </div>
      </div>

      <!-- 用户登录 -->
      <div v-show="activeTab === 'patient'">
        <el-form
          label-position="top"
          @submit.prevent="handleLogin"
        >
          <el-form-item label="账号">
            <el-input
              v-model="patientForm.account"
              placeholder="请输入用户账号"
              :disabled="loading"
              clearable
              class="pill-input"
            >
              <template #prefix>
                <el-icon><User /></el-icon>
              </template>
            </el-input>
          </el-form-item>

          <el-form-item label="密码">
            <el-input
              v-model="patientForm.password"
              type="password"
              placeholder="请输入密码"
              :disabled="loading"
              show-password
              class="pill-input"
              @keyup.enter="handleLogin"
            >
              <template #prefix>
                <el-icon><Lock /></el-icon>
              </template>
            </el-input>
          </el-form-item>

          <div class="flex items-center justify-between -mt-2 mb-2">
            <el-checkbox v-model="rememberMe" :disabled="loading" size="small">
              下次自动登录
            </el-checkbox>
            <el-button type="primary" link size="small">
              忘记密码？
            </el-button>
          </div>

          <el-button
            type="primary"
            size="large"
            class="w-full h-11 pill-btn"
            :loading="loading"
            @click="handleLogin"
          >
            用户登录
          </el-button>

          <div class="text-center mt-4">
            <el-button type="primary" link @click="goRegister('patient')">
              注册新用户
            </el-button>
          </div>
        </el-form>
      </div>

      <!-- 医生登录 -->
      <div v-show="activeTab === 'doctor'">
        <el-form
          label-position="top"
          @submit.prevent="handleLogin"
        >
          <el-form-item label="账号">
            <el-input
              v-model="doctorForm.account"
              placeholder="请输入医生工号"
              :disabled="loading"
              clearable
              class="pill-input"
            >
              <template #prefix>
                <el-icon><User /></el-icon>
              </template>
            </el-input>
          </el-form-item>

          <el-form-item label="密码">
            <el-input
              v-model="doctorForm.password"
              type="password"
              placeholder="请输入密码"
              :disabled="loading"
              show-password
              class="pill-input"
              @keyup.enter="handleLogin"
            >
              <template #prefix>
                <el-icon><Lock /></el-icon>
              </template>
            </el-input>
          </el-form-item>

          <div class="flex items-center justify-between -mt-2 mb-2">
            <el-checkbox v-model="rememberMe" :disabled="loading" size="small">
              下次自动登录
            </el-checkbox>
            <el-button type="primary" link size="small">
              忘记密码？
            </el-button>
          </div>

          <el-button
            type="primary"
            size="large"
            class="w-full h-11 pill-btn"
            :loading="loading"
            @click="handleLogin"
          >
            医生登录
          </el-button>

          <div class="text-center mt-4">
            <el-button type="primary" link @click="goRegister('doctor')">
              注册医生账号
            </el-button>
          </div>
        </el-form>
      </div>
    </el-card>
  </div>
</template>

<style scoped>
.pill-input :deep(.el-input__wrapper) {
  border-radius: 24px;
  padding-left: 12px;
}

.pill-btn {
  border-radius: 24px;
  font-size: 16px;
  letter-spacing: 4px;
}

.tab-active {
  color: var(--el-color-primary);
}
</style>
