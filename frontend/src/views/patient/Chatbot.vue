<script setup lang="ts">
import { ref, nextTick, onMounted } from 'vue'
import MarkdownIt from 'markdown-it'

interface Message {
  role: 'user' | 'ai'
  content: string
}

const md = new MarkdownIt({ breaks: true, linkify: true })

const messages = ref<Message[]>([])
const input = ref('')
const loading = ref(false)
const chatRef = ref<HTMLElement | null>(null)

const welcomeMessage: Message = {
  role: 'ai',
  content:
    '您好！我是您的智能导诊助手，请告诉我您身体目前有哪些不舒服的症状（例如：头晕、肚子右下角隐隐作痛等），我来为您推荐合适的科室。',
}

onMounted(() => {
  messages.value.push({ ...welcomeMessage })
})

async function scrollToBottom() {
  await nextTick()
  if (chatRef.value) {
    chatRef.value.scrollTop = chatRef.value.scrollHeight
  }
}

async function sendMessage() {
  const text = input.value.trim()
  if (!text || loading.value) return

  messages.value.push({ role: 'user', content: text })
  input.value = ''
  loading.value = true
  await scrollToBottom()

  const aiMsg: Message = { role: 'ai', content: '' }
  messages.value.push(aiMsg)
  const aiIndex = messages.value.length - 1

  try {
    const response = await fetch('/api/chat/triage', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text }),
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
            if (event.content) {
              messages.value[aiIndex].content += event.content
              await scrollToBottom()
            }
          } catch {
            // 忽略不完整的 JSON
          }
        }
      }
    }
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : String(err)
    messages.value[aiIndex].content = `抱歉，连接出现了问题：${msg}，请稍后重试。`
  } finally {
    loading.value = false
  }
}

function renderMarkdown(text: string): string {
  return md.render(text)
}
</script>

<template>
  <div class="h-full flex flex-col bg-slate-50">
    <!-- 标题栏 -->
    <div class="flex items-center gap-3 px-5 py-3 bg-white border-b shadow-sm flex-shrink-0">
      <div
        class="w-9 h-9 rounded-lg bg-gradient-to-br from-emerald-600 to-teal-500 flex items-center justify-center shadow-md"
      >
        <span class="text-white text-base font-bold">+</span>
      </div>
      <div>
        <h1 class="text-base font-bold text-slate-800 leading-tight">AI 智能导诊</h1>
        <p class="text-xs text-slate-400">描述您的症状，为您推荐合适的科室</p>
      </div>
    </div>

    <!-- 消息列表 -->
    <div ref="chatRef" class="flex-1 overflow-y-auto px-4 py-5 space-y-4">
      <template v-for="(msg, i) in messages" :key="i">
        <!-- AI 消息（左侧） -->
        <div v-if="msg.role === 'ai'" class="flex gap-3 max-w-[85%]">
          <div
            class="w-8 h-8 rounded-full bg-gradient-to-br from-emerald-500 to-teal-400 flex items-center justify-center flex-shrink-0 shadow-sm"
          >
            <span class="text-white text-xs font-bold">AI</span>
          </div>
          <div class="bg-white rounded-2xl rounded-tl-sm px-4 py-3 shadow-sm border border-slate-100">
            <div
              v-if="msg.content"
              class="text-sm text-slate-700 leading-relaxed markdown-body"
              v-html="renderMarkdown(msg.content)"
            ></div>
            <div v-else class="flex items-center gap-1 text-slate-400 text-sm">
              <span class="inline-block w-2 h-2 bg-slate-300 rounded-full animate-bounce"></span>
              <span class="inline-block w-2 h-2 bg-slate-300 rounded-full animate-bounce" style="animation-delay: 0.15s"></span>
              <span class="inline-block w-2 h-2 bg-slate-300 rounded-full animate-bounce" style="animation-delay: 0.3s"></span>
            </div>
          </div>
        </div>

        <!-- 用户消息（右侧） -->
        <div v-else class="flex justify-end">
          <div class="max-w-[75%] bg-gradient-to-br from-blue-600 to-blue-500 rounded-2xl rounded-tr-sm px-4 py-3 shadow-sm">
            <p class="text-sm text-white leading-relaxed whitespace-pre-wrap">{{ msg.content }}</p>
          </div>
        </div>
      </template>
    </div>

    <!-- 底部输入框 -->
    <div class="flex-shrink-0 px-4 py-3 bg-white border-t">
      <div class="flex items-end gap-3">
        <el-input
          v-model="input"
          type="textarea"
          :rows="1"
          :autosize="{ minRows: 1, maxRows: 4 }"
          placeholder="请描述您身体的不适症状..."
          :disabled="loading"
          resize="none"
          class="flex-1"
          @keydown.enter.exact.prevent="sendMessage"
        />
        <el-button
          type="primary"
          :disabled="!input.trim() || loading"
          :loading="loading"
          @click="sendMessage"
          class="h-10"
        >
          <template v-if="!loading">发送</template>
        </el-button>
      </div>
    </div>
  </div>
</template>
