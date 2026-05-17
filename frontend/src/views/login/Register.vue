<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

// 从 URL query 获取初始角色，默认患者
const initialRole = (route.query.role as 'doctor' | 'patient') || 'patient'
const activeTab = ref<'doctor' | 'patient'>(initialRole)

const doctorForm = reactive({
  account: '',
  name: '',
  department: '',
  password: '',
  confirmPassword: '',
})
const patientForm = reactive({
  account: '',
  name: '',
  password: '',
  confirmPassword: '',
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

  if (!form.account.trim() || !form.password.trim()) {
    ElMessage.warning('请填写账号和密码')
    return
  }
  if (form.password !== form.confirmPassword) {
    ElMessage.warning('两次密码输入不一致')
    return
  }

  loading.value = true
  try {
    // Mock 注册：调用相同的 login 方法模拟账号创建
    await userStore.login(form.account, form.password)

    // 注册成功后跳回登录页
    userStore.logout()
    ElMessage.success('注册成功，请重新登录')
    router.push({ path: '/login', query: { role: activeTab.value } })
  } catch {
    ElMessage.error('注册失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

/** 返回登录页 */
function goLogin() {
  router.push('/login')
}
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-100 via-blue-50 to-slate-200 py-8">
    <el-card class="w-[480px] shadow-xl">
      <template #header>
        <div class="text-center">
          <div
            class="w-12 h-12 rounded-lg bg-gradient-to-br from-emerald-600 to-teal-500 flex items-center justify-center shadow-md mx-auto mb-2"
          >
            <span class="text-white text-xl font-bold">✦</span>
          </div>
          <h2 class="text-lg font-bold text-slate-800">创建新账户</h2>
          <p class="text-xs text-slate-400 mt-1">注册加入智能临床诊疗平台</p>
        </div>
      </template>

      <!-- 注册选项卡：对称布局 + 醒目字体 -->
      <div class="flex border-b border-slate-200 mb-5">
        <div
          class="flex-1 text-center py-3 cursor-pointer text-base font-bold transition-colors"
          :class="activeTab === 'patient'
            ? 'text-green-600 border-b-2 border-green-600 -mb-[1px]'
            : 'text-slate-400 hover:text-slate-600'"
          @click="activeTab = 'patient'; handleTabChange()"
        >
          🙋 用户注册
        </div>
        <div
          class="flex-1 text-center py-3 cursor-pointer text-base font-bold transition-colors"
          :class="activeTab === 'doctor'
            ? 'text-blue-700 border-b-2 border-blue-700 -mb-[1px]'
            : 'text-slate-400 hover:text-slate-600'"
          @click="activeTab = 'doctor'; handleTabChange()"
        >
          👨‍⚕️ 医生注册
        </div>
      </div>

      <!-- ═══════ 用户注册表单 ═══════ -->
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
            />
          </el-form-item>

          <el-form-item label="姓名">
            <el-input
              v-model="patientForm.name"
              placeholder="请输入真实姓名"
              :disabled="loading"
              clearable
            />
          </el-form-item>

          <el-form-item label="密码">
            <el-input
              v-model="patientForm.password"
              type="password"
              placeholder="请设置密码"
              :disabled="loading"
              show-password
            />
          </el-form-item>

          <el-form-item label="确认密码">
            <el-input
              v-model="patientForm.confirmPassword"
              type="password"
              placeholder="请再次输入密码"
              :disabled="loading"
              show-password
              @keyup.enter="handleRegister"
            />
          </el-form-item>

          <el-button
            type="success"
            size="large"
            class="w-full mt-2"
            :loading="loading"
            @click="handleRegister"
          >
            注册
          </el-button>
        </el-form>
      </div>

      <!-- ═══════ 医生注册表单 ═══════ -->
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
            />
          </el-form-item>

          <el-form-item label="姓名">
            <el-input
              v-model="doctorForm.name"
              placeholder="请输入真实姓名"
              :disabled="loading"
              clearable
            />
          </el-form-item>

          <el-form-item label="科室">
            <el-select
              v-model="doctorForm.department"
              placeholder="请选择所属科室"
              :disabled="loading"
              class="w-full"
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
            </el-select>
          </el-form-item>

          <el-form-item label="密码">
            <el-input
              v-model="doctorForm.password"
              type="password"
              placeholder="请设置密码"
              :disabled="loading"
              show-password
            />
          </el-form-item>

          <el-form-item label="确认密码">
            <el-input
              v-model="doctorForm.confirmPassword"
              type="password"
              placeholder="请再次输入密码"
              :disabled="loading"
              show-password
              @keyup.enter="handleRegister"
            />
          </el-form-item>

          <el-button
            type="primary"
            size="large"
            class="w-full mt-2"
            :loading="loading"
            @click="handleRegister"
          >
            注册
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
