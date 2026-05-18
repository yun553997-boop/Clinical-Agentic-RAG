<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import MarkdownIt from 'markdown-it'
import request from '@/utils/request'

const md = new MarkdownIt({
  breaks: true,
  linkify: true,
})

interface Record {
  id: number
  department: string
  doctor_name: string
  appointment_time: string
  status: string
  symptoms_desc: string | null
  ai_report: string | null
  doctor_advice: string | null
}

const records = ref<Record[]>([])
const loading = ref(false)
const reportVisible = ref(false)
const currentReport = ref<{ ai_report: string; doctor_advice: string | null } | null>(null)

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

function viewReport(row: Record) {
  currentReport.value = {
    ai_report: row.ai_report || '',
    doctor_advice: row.doctor_advice,
  }
  reportVisible.value = true
}

function renderMarkdown(text: string | null): string {
  if (!text) return ''
  return md.render(text)
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
              @click="viewReport(row)"
            >
              查看诊疗报告
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-else v-loading="loading" description="暂无预约记录" />
    </el-card>

    <!-- 诊疗报告对话框 -->
    <el-dialog
      v-model="reportVisible"
      title="📄 诊疗报告"
      width="680px"
      top="5vh"
      :close-on-click-modal="false"
    >
      <div v-if="currentReport" class="space-y-6">
        <!-- AI 报告 -->
        <div>
          <h3 class="text-base font-semibold text-medical-800 mb-3">
            🤖 AI 诊疗辅助报告
          </h3>
          <div
            class="markdown-body bg-slate-50 rounded-lg p-4 border"
            v-html="renderMarkdown(currentReport.ai_report)"
          ></div>
        </div>

        <!-- 医生医嘱 -->
        <div v-if="currentReport.doctor_advice">
          <h3 class="text-base font-semibold text-medical-800 mb-3">
            👨‍⚕️ 医生补充医嘱
          </h3>
          <div
            class="markdown-body bg-blue-50 rounded-lg p-4 border border-blue-200"
            v-html="renderMarkdown(currentReport.doctor_advice)"
          ></div>
        </div>
      </div>

      <template #footer>
        <el-button @click="reportVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>
