<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import request from '@/utils/request'

interface Appointment {
  id: number
  patient_id: number
  doctor_id: number
  patient_name: string
  department: string
  appointment_time: string
  status: string
  symptoms_desc: string | null
}

const router = useRouter()
const appointments = ref<Appointment[]>([])
const loading = ref(false)

async function fetchTodayAppointments() {
  loading.value = true
  try {
    const response = await request.get('/api/appointments/today')
    appointments.value = response.data
  } catch {
    // 错误已在拦截器中统一提示
  } finally {
    loading.value = false
  }
}

function startAIConsultation(appointment: Appointment) {
  router.push({
    path: '/doctor/workspace',
    query: {
      appointment_id: String(appointment.id),
      patient_name: appointment.patient_name,
      symptoms: appointment.symptoms_desc || '',
    },
  })
}

function formatTime(iso: string): string {
  const d = new Date(iso)
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

onMounted(() => {
  fetchTodayAppointments()
})
</script>

<template>
  <div class="p-6">
    <h1 class="text-xl font-bold text-slate-800 mb-4">今日候诊列表</h1>

    <el-card shadow="hover">
      <el-table
        :data="appointments"
        v-loading="loading"
        stripe
        empty-text="暂无候诊患者"
        style="width: 100%"
      >
        <el-table-column prop="patient_name" label="患者姓名" width="120" />
        <el-table-column prop="department" label="科室" width="120" />
        <el-table-column label="预约时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.appointment_time) }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === '待就诊' ? 'warning' : 'success'" size="small">
              {{ row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="symptoms_desc" label="症状描述" min-width="200">
          <template #default="{ row }">
            {{ row.symptoms_desc || '未填写' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="140" fixed="right">
          <template #default="{ row }">
            <el-button
              type="primary"
              size="small"
              @click="startAIConsultation(row)"
            >
              开始 AI 会诊
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>
