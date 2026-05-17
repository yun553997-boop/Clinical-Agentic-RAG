<script setup lang="ts">
import { ref, nextTick, watch } from 'vue'
import { ElMessage } from 'element-plus'
import MarkdownIt from 'markdown-it'

const md = new MarkdownIt({
  breaks: true,
  linkify: true,
})

// ── 表单数据 ──
const form = ref({
  name: '',
  age: undefined as number | undefined,
  history: '',
  symptoms: '',
})

// ── UI 状态 ──
const loading = ref(false)
const toolLogs = ref<{ text: string; kind: string }[]>([])
const finalReport = ref('')
const renderedReport = ref('')
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
  }
)

// ── 报告自动滚动 ──
watch(finalReport, async () => {
  await nextTick()
  if (reportRef.value) {
    reportRef.value.scrollTop = reportRef.value.scrollHeight
  }
})

// ── 构建问诊 query ──
function buildQuery(): string {
  const parts: string[] = []
  if (form.value.name) parts.push(`患者姓名：${form.value.name}`)
  if (form.value.age) parts.push(`患者年龄：${form.value.age} 岁`)
  if (form.value.history) parts.push(`基础病史：${form.value.history}`)
  parts.push(`主诉 / 当前症状描述：${form.value.symptoms}`)
  parts.push('请基于以上患者信息，按照推荐工作流程进行分析并生成诊疗辅助报告。')
  return parts.join('\n')
}

// ── 处理 SSE 事件 ──
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

// ── 核心：SSE 流式请求 ──
async function startConsultation() {
  if (!form.value.symptoms.trim()) {
    ElMessage.warning('请输入患者当前症状描述')
    return
  }

  loading.value = true
  toolLogs.value = []
  finalReport.value = ''
  renderedReport.value = ''

  // 显示第一条日志
  toolLogs.value.push({
    text: '🚀 正在连接 AI 临床诊疗服务...\n',
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
      text: `\n❌ 连接错误：${msg}`,
      kind: 'error',
    })
  } finally {
    loading.value = false
  }
}

// ── 重置表单 ──
function resetForm() {
  form.value = { name: '', age: undefined, history: '', symptoms: '' }
  toolLogs.value = []
  finalReport.value = ''
  renderedReport.value = ''
}
</script>

<template>
  <div class="h-screen flex bg-slate-100 overflow-hidden">
    <!-- ══════════════════════════ 左侧：病历工作区 ══════════════════════════ -->
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
          <!-- 患者姓名 -->
          <el-form-item label="患者姓名">
            <el-input
              v-model="form.name"
              placeholder="请输入患者姓名（选填）"
              :disabled="loading"
              clearable
            />
          </el-form-item>

          <!-- 年龄 -->
          <el-form-item label="年龄">
            <el-input-number
              v-model="form.age"
              :min="0"
              :max="150"
              placeholder="岁"
              :disabled="loading"
              controls-position="right"
              class="w-full"
            />
          </el-form-item>

          <!-- 基础病史 -->
          <el-form-item label="基础病史">
            <el-input
              v-model="form.history"
              type="textarea"
              :rows="3"
              placeholder="如：高血压病史 10 年、2 型糖尿病 5 年……"
              :disabled="loading"
            />
          </el-form-item>

          <!-- 当前症状 -->
          <el-form-item label="当前症状描述" required>
            <el-input
              v-model="form.symptoms"
              type="textarea"
              :rows="5"
              placeholder="请详细描述患者当前主诉、症状、体征、检查结果等……
示例：患者近一周出现头晕、视物模糊，自测血压 165/95 mmHg，空腹血糖 8.2 mmol/L……"
              :disabled="loading"
            />
          </el-form-item>

          <!-- 按钮组 -->
          <div class="mt-auto pt-3 flex gap-3">
            <el-button
              type="primary"
              size="large"
              class="flex-1 h-11 font-semibold text-base"
              :loading="loading"
              :disabled="!form.symptoms.trim()"
              @click="startConsultation"
            >
              {{ loading ? 'AI 正在分析中…' : '🧠 请求 AI 会诊' }}
            </el-button>
            <el-button
              size="large"
              class="h-11"
              :disabled="loading"
              @click="resetForm"
            >
              重置
            </el-button>
          </div>
        </el-form>
      </el-card>

      <!-- 底部提示 -->
      <div
        class="text-xs text-slate-400 text-center leading-relaxed flex-shrink-0"
      >
        ⚠️ 本系统为 AI 辅助决策工具，最终诊疗方案需由执业医师确认
      </div>
    </aside>

    <!-- ══════════════════════════ 右侧：AI 思考与输出区 ══════════════════════════ -->
    <main class="flex-1 flex flex-col p-5 pl-0 gap-4 min-w-0">
      <!-- 上半部分：Agent 执行日志（终端风格） -->
      <el-card
        shadow="hover"
        class="flex-1 flex flex-col min-h-0"
        :body-style="{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          padding: 0,
          overflow: 'hidden',
        }"
      >
        <template #header>
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2 text-medical-800 font-semibold">
              <span class="text-lg">🖥️</span>
              <span>Agent 执行日志</span>
              <el-tag
                v-if="loading"
                type="warning"
                size="small"
                effect="dark"
                round
              >
                执行中
              </el-tag>
              <el-tag
                v-else-if="toolLogs.length > 0"
                type="success"
                size="small"
                effect="dark"
                round
              >
                已完成
              </el-tag>
            </div>
            <el-button
              v-if="toolLogs.length > 0"
              size="small"
              text
              @click="toolLogs = []"
            >
              清空日志
            </el-button>
          </div>
        </template>

        <!-- 终端内容区 -->
        <div
          ref="terminalRef"
          class="terminal-scroll flex-1 bg-[#0d1117] text-green-400 font-mono text-sm p-4 overflow-y-auto whitespace-pre-wrap break-words leading-relaxed"
        >
          <!-- 空状态 -->
          <div
            v-if="toolLogs.length === 0"
            class="text-slate-500 flex items-center justify-center h-full"
          >
            <div class="text-center">
              <div class="text-3xl mb-3">🖥️</div>
              <div>Agent 执行日志将在此实时显示</div>
              <div class="text-xs mt-1 text-slate-600">
                请在左侧输入患者信息后点击「请求 AI 会诊」
              </div>
            </div>
          </div>

          <!-- 日志条目 -->
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

          <!-- 光标闪烁（正在输出中） -->
          <span
            v-if="loading"
            class="inline-block w-2 h-4 bg-green-400 animate-pulse align-middle ml-0.5"
          >&nbsp;</span>
        </div>
      </el-card>

      <!-- 下半部分：最终报告 -->
      <el-card
        shadow="hover"
        class="flex-1 flex flex-col min-h-0"
        :body-style="{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          padding: 0,
          overflow: 'hidden',
        }"
      >
        <template #header>
          <div class="flex items-center gap-2 text-medical-800 font-semibold">
            <span class="text-lg">📄</span>
            <span>智能诊疗辅助报告</span>
            <el-tag
              v-if="loading"
              type="info"
              size="small"
              effect="dark"
              round
            >
              生成中
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
        </template>

        <!-- 报告内容区 -->
        <div
          ref="reportRef"
          class="flex-1 overflow-y-auto p-6 bg-white"
        >
          <!-- 空状态 -->
          <div
            v-if="!finalReport && !loading"
            class="text-slate-400 flex items-center justify-center h-full"
          >
            <div class="text-center">
              <div class="text-3xl mb-3">📄</div>
              <div>AI 诊疗辅助报告将在此渲染</div>
              <div class="text-xs mt-1 text-slate-400">
                Markdown 格式的结构化报告
              </div>
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
          </div>

          <!-- Markdown 渲染 -->
          <div
            v-else
            class="markdown-body"
            v-html="renderedReport"
          ></div>
        </div>
      </el-card>
    </main>
  </div>
</template>
