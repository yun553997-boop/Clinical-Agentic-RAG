<script setup lang="ts">
import { reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import request from '@/utils/request'
import { getDoctors, type Doctor } from '@/utils/doctor'

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
    await request.post('/api/appointments/', {
      doctor_id: form.doctor_id,
      department: form.department,
      appointment_time: new Date(form.appointment_time).toISOString(),
      symptoms_desc: form.symptoms_desc || null,
    })
    ElMessage.success('预约成功')
    form.department = ''
    form.doctor_id = null
    form.appointment_time = ''
    form.symptoms_desc = ''
  } finally {
    loading.value = false
  }
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
  </div>
</template>
