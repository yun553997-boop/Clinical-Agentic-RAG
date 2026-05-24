<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import request from '@/utils/request'
import PrescriptionPad from '@/components/PrescriptionPad.vue'
import type { PrescriptionData, MedicationItem } from '@/components/PrescriptionPad.vue'

const route = useRoute()
const router = useRouter()

// ── appointment_id ──
const appointmentId = computed(() => {
  const id = route.query.appointment_id
  if (id) return Number(id)
  return null
})

// ── 患者信息表单 ──
const form = ref({
  name: '',
  age: undefined as number | undefined,
  history: '',
  symptoms: '',
})

onMounted(() => {
  if (route.query.patient_name) {
    form.value.name = route.query.patient_name as string
  }
  if (route.query.symptoms) {
    form.value.symptoms = route.query.symptoms as string
  }
  // 检查 localStorage 中是否有 AI 报告
  checkLocalReport()
})

// ── UI 状态 ──
const submitting = ref(false)
const hasAiReport = ref(false)
const aiReportContent = ref('')

// ── 处方数据 ──
const prescription = ref<PrescriptionData>({
  diagnosis: '',
  medications: [
    { drug_name: '', specification: '', dosage: '', usage_method: '口服', frequency: '每日1次', days: 7 },
  ],
  notes: '',
})
const prescriptionFilled = ref(false)

// ── 检查 localStorage 中的报告 ──
function checkLocalReport() {
  const report = localStorage.getItem('ai_report_latest')
  if (report) {
    aiReportContent.value = report
    hasAiReport.value = true
  }
}

// ── 跨窗口事件监听 ──
function handleStorageEvent(e: StorageEvent) {
  if (e.key === 'ai_report_latest' && e.newValue) {
    aiReportContent.value = e.newValue
    hasAiReport.value = true
    ElMessage.success('AI 诊断报告已生成，可一键填入处方')
  }
}

function handleMessageEvent(e: MessageEvent) {
  if (e.origin !== window.location.origin) return
  if (e.data?.type === 'ai_report_ready') {
    const report = localStorage.getItem('ai_report_latest')
    if (report) {
      aiReportContent.value = report
      hasAiReport.value = true
      ElMessage.success('AI 诊断报告已同步，可一键填入处方')
    }
  }
}

onMounted(() => {
  window.addEventListener('storage', handleStorageEvent)
  window.addEventListener('message', handleMessageEvent)
})

onUnmounted(() => {
  window.removeEventListener('storage', handleStorageEvent)
  window.removeEventListener('message', handleMessageEvent)
})

// ── 从 AI 报告解析处方数据 ──
function parsePrescriptionFromReport(): PrescriptionData | null {
  const text = aiReportContent.value
  if (!text) return null

  const jsonBlockRegex = /```json\s*([\s\S]*?)```/g
  let match: RegExpExecArray | null

  while ((match = jsonBlockRegex.exec(text)) !== null) {
    try {
      const parsed = JSON.parse(match[1])
      if (parsed.medications && Array.isArray(parsed.medications)) {
        const medications: MedicationItem[] = parsed.medications.map((m: Record<string, unknown>) => ({
          drug_name: String(m.drug_name || ''),
          specification: String(m.specification || ''),
          dosage: String(m.dosage || ''),
          usage_method: String(m.usage_method || '口服'),
          frequency: String(m.frequency || '每日1次'),
          days: Number(m.days) || 7,
        }))
        return {
          diagnosis: String(parsed.diagnosis || ''),
          medications,
          notes: String(parsed.notes || ''),
        }
      }
    } catch {
      continue
    }
  }

  const jsonObjRegex = /\{[\s\S]*"medications"[\s\S]*\}/g
  while ((match = jsonObjRegex.exec(text)) !== null) {
    try {
      const parsed = JSON.parse(match[0])
      if (parsed.medications && Array.isArray(parsed.medications)) {
        const medications: MedicationItem[] = parsed.medications.map((m: Record<string, unknown>) => ({
          drug_name: String(m.drug_name || ''),
          specification: String(m.specification || ''),
          dosage: String(m.dosage || ''),
          usage_method: String(m.usage_method || '口服'),
          frequency: String(m.frequency || '每日1次'),
          days: Number(m.days) || 7,
        }))
        return {
          diagnosis: String(parsed.diagnosis || ''),
          medications,
          notes: String(parsed.notes || ''),
        }
      }
    } catch {
      continue
    }
  }

  return null
}

// ── 一键填入处方 ──
function autoFillPrescription() {
  const data = parsePrescriptionFromReport()
  if (data && data.medications.length > 0) {
    prescription.value = data
    prescriptionFilled.value = true
    ElMessage.success(`已从 AI 报告提取 ${data.medications.length} 条用药建议`)
  } else {
    ElMessage.warning('AI 报告中未找到结构化用药数据，请手动填写处方')
  }
}

// ── 打开 AI 会诊新窗口 ──
function startConsultation() {
  if (!form.value.symptoms.trim()) {
    ElMessage.warning('请输入患者当前症状描述')
    return
  }

  const params = new URLSearchParams()
  if (form.value.name) params.set('name', form.value.name)
  if (form.value.age) params.set('age', String(form.value.age))
  if (form.value.history) params.set('history', form.value.history)
  params.set('symptoms', form.value.symptoms)
  if (appointmentId.value) params.set('appointment_id', String(appointmentId.value))

  const url = `/doctor/report?${params.toString()}`
  window.open(url, '_blank')
  ElMessage.success('AI 会诊报告已在新窗口中打开，完成后将自动同步处方数据')
}

// ── 提交处方并完成会诊 ──
async function submitPrescription() {
  const validMeds = prescription.value.medications.filter((m) => m.drug_name.trim())
  if (validMeds.length === 0) {
    ElMessage.warning('请至少填写一种药品')
    return
  }
  if (!appointmentId.value) {
    ElMessage.error('未关联挂号单 ID，请从今日候诊列表进入')
    return
  }
  if (!aiReportContent.value) {
    ElMessage.warning('请先通过 AI 会诊生成诊断报告')
    return
  }

  submitting.value = true
  try {
    await request.post(`/api/prescriptions/${appointmentId.value}`, {
      diagnosis: prescription.value.diagnosis,
      medications: validMeds,
      notes: prescription.value.notes || null,
    })

    await request.put(`/api/appointments/${appointmentId.value}/submit`, {
      ai_report: aiReportContent.value,
      doctor_advice: null,
    })

    ElMessage.success('处方已提交，报告已发送给患者')
    localStorage.removeItem('ai_report_latest')
    router.push('/doctor/dashboard')
  } catch {
    ElMessage.error('提交失败，请重试')
  } finally {
    submitting.value = false
  }
}

// ── 重置 ──
function resetForm() {
  form.value = { name: '', age: undefined, history: '', symptoms: '' }
  prescription.value = {
    diagnosis: '',
    medications: [{ drug_name: '', specification: '', dosage: '', usage_method: '口服', frequency: '每日1次', days: 7 }],
    notes: '',
  }
  prescriptionFilled.value = false
  hasAiReport.value = false
  aiReportContent.value = ''
  localStorage.removeItem('ai_report_latest')
}
</script>

<template>
  <div class="h-screen flex bg-slate-100 overflow-hidden">
    <!-- ══════════════════════════ 左侧：患者病历工作区 ══════════════════════════ -->
    <aside class="w-[420px] flex-shrink-0 flex flex-col p-5 gap-4">
      <!-- 标题栏 -->
      <div class="flex items-center gap-3 mb-1">
        <div
          class="w-10 h-10 rounded-lg bg-gradient-to-br from-blue-700 to-blue-500 flex items-center justify-center shadow-md"
        >
          <span class="text-white text-lg font-bold">+</span>
        </div>
        <div>
          <h1 class="text-lg font-bold text-medical-900 leading-tight">
            智能临床诊疗辅助系统
          </h1>
          <p class="text-xs text-slate-500">Agentic RAG Medical Assistant</p>
        </div>
      </div>

      <!-- 表单卡片 -->
      <el-card shadow="hover" class="flex-1 flex flex-col overflow-y-auto">
        <template #header>
          <div class="flex items-center gap-2 text-medical-800 font-semibold">
            <span class="text-lg">📋</span>
            <span>患者病历工作区</span>
          </div>
        </template>

        <el-form
          :model="form"
          label-position="top"
          class="h-full flex flex-col"
          @submit.prevent="startConsultation"
        >
          <el-form-item label="患者姓名">
            <el-input
              v-model="form.name"
              placeholder="请输入患者姓名（选填）"
              :disabled="submitting"
              clearable
            />
          </el-form-item>

          <el-form-item label="年龄">
            <el-input-number
              v-model="form.age"
              :min="0"
              :max="150"
              placeholder="岁"
              :disabled="submitting"
              controls-position="right"
              class="w-full"
            />
          </el-form-item>

          <el-form-item label="基础病史">
            <el-input
              v-model="form.history"
              type="textarea"
              :rows="3"
              placeholder="如：高血压病史 10 年、2 型糖尿病 5 年……"
              :disabled="submitting"
            />
          </el-form-item>

          <el-form-item label="当前症状描述" required>
            <el-input
              v-model="form.symptoms"
              type="textarea"
              :rows="5"
              placeholder="请详细描述患者当前主诉、症状、体征、检查结果等……
        示例：患者近一周出现头晕、视物模糊，自测血压 165/95 mmHg，空腹血糖 8.2 mmol/L……"
              :disabled="submitting"
            />
          </el-form-item>

          <div class="mt-auto pt-3 flex gap-3">
            <el-button
              type="primary"
              size="large"
              class="flex-1 h-11 font-semibold text-base"
              :disabled="!form.symptoms.trim()"
              @click="startConsultation"
            >
              🧠 请求 AI 会诊
            </el-button>
            <el-button
              size="large"
              class="h-11"
              :disabled="submitting"
              @click="resetForm"
            >
              重置
            </el-button>
          </div>
        </el-form>
      </el-card>

      <div
        class="text-xs text-slate-400 text-center leading-relaxed flex-shrink-0"
      >
        ⚠️ 本系统为 AI 辅助决策工具，最终诊疗方案需由执业医师确认
      </div>
    </aside>

    <!-- ══════════════════════════ 右侧：传统处方筏 ══════════════════════════ -->
    <main class="flex-1 flex flex-col p-5 pl-0 gap-4 min-w-0 overflow-y-auto">
      <!-- AI 报告状态指示 -->
      <div
        v-if="!hasAiReport"
        class="bg-blue-50 border border-blue-200 rounded-lg p-4 flex items-center gap-3"
      >
        <span class="text-2xl">ℹ️</span>
        <div class="flex-1">
          <div class="text-blue-800 font-semibold text-sm">尚未获取 AI 诊断报告</div>
          <div class="text-blue-600 text-xs mt-0.5">
            请在左侧填写患者信息后点击「请求 AI 会诊」，AI 报告将在新窗口中生成
          </div>
        </div>
      </div>
      <div
        v-else
        class="bg-green-50 border border-green-200 rounded-lg p-4 flex items-center gap-3"
      >
        <span class="text-2xl">✅</span>
        <div class="flex-1">
          <div class="text-green-800 font-semibold text-sm">AI 诊断报告已就绪</div>
          <div class="text-green-600 text-xs mt-0.5">可点击「从 AI 报告一键填入」自动填写处方</div>
        </div>
      </div>

      <!-- 处方筏 -->
      <PrescriptionPad
        v-model="prescription"
        :disabled="submitting"
        :patient-name="form.name"
        :patient-age="form.age"
        :prescription-filled="prescriptionFilled"
        :appointment-id="appointmentId"
        :has-ai-report="hasAiReport"
        :submitting="submitting"
        @auto-fill="autoFillPrescription"
      />

      <!-- 提交按钮 -->
      <div class="flex items-center justify-between bg-white rounded-lg p-4 shadow flex-shrink-0">
        <div
          v-if="!appointmentId"
          class="text-amber-600 text-sm flex items-center gap-2"
        >
          <span>⚠️</span>
          <span>未关联挂号单 ID，请从今日候诊列表进入</span>
        </div>
        <div v-else-if="!hasAiReport" class="text-sm text-slate-500">
          请先通过 AI 会诊生成诊断报告
        </div>
        <div v-else class="text-sm text-slate-500">
          确认处方信息无误后提交给患者
        </div>
        <el-button
          type="primary"
          size="large"
          :loading="submitting"
          :disabled="!appointmentId || !hasAiReport"
          @click="submitPrescription"
        >
          {{ submitting ? '提交中…' : '📋 提交处方给患者' }}
        </el-button>
      </div>
    </main>
  </div>
</template>
