<script setup lang="ts">
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()
</script>

<template>
  <div class="p-6">
    <h1 class="text-xl font-bold text-slate-800 mb-4">预约挂号</h1>
    <el-card shadow="hover">
      <p class="text-slate-500">欢迎，{{ userStore.userInfo.name }}。预约挂号功能开发中...</p>
    </el-card>
  </div>
</template>
