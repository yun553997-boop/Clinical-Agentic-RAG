<script setup lang="ts">
import { ref, nextTick, watch, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import MarkdownIt from 'markdown-it'

const route = useRoute()

const md = new MarkdownIt({
  breaks: true,
  linkify: true,
})

// ── 患者信息（从 query 读取）──
const patientInfo = ref({
  name: (route.query.name as string) || '',
  age: (route.query.age as string) || '',
  history: (route.query.history as string) || '',
  symptoms: (route.query.symptoms as string) || '',
  appointmentId: (route.query.appointment_id as string) || '',
})

// ── UI 状态 ──
const loading = ref(false)
const toolLogs = ref<{ text: string; kind: string }[]>([])
const finalReport = ref('')
const renderedReport = ref('')
const activeCollapse = ref<string[]>(['logs'])
const terminalRef = ref<HTMLElement | null>(null)
const reportRef = ref<HTMLElement | null>(null)

// ── 终端自动滚动 ──
watch(
  () => toolLogs.value.length,
  async () => {
    await nextTick()
    if (terminalRef.value) {
      terminalRef.value.scrollTop = terminalRef.value.scrollHeight
    }
  },
)

// ── 报告自动滚动 ──
watch(finalReport, async () => {
  await nextTick()
  if (reportRef.value) {
    reportRef.value.scrollTop = reportRef.value.scrollHeight
  }
})

function buildQuery(): string {
  const parts: string[] = []
  if (patientInfo.value.name) parts.push(`患者姓名：${patientInfo.value.name}`)
  if (patientInfo.value.age) parts.push(`患者年龄：${patientInfo.value.age} 岁`)
  if (patientInfo.value.history) parts.push(`基础病史：${patientInfo.value.history}`)
  parts.push(`主诉 / 当前症状描述：${patientInfo.value.symptoms}`)
  parts.push('请基于以上患者信息，按照推荐工作流程进行分析并生成诊疗辅助报告。')
  return parts.join('\n')
}

function handleSSEEvent(event: { type: string; data?: string }) {
  switch (event.type) {
    case 'tool_log':
      toolLogs.value.push({ text: event.data || '', kind: 'log' })
      break
    case 'final_answer':
      finalReport.value += event.data || ''
      renderedReport.value = md.render(finalReport.value)
      break
    case 'done':
      break
  }
}

async function startConsultation() {
  loading.value = true
  toolLogs.value = []
  finalReport.value = ''
  renderedReport.value = ''

  toolLogs.value.push({
    text: '正在连接 AI 临床诊疗服务...\n',
    kind: 'system',
  })

  try {
    const response = await fetch('/api/chat/agent', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query: buildQuery() }),
    })

    if (!response.ok) {
      throw new Error(`服务器返回 HTTP ${response.status}`)
    }

    const reader = response.body!.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        const trimmed = line.trim()
        if (trimmed.startsWith('data: ')) {
          try {
            const event = JSON.parse(trimmed.slice(6))
            handleSSEEvent(event)
          } catch {
            // 忽略不完整的 JSON
          }
        }
      }
    }
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : String(err)
    ElMessage.error(`连接失败：${msg}`)
    toolLogs.value.push({
      text: `\n连接错误：${msg}`,
      kind: 'error',
    })
  } finally {
    loading.value = false
    // 报告生成完成后存入 localStorage，供工作区读取
    if (finalReport.value) {
      const key = `ai_report_${patientInfo.value.appointmentId || Date.now()}`
      localStorage.setItem(key, finalReport.value)
      localStorage.setItem('ai_report_latest', finalReport.value)
      // 通知 opener 窗口有新报告
      if (window.opener) {
        window.opener.postMessage({ type: 'ai_report_ready', key }, window.location.origin)
      }
      toolLogs.value.push({
        text: '\n报告已生成，数据已同步至工作区处方页面',
        kind: 'system',
      })
    }
  }
}

onMounted(() => {
  if (patientInfo.value.symptoms) {
    startConsultation()
  }
})
</script>

<template>
  <div class="h-screen flex flex-col bg-slate-100 overflow-hidden">
    <!-- 顶部：患者信息摘要 + 操作栏 -->
    <header class="flex-shrink-0 bg-white border-b border-slate-200 px-6 py-3">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-4">
          <div class="flex items-center gap-2 text-medical-800 font-semibold">
            <span class="text-xl">🧠</span>
            <span class="text-lg">AI 智能诊断报告</span>
            <el-tag
              v-if="loading"
              type="warning"
              size="small"
              effect="dark"
              round
            >
              生成中...
            </el-tag>
            <el-tag
              v-else-if="finalReport"
              type="success"
              size="small"
              effect="dark"
              round
            >
              报告就绪
            </el-tag>
          </div>
          <div class="flex items-center gap-3 text-sm text-slate-500">
            <span v-if="patientInfo.name">患者：{{ patientInfo.name }}</span>
            <span v-if="patientInfo.age">年龄：{{ patientInfo.age }} 岁</span>
            <span v-if="patientInfo.history">病史：{{ patientInfo.history }}</span>
          </div>
        </div>
        <el-button
          type="primary"
          size="default"
          :disabled="loading"
          @click="startConsultation"
        >
          {{ loading ? '分析中...' : '🔄 重新分析' }}
        </el-button>
      </div>
    </header>

    <!-- 主体：日志 + 报告 -->
    <main class="flex-1 flex flex-col p-5 gap-4 min-h-0 overflow-y-auto">
      <!-- Agent 执行日志（可折叠） -->
      <el-collapse v-model="activeCollapse">
        <el-collapse-item title="Agent 思考与工具调用过程" name="logs">
          <div
            ref="terminalRef"
            class="terminal-scroll bg-[#0d1117] text-green-400 font-mono text-sm p-4 overflow-y-auto whitespace-pre-wrap break-words leading-relaxed max-h-[320px]"
          >
            <div
              v-if="toolLogs.length === 0"
              class="text-slate-500 flex items-center justify-center h-full"
            >
              <div class="text-center">
                <div class="text-3xl mb-3">🖥️</div>
                <div>Agent 执行日志将在此实时显示</div>
              </div>
            </div>

            <template v-for="(log, i) in toolLogs" :key="i">
              <span
                v-if="log.kind === 'system'"
                class="text-cyan-400"
              >{{ log.text }}</span>
              <span
                v-else-if="log.kind === 'error'"
                class="text-red-400"
              >{{ log.text }}</span>
              <span
                v-else
              >{{ log.text }}</span>
            </template>

            <span
              v-if="loading"
              class="inline-block w-2 h-4 bg-green-400 animate-pulse align-middle ml-0.5"
            >&nbsp;</span>
          </div>
        </el-collapse-item>
      </el-collapse>

      <!-- 诊断报告 -->
      <el-card
        shadow="hover"
        :body-style="{ padding: 0, overflow: 'hidden' }"
        class="flex-1 flex flex-col min-h-0"
      >
        <div
          ref="reportRef"
          class="overflow-y-auto p-8 bg-white flex-1"
        >
          <!-- 空状态 -->
          <div
            v-if="!finalReport && !loading"
            class="text-slate-400 flex items-center justify-center h-full py-12"
          >
            <div class="text-center">
              <div class="text-4xl mb-4">📄</div>
              <div class="text-lg font-semibold">等待 AI 分析</div>
              <div class="text-sm mt-1">
                症状：{{ patientInfo.symptoms || '未填写' }}
              </div>
              <el-button
                v-if="!loading"
                type="primary"
                class="mt-4"
                @click="startConsultation"
              >
                🚀 开始 AI 会诊
              </el-button>
            </div>
          </div>

          <!-- 加载骨架 -->
          <div v-else-if="loading && !finalReport" class="space-y-4 animate-pulse">
            <div class="h-6 bg-slate-200 rounded w-1/3"></div>
            <div class="h-4 bg-slate-100 rounded w-full"></div>
            <div class="h-4 bg-slate-100 rounded w-4/5"></div>
            <div class="h-6 bg-slate-200 rounded w-1/2 mt-6"></div>
            <div class="h-4 bg-slate-100 rounded w-full"></div>
            <div class="h-4 bg-slate-100 rounded w-3/4"></div>
            <div class="h-6 bg-slate-200 rounded w-1/3 mt-6"></div>
            <div class="h-4 bg-slate-100 rounded w-full"></div>
            <div class="h-4 bg-slate-100 rounded w-5/6"></div>
          </div>

          <!-- Markdown 渲染 -->
          <div
            v-else
            class="markdown-body"
            v-html="renderedReport"
          ></div>
        </div>
      </el-card>

      <!-- 底部提示 -->
      <div
        v-if="finalReport"
        class="flex items-center justify-center gap-2 text-sm text-slate-500"
      >
        <span>💡</span>
        <span>报告数据已自动同步到处方工作区，可返回工作区继续开具处方</span>
      </div>
    </main>
  </div>
</template>
