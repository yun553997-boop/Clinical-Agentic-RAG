<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import type { UploadRequestOptions } from 'element-plus'
import request from '@/utils/request'

interface Doc {
  id: number
  filename: string
  upload_time: string
  uploader_name: string
  status: string
}

const docs = ref<Doc[]>([])
const loading = ref(false)
const uploading = ref(false)

function formatTime(dateStr: string) {
  const d = new Date(dateStr)
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  const h = String(d.getHours()).padStart(2, '0')
  const min = String(d.getMinutes()).padStart(2, '0')
  return `${y}-${m}-${day} ${h}:${min}`
}

async function fetchDocs() {
  loading.value = true
  try {
    const res = await request.get<Doc[]>('/api/knowledge/')
    docs.value = res.data
  } finally {
    loading.value = false
  }
}

async function handleUpload(options: UploadRequestOptions) {
  uploading.value = true
  try {
    const formData = new FormData()
    formData.append('file', options.file)
    await request.post('/api/knowledge/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    ElMessage.success('文档上传并向量化成功')
    await fetchDocs()
  } catch {
    ElMessage.error('上传失败，请确保文件为有效 PDF')
  } finally {
    uploading.value = false
  }
}

async function handleDelete(id: number) {
  try {
    await request.delete(`/api/knowledge/${id}`)
    ElMessage.success('文档已删除')
    await fetchDocs()
  } catch {
    ElMessage.error('删除失败，请重试')
  }
}

onMounted(() => {
  fetchDocs()
})
</script>

<template>
  <div class="p-6">
    <h1 class="text-xl font-bold text-slate-800 mb-4">指南知识库管理</h1>

    <!-- 上传区域 -->
    <el-card shadow="hover" class="mb-4">
      <div class="flex items-center gap-4">
        <span class="text-sm text-slate-600">上传医学指南 PDF：</span>
        <el-upload
          :http-request="handleUpload"
          :show-file-list="false"
          accept=".pdf"
          :disabled="uploading"
        >
          <el-button type="primary" :loading="uploading" :icon="'Upload'">
            {{ uploading ? '正在解析并向量化...' : '选择 PDF 文件上传' }}
          </el-button>
        </el-upload>
        <span class="text-xs text-slate-400">仅支持 PDF 格式，文件将自动解析、切分并注入向量知识库</span>
      </div>
    </el-card>

    <!-- 文档列表 -->
    <el-card shadow="hover">
      <el-table
        v-if="docs.length > 0"
        :data="docs"
        v-loading="loading"
        stripe
        class="w-full"
      >
        <el-table-column prop="filename" label="文件名" min-width="200" />
        <el-table-column prop="uploader_name" label="上传者" min-width="100" />
        <el-table-column label="上传时间" min-width="160">
          <template #default="{ row }">
            {{ formatTime(row.upload_time) }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="向量化状态" min-width="110">
          <template #default="{ row }">
            <el-tag
              :type="row.status === '已向量化' ? 'success' : row.status === '向量化中' ? 'warning' : 'danger'"
              size="small"
            >
              {{ row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" min-width="80" fixed="right">
          <template #default="{ row }">
            <el-popconfirm
              title="确认删除该知识文档及对应向量数据？"
              confirm-button-text="确认删除"
              cancel-button-text="取消"
              @confirm="handleDelete(row.id)"
            >
              <template #reference>
                <el-button type="danger" link size="small">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-else v-loading="loading" description="暂无知识库文档，请上传 PDF 指南" />
    </el-card>
  </div>
</template>
