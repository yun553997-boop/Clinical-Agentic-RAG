<script setup lang="ts">
import { reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import request from '@/utils/request'
import { getDoctors, type Doctor } from '@/utils/doctor'
import weixinQr from '@/assets/weixin.jpg'
import zhifubaoQr from '@/assets/zhifubao.jpg'

const form = reactive({
  department: '',
  doctor_id: null as number | null,
  appointment_time: '',
  symptoms_desc: '',
})

const loading = ref(false)
const doctorsList = ref<Doctor[]>([])
const loadingDoctors = ref(false)

const departments = [
  '消化内科',
  '心内科',
  '内科',
  '外科',
  '儿科',
  '妇产科',
  '急诊科',
  '骨科',
  '眼科',
  '皮肤科',
]

// ── 支付方式选择 ──
const paymentMethod = ref<'wechat' | 'alipay'>('wechat')

watch(
  () => form.department,
  async (dept) => {
    form.doctor_id = null
    if (!dept) {
      doctorsList.value = []
      return
    }
    loadingDoctors.value = true
    try {
      const res = await getDoctors(dept)
      doctorsList.value = res.data
    } catch {
      doctorsList.value = []
    } finally {
      loadingDoctors.value = false
    }
  },
)

// ── 支付对话框 ──
const paymentVisible = ref(false)
const pendingAppointmentId = ref<number | null>(null)
const paying = ref(false)

async function submitAppointment() {
  if (!form.department) {
    ElMessage.warning('请选择科室')
    return
  }
  if (form.doctor_id === null) {
    ElMessage.warning('请选择医生')
    return
  }
  if (!form.appointment_time) {
    ElMessage.warning('请选择预约时间')
    return
  }

  loading.value = true
  try {
    const res = await request.post('/api/appointments/', {
      doctor_id: form.doctor_id,
      department: form.department,
      appointment_time: new Date(form.appointment_time).toISOString(),
      symptoms_desc: form.symptoms_desc || null,
    })
    pendingAppointmentId.value = res.data.id
    paymentVisible.value = true
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : '未知错误'
    ElMessage.error(`预约提交失败：${msg}`)
  } finally {
    loading.value = false
  }
}

async function confirmPayment() {
  paying.value = true
  try {
    await request.post(`/api/payments/${pendingAppointmentId.value}/pay?method=${paymentMethod.value}`)
    ElMessage.success('支付成功，挂号完成！')
    paymentVisible.value = false
    form.department = ''
    form.doctor_id = null
    form.appointment_time = ''
    form.symptoms_desc = ''
    pendingAppointmentId.value = null
  } catch {
    ElMessage.error('支付失败，请重试')
  } finally {
    paying.value = false
  }
}

function closePayment() {
  paymentVisible.value = false
  pendingAppointmentId.value = null
}
</script>

<template>
  <div class="p-6">
    <h1 class="text-xl font-bold text-slate-800 mb-4">预约挂号</h1>

    <el-card shadow="hover" class="max-w-lg">
      <el-form
        :model="form"
        label-position="top"
        @submit.prevent="submitAppointment"
      >
        <el-form-item label="选择科室" required>
          <el-select
            v-model="form.department"
            placeholder="请选择就诊科室"
            :disabled="loading"
            class="w-full"
            clearable
          >
            <el-option
              v-for="dept in departments"
              :key="dept"
              :label="dept"
              :value="dept"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="选择医生" required>
          <el-select
            v-model="form.doctor_id"
            placeholder="请选择医生"
            :disabled="loading || !form.department"
            :loading="loadingDoctors"
            class="w-full"
            clearable
          >
            <el-option
              v-for="doc in doctorsList"
              :key="doc.id"
              :label="`${doc.full_name}（${doc.department}）`"
              :value="doc.id"
            />
          </el-select>
          <p
            v-if="form.department && !loadingDoctors && doctorsList.length === 0"
            class="text-sm text-gray-400 mt-1"
          >
            暂无医生排班
          </p>
        </el-form-item>

        <el-form-item label="预约时间" required>
          <el-date-picker
            v-model="form.appointment_time"
            type="datetime"
            placeholder="请选择预约时间"
            :disabled="loading"
            class="w-full"
            :shortcuts="[
              { text: '今天', value: new Date() },
              { text: '明天', value: (() => { const d = new Date(); d.setDate(d.getDate() + 1); return d })() },
            ]"
          />
        </el-form-item>

        <el-form-item label="症状描述">
          <el-input
            v-model="form.symptoms_desc"
            type="textarea"
            :rows="4"
            placeholder="请简要描述您的症状（选填）"
            :disabled="loading"
          />
        </el-form-item>

        <!-- 支付方式选择 -->
        <div class="bg-blue-50 rounded-lg p-3 mb-4">
          <div class="text-sm text-blue-700 mb-2">
            <span class="font-semibold">挂号费：¥50.00</span>
          </div>
          <div class="flex gap-3">
            <label
              class="flex items-center gap-2 px-4 py-2 rounded-lg border-2 cursor-pointer transition-all"
              :class="paymentMethod === 'wechat'
                ? 'border-green-500 bg-green-50 text-green-700'
                : 'border-gray-200 bg-white text-gray-500 hover:border-green-300'"
            >
              <input
                v-model="paymentMethod"
                type="radio"
                value="wechat"
                class="sr-only"
                :disabled="loading"
              />
              <span class="text-lg">💚</span>
              <span class="font-semibold text-sm">微信支付</span>
            </label>
            <label
              class="flex items-center gap-2 px-4 py-2 rounded-lg border-2 cursor-pointer transition-all"
              :class="paymentMethod === 'alipay'
                ? 'border-blue-500 bg-blue-50 text-blue-700'
                : 'border-gray-200 bg-white text-gray-500 hover:border-blue-300'"
            >
              <input
                v-model="paymentMethod"
                type="radio"
                value="alipay"
                class="sr-only"
                :disabled="loading"
              />
              <span class="text-lg">💙</span>
              <span class="font-semibold text-sm">支付宝</span>
            </label>
          </div>
        </div>

        <el-button
          type="primary"
          size="large"
          class="w-full"
          :loading="loading"
          @click="submitAppointment"
        >
          提交预约
        </el-button>
      </el-form>
    </el-card>

    <!-- 收款码弹窗 -->
    <el-dialog
      v-model="paymentVisible"
      title="扫码支付"
      width="380px"
      :close-on-click-modal="false"
      :show-close="!paying"
      @close="closePayment"
    >
      <div class="text-center py-2">
        <div class="text-lg font-bold text-slate-800 mb-1">
          应缴金额：<span class="text-red-500">¥50.00</span>
        </div>
        <p class="text-sm text-slate-500 mb-4">
          {{ paymentMethod === 'wechat' ? '微信' : '支付宝' }}扫码支付
        </p>

        <!-- 收款码图片 -->
        <div class="w-52 h-52 mx-auto mb-4 border rounded-lg overflow-hidden bg-white">
          <img
            v-if="paymentMethod === 'wechat'"
            :src="weixinQr"
            alt="微信收款码"
            class="w-full h-full object-contain"
          />
          <img
            v-else
            :src="zhifubaoQr"
            alt="支付宝收款码"
            class="w-full h-full object-contain"
          />
        </div>

        <p class="text-xs text-slate-400 mb-4">
          请使用{{ paymentMethod === 'wechat' ? '微信' : '支付宝' }}扫描上方二维码完成支付
        </p>

        <el-button
          type="success"
          size="large"
          class="w-full"
          :loading="paying"
          @click="confirmPayment"
        >
          {{ paying ? '处理中…' : '✅ 我已支付' }}
        </el-button>

        <p class="text-xs text-slate-400 mt-3">
          * 本系统为模拟支付，点击按钮即视为已完成支付
        </p>
      </div>
    </el-dialog>
  </div>
</template>
