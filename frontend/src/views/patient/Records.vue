<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import request from '@/utils/request'

interface Record {
  id: number
  department: string
  doctor_name: string
  appointment_time: string
  status: string
  symptoms_desc: string | null
  ai_report: string | null
  doctor_advice: string | null
  paid: boolean
  payment_method: string | null
}

interface PrescriptionData {
  id: number
  appointment_id: number
  diagnosis: string | null
  medications: {
    drug_name: string
    specification: string
    dosage: string
    usage_method: string
    frequency: string
    days: number
  }[]
  notes: string | null
  created_at: string
}

const records = ref<Record[]>([])
const loading = ref(false)
const prescriptionVisible = ref(false)
const currentPrescription = ref<PrescriptionData | null>(null)
const loadingPrescription = ref(false)

function formatTime(dateStr: string) {
  const d = new Date(dateStr)
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  const h = String(d.getHours()).padStart(2, '0')
  const min = String(d.getMinutes()).padStart(2, '0')
  return `${y}-${m}-${day} ${h}:${min}`
}

function statusType(status: string) {
  if (status === '待就诊') return 'warning'
  if (status === '已取消') return 'info'
  return 'success'
}

function payStatusText(row: Record) {
  if (row.paid) return '已支付'
  return '未支付'
}

function payStatusType(row: Record) {
  return row.paid ? 'success' : 'warning'
}

async function fetchRecords() {
  loading.value = true
  try {
    const res = await request.get<Record[]>('/api/appointments/my')
    records.value = res.data
  } finally {
    loading.value = false
  }
}

async function cancelAppointment(id: number) {
  try {
    await request.delete(`/api/appointments/${id}`)
    ElMessage.success('已成功取消预约')
    await fetchRecords()
  } catch {
    ElMessage.error('取消失败，请重试')
  }
}

async function viewPrescription(row: Record) {
  loadingPrescription.value = true
  currentPrescription.value = null
  try {
    const res = await request.get(`/api/prescriptions/by-appointment/${row.id}`)
    currentPrescription.value = res.data
  } catch {
    ElMessage.warning('暂无处方信息')
  }
  loadingPrescription.value = false
  prescriptionVisible.value = true
}

onMounted(() => {
  fetchRecords()
})
</script>

<template>
  <div class="p-6">
    <h1 class="text-xl font-bold text-slate-800 mb-4">我的预约记录</h1>

    <el-card shadow="hover">
      <el-table
        v-if="records.length > 0"
        :data="records"
        v-loading="loading"
        stripe
        class="w-full"
      >
        <el-table-column prop="appointment_time" label="预约时间" min-width="160">
          <template #default="{ row }">
            {{ formatTime(row.appointment_time) }}
          </template>
        </el-table-column>
        <el-table-column prop="department" label="预约科室" min-width="100" />
        <el-table-column prop="doctor_name" label="主治医生" min-width="100" />
        <el-table-column prop="symptoms_desc" label="症状描述" min-width="160">
          <template #default="{ row }">
            {{ row.symptoms_desc || '-' }}
          </template>
        </el-table-column>
        <el-table-column label="支付" min-width="100">
          <template #default="{ row }">
            <el-tag :type="payStatusType(row)">
              {{ payStatusText(row) }}
            </el-tag>
            <span v-if="row.payment_method" class="text-xs text-slate-400 ml-1">
              {{ row.payment_method === 'wechat' ? '微信' : '支付宝' }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" min-width="90">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)">
              {{ row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" min-width="140" fixed="right">
          <template #default="{ row }">
            <el-popconfirm
              v-if="row.status === '待就诊'"
              title="确认要取消本次挂号预约吗？"
              confirm-button-text="确认取消"
              cancel-button-text="再想想"
              @confirm="cancelAppointment(row.id)"
            >
              <template #reference>
                <el-button type="danger" link size="small">
                  取消预约
                </el-button>
              </template>
            </el-popconfirm>
            <el-button
              v-if="row.status === '已完成'"
              type="primary"
              size="small"
              @click="viewPrescription(row)"
            >
              查看处方筏
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-else v-loading="loading" description="暂无预约记录" />
    </el-card>

    <!-- 处方筏对话框 -->
    <el-dialog
      v-model="prescriptionVisible"
      title="📝 电子处方筏"
      width="700px"
      top="5vh"
      :close-on-click-modal="false"
    >
      <div v-if="currentPrescription" class="space-y-6">
        <div class="bg-green-50 rounded-lg p-4 border border-green-200">
          <div v-if="currentPrescription.diagnosis" class="mb-3">
            <span class="text-sm font-semibold text-slate-600">诊断：</span>
            <span class="text-sm text-slate-800">{{ currentPrescription.diagnosis }}</span>
          </div>

          <el-table
            :data="currentPrescription.medications"
            size="small"
            border
            class="mb-3"
          >
            <el-table-column prop="drug_name" label="药品名称" min-width="120" />
            <el-table-column prop="specification" label="规格" min-width="90" />
            <el-table-column prop="dosage" label="用量" min-width="70" />
            <el-table-column prop="usage_method" label="用法" min-width="80" />
            <el-table-column prop="frequency" label="频次" min-width="90" />
            <el-table-column prop="days" label="天数" min-width="60">
              <template #default="{ row }">
                {{ row.days }}天
              </template>
            </el-table-column>
          </el-table>

          <div v-if="currentPrescription.notes">
            <span class="text-sm font-semibold text-slate-600">医嘱：</span>
            <span class="text-sm text-slate-800">{{ currentPrescription.notes }}</span>
          </div>
        </div>
      </div>

      <div
        v-else-if="loadingPrescription"
        class="text-center text-slate-400 text-sm py-4"
      >
        加载处方中...
      </div>

      <div v-else class="text-center text-slate-400 text-sm py-4">
        暂无处方信息
      </div>

      <template #footer>
        <el-button @click="prescriptionVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>
