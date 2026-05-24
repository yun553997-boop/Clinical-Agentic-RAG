<script setup lang="ts">
import { ref, watch, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import type { UploadFile } from 'element-plus'
import { useUserStore, type UserProfile } from '@/stores/user'

const userStore = useUserStore()

const props = defineProps<{
  modelValue: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
}>()

const HOSPITAL_NAME = '临床智能诊疗辅助系统协作医院'
const HOSPITAL_LEVEL = '三级甲等'

const saving = ref(false)
const uploadRef = ref()

const form = reactive({
  full_name: '',
  gender: '' as string,
  title: '',
  specialty: '',
  phone: '',
  email: '',
  avatar_url: '',
  bio: '',
})

watch(() => props.modelValue, async (visible) => {
  if (visible) {
    await userStore.fetchProfile()
    const p = userStore.profile
    if (p) {
      form.full_name = p.full_name || ''
      form.gender = p.gender || ''
      form.title = p.title || ''
      form.specialty = p.specialty || ''
      form.phone = p.phone || ''
      form.email = p.email || ''
      form.avatar_url = p.avatar_url || ''
      form.bio = p.bio || ''
    }
  }
})

async function handleSave() {
  saving.value = true
  try {
    await userStore.updateProfile({
      full_name: form.full_name,
      gender: form.gender || null,
      title: form.title || null,
      specialty: form.specialty || null,
      phone: form.phone || null,
      email: form.email || null,
      avatar_url: form.avatar_url || null,
      bio: form.bio || null,
    })
    ElMessage.success('个人信息已更新')
    emit('update:modelValue', false)
  } catch {
    ElMessage.error('保存失败，请重试')
  } finally {
    saving.value = false
  }
}

function handleAvatarChange(file: UploadFile) {
  const raw = file.raw
  if (!raw) return
  if (!raw.type.startsWith('image/')) {
    ElMessage.warning('请选择图片文件')
    return
  }
  const reader = new FileReader()
  reader.onload = (e) => {
    form.avatar_url = e.target?.result as string
  }
  reader.readAsDataURL(raw)
}

function clearAvatar() {
  form.avatar_url = ''
  uploadRef.value?.clearFiles()
}

function handleCancel() {
  emit('update:modelValue', false)
}
</script>

<template>
  <el-dialog
    :model-value="modelValue"
    title="个人信息"
    width="520px"
    :close-on-click-modal="false"
    @update:model-value="emit('update:modelValue', $event)"
  >
    <el-form label-position="top" :disabled="saving">
      <!-- 头像 -->
      <div class="flex flex-col items-center mb-6">
        <el-avatar
          :src="form.avatar_url"
          :size="88"
          class="ring-2 ring-blue-100 mb-3"
        >
          {{ form.full_name?.charAt(0) || '医' }}
        </el-avatar>
        <div class="flex items-center gap-2">
          <el-upload
            ref="uploadRef"
            :auto-upload="false"
            :show-file-list="false"
            accept="image/*"
            :on-change="handleAvatarChange"
          >
            <el-button size="small" type="primary" plain>
              {{ form.avatar_url ? '更换头像' : '上传头像' }}
            </el-button>
          </el-upload>
          <el-button
            v-if="form.avatar_url"
            size="small"
            @click="clearAvatar"
          >
            移除
          </el-button>
        </div>
        <p class="text-xs text-gray-400 mt-1">支持 JPG / PNG / GIF / WebP</p>
      </div>

      <!-- 医院信息（只读） -->
      <div class="bg-gray-50 rounded-lg p-3 mb-4 text-sm space-y-1">
        <div class="flex">
          <span class="text-gray-400 w-16 flex-shrink-0">所属医院</span>
          <span class="text-gray-700">{{ HOSPITAL_NAME }}</span>
        </div>
        <div class="flex">
          <span class="text-gray-400 w-16 flex-shrink-0">医院等级</span>
          <span class="text-gray-700">{{ HOSPITAL_LEVEL }}</span>
        </div>
        <div v-if="userStore.profile?.department" class="flex">
          <span class="text-gray-400 w-16 flex-shrink-0">科室</span>
          <span class="text-gray-700">{{ userStore.profile.department }}</span>
        </div>
        <div v-if="userStore.profile?.employee_id" class="flex">
          <span class="text-gray-400 w-16 flex-shrink-0">工号</span>
          <span class="text-gray-700">{{ userStore.profile.employee_id }}</span>
        </div>
      </div>

      <!-- 基本信息 -->
      <div class="text-xs text-gray-400 mb-3 pb-2 border-b border-gray-100">基本信息</div>
      <div class="grid grid-cols-2 gap-x-4 gap-y-0">
        <el-form-item label="姓名">
          <el-input v-model="form.full_name" placeholder="真实姓名" />
        </el-form-item>
        <el-form-item label="性别">
          <el-select v-model="form.gender" placeholder="请选择" clearable>
            <el-option label="男" value="男" />
            <el-option label="女" value="女" />
          </el-select>
        </el-form-item>
        <el-form-item label="职称">
          <el-input v-model="form.title" placeholder="如: 主任医师" />
        </el-form-item>
        <el-form-item label="专长">
          <el-input v-model="form.specialty" placeholder="如: 消化内科" />
        </el-form-item>
      </div>

      <!-- 联系方式 -->
      <div class="text-xs text-gray-400 mb-3 pb-2 border-b border-gray-100">联系方式</div>
      <div class="grid grid-cols-2 gap-x-4 gap-y-0">
        <el-form-item label="手机号">
          <el-input v-model="form.phone" placeholder="手机号码" />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="form.email" placeholder="电子邮箱" />
        </el-form-item>
      </div>

      <!-- 个人简介 -->
      <div class="text-xs text-gray-400 mb-3 pb-2 border-b border-gray-100">个人简介</div>
      <el-form-item label="">
        <el-input
          v-model="form.bio"
          type="textarea"
          :rows="4"
          placeholder="请输入个人简介、教育背景、从业经历等..."
        />
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="handleCancel" :disabled="saving">取消</el-button>
      <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
    </template>
  </el-dialog>
</template>
