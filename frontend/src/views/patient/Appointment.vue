<script setup lang="ts">
import { reactive, ref, watch, computed } from 'vue'
import { ElMessage } from 'element-plus'
import request from '@/utils/request'
import { getDoctors, type Doctor } from '@/utils/doctor'
import DoctorInfoCard from '@/components/DoctorInfoCard.vue'
import weixinQr from '@/assets/weixin.jpg'
import zhifubaoQr from '@/assets/zhifubao.jpg'

interface SlotItem {
  id: number
  doctor_id: number
  slot_date: string
  slot_time: string
}

const form = reactive({
  department: '',
  doctor_id: null as number | null,
  slot_id: null as number | null,
  symptoms_desc: '',
})

const loading = ref(false)
const doctorsList = ref<Doctor[]>([])
const loadingDoctors = ref(false)
const slots = ref<SlotItem[]>([])
const loadingSlots = ref(false)

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

// ── 当前选中的医生 ──
const selectedDoctor = computed(() => {
  if (form.doctor_id === null) return null
  return doctorsList.value.find((d) => d.id === form.doctor_id) ?? null
})

watch(
  () => form.department,
  async (dept) => {
    form.doctor_id = null
    form.slot_id = null
    slots.value = []
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

watch(
  () => form.doctor_id,
  async (docId) => {
    form.slot_id = null
    slots.value = []
    if (docId === null) return
    loadingSlots.value = true
    try {
      const res = await request.get<SlotItem[]>('/api/schedules/available', {
        params: { doctor_id: docId },
      })
      slots.value = res.data
    } catch {
      slots.value = []
    } finally {
      loadingSlots.value = false
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
  if (form.slot_id === null) {
    ElMessage.warning('请选择预约时间')
    return
  }

  loading.value = true
  try {
    const res = await request.post('/api/appointments/', {
      doctor_id: form.doctor_id,
      department: form.department,
      slot_id: form.slot_id,
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
    form.slot_id = null
    form.symptoms_desc = ''
    slots.value = []
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

    <div class="flex gap-6 items-start">
      <!-- 左侧：预约表单 -->
      <el-card shadow="hover" class="max-w-lg flex-shrink-0">
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
            <div v-if="form.doctor_id === null" class="text-sm text-gray-400">
              请先选择医生
            </div>
            <div v-else-if="loadingSlots" class="text-sm text-gray-400">
              加载可用时段中...
            </div>
            <div v-else-if="slots.length === 0" class="text-sm text-amber-600">
              该医生暂无可用排班时段
            </div>
            <el-radio-group
              v-else
              v-model="form.slot_id"
              :disabled="loading"
              class="w-full"
            >
              <div
                v-for="s in slots"
                :key="s.id"
                class="mb-2"
              >
                <el-radio :value="s.id" class="w-full">
                  <span class="font-mono text-sm">
                    {{ s.slot_date }} {{ s.slot_time }}
                  </span>
                </el-radio>
              </div>
            </el-radio-group>
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

      <!-- 右侧：医生信息卡片 -->
      <div class="flex-1 min-w-0">
        <DoctorInfoCard v-if="selectedDoctor" :doctor="selectedDoctor" />
        <div
          v-else
          class="flex items-center justify-center h-64 text-gray-400 border-2 border-dashed border-gray-200 rounded-lg"
        >
          <div class="text-center">
            <div class="text-4xl mb-2">👨‍⚕️</div>
            <p>请先选择科室和医生</p>
            <p class="text-xs mt-1">选择后将在此处显示医生信息</p>
          </div>
        </div>
      </div>
    </div>

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
