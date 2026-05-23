<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'
import request from '@/utils/request'

const router = useRouter()
const userStore = useUserStore()

const activeTab = ref<'doctor' | 'patient'>('patient')
const doctorForm = reactive({ account: 'admin', password: '' })
const patientForm = reactive({ account: 'user', password: '' })
const loading = ref(false)
const rememberMe = ref(false)

const currentForm = computed(() => (activeTab.value === 'doctor' ? doctorForm : patientForm))

onMounted(() => {
  const remembered = localStorage.getItem('rememberedUsername')
  if (remembered) {
    patientForm.account = remembered
    doctorForm.account = remembered
    rememberMe.value = true
  }
})

async function handleLogin() {
  const form = currentForm.value
  if (!form.account.trim() || !form.password.trim()) {
    ElMessage.warning('请输入账号和密码')
    return
  }

  loading.value = true
  try {
    await userStore.login(form.account.trim(), form.password, rememberMe.value)
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

// ── 忘记密码流程 ──
const forgotVisible = ref(false)
const forgotStep = ref(1)
const forgotUsername = ref('')
const forgotQuestion = ref('')
const forgotAnswer = ref('')
const forgotResetToken = ref('')
const forgotNewPassword = ref('')
const forgotConfirmPassword = ref('')
const forgotLoading = ref(false)

function openForgotPassword() {
  forgotStep.value = 1
  forgotUsername.value = ''
  forgotQuestion.value = ''
  forgotAnswer.value = ''
  forgotResetToken.value = ''
  forgotNewPassword.value = ''
  forgotConfirmPassword.value = ''
  forgotVisible.value = true
}

async function handleForgotStep1() {
  if (!forgotUsername.value.trim()) {
    ElMessage.warning('请输入用户名')
    return
  }
  forgotLoading.value = true
  try {
    const res = await request.post('/api/auth/forgot-password/question', {
      username: forgotUsername.value.trim(),
    })
    forgotQuestion.value = res.data.security_question
    forgotStep.value = 2
  } catch {
    // 错误已在拦截器处理
  } finally {
    forgotLoading.value = false
  }
}

async function handleForgotStep2() {
  if (!forgotAnswer.value.trim()) {
    ElMessage.warning('请输入密保答案')
    return
  }
  forgotLoading.value = true
  try {
    const res = await request.post('/api/auth/forgot-password/verify', {
      username: forgotUsername.value.trim(),
      answer: forgotAnswer.value.trim(),
    })
    forgotResetToken.value = res.data.reset_token
    forgotStep.value = 3
  } catch {
    // 错误已在拦截器处理
  } finally {
    forgotLoading.value = false
  }
}

async function handleForgotStep3() {
  if (!forgotNewPassword.value.trim()) {
    ElMessage.warning('请输入新密码')
    return
  }
  if (forgotNewPassword.value !== forgotConfirmPassword.value) {
    ElMessage.warning('两次密码输入不一致')
    return
  }
  forgotLoading.value = true
  try {
    await request.post('/api/auth/forgot-password/reset', {
      reset_token: forgotResetToken.value,
      new_password: forgotNewPassword.value,
    })
    ElMessage.success('密码重置成功，请登录')
    forgotVisible.value = false
  } catch {
    // 错误已在拦截器处理
  } finally {
    forgotLoading.value = false
  }
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
            <el-button type="primary" link size="small" @click="openForgotPassword">
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
            <el-button type="primary" link size="small" @click="openForgotPassword">
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

    <!-- 忘记密码对话框 -->
    <el-dialog
      v-model="forgotVisible"
      title="找回密码"
      width="400px"
      :close-on-click-modal="false"
      :show-close="!forgotLoading"
      @close="forgotStep = 1"
    >
      <!-- 步骤1：输入用户名 -->
      <div v-if="forgotStep === 1">
        <p class="text-sm text-slate-600 mb-4">请输入您的账号，我们将通过密保问题验证您的身份。</p>
        <el-form label-position="top" @submit.prevent="handleForgotStep1">
          <el-form-item label="账号">
            <el-input
              v-model="forgotUsername"
              placeholder="请输入账号"
              :disabled="forgotLoading"
            />
          </el-form-item>
          <el-button
            type="primary"
            class="w-full"
            :loading="forgotLoading"
            @click="handleForgotStep1"
          >
            下一步
          </el-button>
        </el-form>
      </div>

      <!-- 步骤2：回答密保问题 -->
      <div v-if="forgotStep === 2">
        <div class="bg-blue-50 rounded-lg p-3 mb-4">
          <span class="text-sm font-semibold text-blue-800">密保问题：</span>
          <span class="text-sm text-blue-700">{{ forgotQuestion }}</span>
        </div>
        <el-form label-position="top" @submit.prevent="handleForgotStep2">
          <el-form-item label="密保答案">
            <el-input
              v-model="forgotAnswer"
              placeholder="请输入密保答案"
              :disabled="forgotLoading"
            />
          </el-form-item>
          <el-button
            type="primary"
            class="w-full"
            :loading="forgotLoading"
            @click="handleForgotStep2"
          >
            验证答案
          </el-button>
        </el-form>
      </div>

      <!-- 步骤3：重置密码 -->
      <div v-if="forgotStep === 3">
        <p class="text-sm text-green-600 mb-4">身份验证通过，请设置新密码。</p>
        <el-form label-position="top" @submit.prevent="handleForgotStep3">
          <el-form-item label="新密码">
            <el-input
              v-model="forgotNewPassword"
              type="password"
              placeholder="请输入新密码"
              :disabled="forgotLoading"
              show-password
            />
          </el-form-item>
          <el-form-item label="确认密码">
            <el-input
              v-model="forgotConfirmPassword"
              type="password"
              placeholder="请再次输入新密码"
              :disabled="forgotLoading"
              show-password
              @keyup.enter="handleForgotStep3"
            />
          </el-form-item>
          <el-button
            type="primary"
            class="w-full"
            :loading="forgotLoading"
            @click="handleForgotStep3"
          >
            重置密码
          </el-button>
        </el-form>
      </div>
    </el-dialog>
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
