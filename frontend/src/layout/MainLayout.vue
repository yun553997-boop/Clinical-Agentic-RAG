<script setup lang="ts">
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

// 根据角色动态生成菜单项
const menuItems = computed(() => {
  if (userStore.isDoctor) {
    return [
      { path: '/doctor/dashboard', title: '今日候诊', icon: 'List' },
      { path: '/doctor/workspace', title: 'AI 辅助会诊', icon: 'Cpu' },
    ]
  }
  if (userStore.isPatient) {
    return [
      { path: '/patient/chatbot', title: 'AI 智能导诊', icon: 'ChatDotRound' },
      { path: '/patient/appointment', title: '预约挂号', icon: 'Calendar' },
    ]
  }
  return []
})

// 当前激活的菜单项
const activeMenu = computed(() => route.path)

// 处理菜单选择
function handleSelect(path: string) {
  router.push(path)
}

// 退出登录
function handleLogout() {
  userStore.logout()
  router.push('/login')
}
</script>

<template>
  <el-container class="h-screen">
    <!-- ══════════════════════════ 顶部导航栏 ══════════════════════════ -->
    <el-header class="flex items-center justify-between bg-white border-b shadow-sm px-5 h-14">
      <div class="flex items-center gap-3">
        <div
          class="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-700 to-blue-500 flex items-center justify-center shadow-md"
        >
          <span class="text-white text-sm font-bold">+</span>
        </div>
        <span class="text-base font-bold text-slate-800">智能临床诊疗系统</span>
      </div>

      <div class="flex items-center gap-3">
        <span class="text-sm text-slate-500">
          {{ userStore.userInfo.name }}
          <el-tag size="small" :type="userStore.isDoctor ? 'primary' : 'success'">
            {{ userStore.isDoctor ? '医生' : '患者' }}
          </el-tag>
        </span>
        <el-button size="small" text @click="handleLogout">退出登录</el-button>
      </div>
    </el-header>

    <el-container>
      <!-- ══════════════════════════ 左侧边栏 ══════════════════════════ -->
      <el-aside width="220px" class="bg-slate-50 border-r">
        <el-menu
          :default-active="activeMenu"
          class="border-none"
          @select="handleSelect"
        >
          <el-menu-item
            v-for="item in menuItems"
            :key="item.path"
            :index="item.path"
          >
            <el-icon><component :is="item.icon" /></el-icon>
            <span>{{ item.title }}</span>
          </el-menu-item>
        </el-menu>
      </el-aside>

      <!-- ══════════════════════════ 右侧主体区 ══════════════════════════ -->
      <el-main class="p-0">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>
