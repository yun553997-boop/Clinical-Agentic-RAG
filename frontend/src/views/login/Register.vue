<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import request from '@/utils/request'

const route = useRoute()
const router = useRouter()

const initialRole = (route.query.role as 'doctor' | 'patient') || 'patient'
const activeTab = ref<'doctor' | 'patient'>(initialRole)

const doctorForm = reactive({
  account: '',
  name: '',
  department: '',
  password: '',
  confirmPassword: '',
  security_question: '',
  security_answer: '',
})
const patientForm = reactive({
  account: '',
  name: '',
  password: '',
  confirmPassword: '',
  security_question: '',
  security_answer: '',
})
const loading = ref(false)

const currentForm = computed(() => (activeTab.value === 'doctor' ? doctorForm : patientForm))

function handleTabChange() {
  doctorForm.password = ''
  doctorForm.confirmPassword = ''
  patientForm.password = ''
  patientForm.confirmPassword = ''
}

async function handleRegister() {
  const form = currentForm.value

  if (!form.account.trim() || !form.name.trim() || !form.password.trim()) {
    ElMessage.warning('请填写完整信息')
    return
  }
  if (form.password !== form.confirmPassword) {
    ElMessage.warning('两次密码输入不一致')
    return
  }
  if (activeTab.value === 'doctor' && !doctorForm.department) {
    ElMessage.warning('请选择所属科室')
    return
  }

  loading.value = true
  try {
    const payload: Record<string, string> = {
      username: form.account.trim(),
      password: form.password,
      full_name: form.name.trim(),
      role: activeTab.value,
    }

    if (activeTab.value === 'doctor') {
      payload.employee_id = form.account.trim()
      payload.department = doctorForm.department
    }

    // 密保字段（选填）
    if (form.security_question && form.security_answer) {
      payload.security_question = form.security_question
      payload.security_answer = form.security_answer
    }

    await request.post('/api/auth/register', payload)
    ElMessage.success('注册成功，请返回登录')
    router.push({ path: '/login', query: { role: activeTab.value } })
  } catch {
    // 错误已在拦截器中统一提示
  } finally {
    loading.value = false
  }
}

function goLogin() {
  router.push('/login')
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
          <h2 class="text-lg font-bold text-slate-800">创建新账户</h2>
          <p class="text-xs text-slate-400 mt-1">注册加入智能临床诊疗平台</p>
        </div>
      </template>

      <!-- 注册选项卡 -->
      <div class="flex mb-5">
        <div
          class="flex-1 text-center py-3 cursor-pointer text-base font-bold transition-colors select-none"
          :class="activeTab === 'patient'
            ? 'tab-active'
            : 'text-slate-400 hover:text-slate-600'"
          @click="activeTab = 'patient'; handleTabChange()"
        >
          🙋 用户注册
        </div>
        <div
          class="flex-1 text-center py-3 cursor-pointer text-base font-bold transition-colors select-none"
          :class="activeTab === 'doctor'
            ? 'tab-active'
            : 'text-slate-400 hover:text-slate-600'"
          @click="activeTab = 'doctor'; handleTabChange()"
        >
          👨‍⚕️ 医生注册
        </div>
      </div>

      <!-- 用户注册表单 -->
      <div v-show="activeTab === 'patient'">
        <el-form
          label-position="top"
          @submit.prevent="handleRegister"
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

          <el-form-item label="姓名">
            <el-input
              v-model="patientForm.name"
              placeholder="请输入真实姓名"
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
              placeholder="请设置密码"
              :disabled="loading"
              show-password
              class="pill-input"
            >
              <template #prefix>
                <el-icon><Lock /></el-icon>
              </template>
            </el-input>
          </el-form-item>

          <el-form-item label="确认密码">
            <el-input
              v-model="patientForm.confirmPassword"
              type="password"
              placeholder="请再次输入密码"
              :disabled="loading"
              show-password
              class="pill-input"
              @keyup.enter="handleRegister"
            >
              <template #prefix>
                <el-icon><Lock /></el-icon>
              </template>
            </el-input>
          </el-form-item>

          <!-- 安全设置（可选） -->
          <div class="bg-slate-50 rounded-lg p-3 mb-4">
            <p class="text-xs text-slate-500 mb-2">安全设置（可选，用于找回密码）</p>
            <el-form-item label="密保问题" class="mb-2">
              <el-select
                v-model="patientForm.security_question"
                placeholder="请选择密保问题"
                :disabled="loading"
                class="w-full"
                clearable
                filterable
                allow-create
              >
                <el-option label="您的出生城市是？" value="您的出生城市是？" />
                <el-option label="您的小学名称是？" value="您的小学名称是？" />
                <el-option label="您的母亲姓名是？" value="您的母亲姓名是？" />
                <el-option label="您最喜欢的颜色是？" value="您最喜欢的颜色是？" />
                <el-option label="您的宠物名字是？" value="您的宠物名字是？" />
              </el-select>
            </el-form-item>
            <el-form-item label="密保答案" class="mb-0">
              <el-input
                v-model="patientForm.security_answer"
                placeholder="请输入密保答案"
                :disabled="loading"
              />
            </el-form-item>
          </div>

          <el-button
            type="primary"
            size="large"
            class="w-full h-11 pill-btn"
            :loading="loading"
            @click="handleRegister"
          >
            用户注册
          </el-button>
        </el-form>
      </div>

      <!-- 医生注册表单 -->
      <div v-show="activeTab === 'doctor'">
        <el-form
          label-position="top"
          @submit.prevent="handleRegister"
        >
          <el-form-item label="工号">
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

          <el-form-item label="姓名">
            <el-input
              v-model="doctorForm.name"
              placeholder="请输入真实姓名"
              :disabled="loading"
              clearable
              class="pill-input"
            >
              <template #prefix>
                <el-icon><User /></el-icon>
              </template>
            </el-input>
          </el-form-item>

          <el-form-item label="科室">
            <el-select
              v-model="doctorForm.department"
              placeholder="请选择所属科室"
              :disabled="loading"
              class="w-full pill-input"
              clearable
            >
              <el-option label="内科" value="内科" />
              <el-option label="外科" value="外科" />
              <el-option label="儿科" value="儿科" />
              <el-option label="妇产科" value="妇产科" />
              <el-option label="急诊科" value="急诊科" />
              <el-option label="骨科" value="骨科" />
              <el-option label="眼科" value="眼科" />
              <el-option label="皮肤科" value="皮肤科" />
              <el-option label="消化内科" value="消化内科" />
              <el-option label="心内科" value="心内科" />
            </el-select>
          </el-form-item>

          <el-form-item label="密码">
            <el-input
              v-model="doctorForm.password"
              type="password"
              placeholder="请设置密码"
              :disabled="loading"
              show-password
              class="pill-input"
            >
              <template #prefix>
                <el-icon><Lock /></el-icon>
              </template>
            </el-input>
          </el-form-item>

          <el-form-item label="确认密码">
            <el-input
              v-model="doctorForm.confirmPassword"
              type="password"
              placeholder="请再次输入密码"
              :disabled="loading"
              show-password
              class="pill-input"
              @keyup.enter="handleRegister"
            >
              <template #prefix>
                <el-icon><Lock /></el-icon>
              </template>
            </el-input>
          </el-form-item>

          <!-- 安全设置（可选） -->
          <div class="bg-slate-50 rounded-lg p-3 mb-4">
            <p class="text-xs text-slate-500 mb-2">安全设置（可选，用于找回密码）</p>
            <el-form-item label="密保问题" class="mb-2">
              <el-select
                v-model="doctorForm.security_question"
                placeholder="请选择密保问题"
                :disabled="loading"
                class="w-full"
                clearable
                filterable
                allow-create
              >
                <el-option label="您的出生城市是？" value="您的出生城市是？" />
                <el-option label="您的小学名称是？" value="您的小学名称是？" />
                <el-option label="您的母亲姓名是？" value="您的母亲姓名是？" />
                <el-option label="您最喜欢的颜色是？" value="您最喜欢的颜色是？" />
                <el-option label="您的宠物名字是？" value="您的宠物名字是？" />
              </el-select>
            </el-form-item>
            <el-form-item label="密保答案" class="mb-0">
              <el-input
                v-model="doctorForm.security_answer"
                placeholder="请输入密保答案"
                :disabled="loading"
              />
            </el-form-item>
          </div>

          <el-button
            type="primary"
            size="large"
            class="w-full h-11 pill-btn"
            :loading="loading"
            @click="handleRegister"
          >
            医生注册
          </el-button>
        </el-form>
      </div>

      <!-- 底部：返回登录 -->
      <div class="text-center mt-4">
        <span class="text-sm text-slate-500">已有账号？</span>
        <el-button type="primary" link @click="goLogin">
          返回登录
        </el-button>
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
