<script setup lang="ts">
import type { Doctor } from '@/utils/doctor'

defineProps<{
  doctor: Doctor
}>()

const HOSPITAL_NAME = '临床智能诊疗辅助系统协作医院'
const HOSPITAL_LEVEL = '三级甲等'
</script>

<template>
  <el-card shadow="hover" class="doctor-info-card">
    <!-- 头像 + 基本信息 -->
    <div class="text-center pb-4 border-b border-gray-100">
      <el-avatar
        :src="doctor.avatar_url"
        :size="80"
        class="mb-3 ring-2 ring-blue-100"
      >
        {{ doctor.full_name?.charAt(0) }}
      </el-avatar>
      <h3 class="text-xl font-bold text-gray-800">{{ doctor.full_name }}</h3>
      <el-tag
        v-if="doctor.title"
        type="primary"
        size="small"
        class="mt-1"
      >
        {{ doctor.title }}
      </el-tag>
      <div class="text-sm text-gray-500 mt-2">{{ HOSPITAL_NAME }}</div>
      <div class="text-xs text-gray-400">{{ HOSPITAL_LEVEL }}</div>
    </div>

    <!-- 详细信息 -->
    <div class="py-3 space-y-3">
      <div v-if="doctor.department" class="flex items-start gap-3 text-sm">
        <span class="text-gray-400 flex-shrink-0 w-10 text-right">科室</span>
        <span class="text-gray-700">{{ doctor.department }}</span>
      </div>
      <div v-if="doctor.specialty" class="flex items-start gap-3 text-sm">
        <span class="text-gray-400 flex-shrink-0 w-10 text-right">专长</span>
        <span class="text-gray-700">{{ doctor.specialty }}</span>
      </div>
    </div>

    <!-- 个人简介 -->
    <div class="border-t border-gray-100 pt-3">
      <div class="text-xs text-gray-400 mb-2">个人简介</div>
      <p class="text-sm text-gray-600 leading-relaxed">
        {{ doctor.bio || '暂无简介' }}
      </p>
    </div>
  </el-card>
</template>

<style scoped>
.doctor-info-card {
  max-width: 400px;
}
</style>
