<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '@/stores/user'
import DoctorProfileDialog from '@/components/DoctorProfileDialog.vue'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const profileDialogVisible = ref(false)

function openProfile() {
  if (userStore.isDoctor) {
    profileDialogVisible.value = true
  }
}

// 根据角色动态生成菜单项
const menuItems = computed(() => {
  if (userStore.isDoctor) {
    return [
      { path: '/doctor/dashboard', title: '今日候诊', icon: 'List' },
      { path: '/doctor/workspace', title: 'AI 辅助会诊', icon: 'Cpu' },
      { path: '/doctor/schedule', title: '出诊排班', icon: 'Clock' },
      { path: '/doctor/knowledge', title: '指南知识库管理', icon: 'Collection' },
    ]
  }
  if (userStore.isPatient) {
    return [
      { path: '/patient/chatbot', title: 'AI 智能导诊', icon: 'ChatDotRound' },
      { path: '/patient/appointment', title: '预约挂号', icon: 'Calendar' },
      { path: '/patient/records', title: '我的预约记录', icon: 'Document' },
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
        <template v-if="userStore.isDoctor">
          <el-avatar
            :src="userStore.avatarUrl"
            :size="32"
            class="cursor-pointer hover:ring-2 hover:ring-blue-400 transition-all flex-shrink-0"
            @click="openProfile"
          >
            {{ userStore.fullName?.charAt(0) }}
          </el-avatar>
          <span
            class="text-sm text-slate-500 cursor-pointer hover:text-blue-600 transition-colors"
            @click="openProfile"
          >
            {{ userStore.fullName }}
            <el-tag size="small" type="primary">医生</el-tag>
          </span>
        </template>
        <template v-else>
          <span class="text-sm text-slate-500">
            {{ userStore.fullName }}
            <el-tag size="small" type="success">患者</el-tag>
          </span>
        </template>
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

    <!-- 医生个人信息弹窗 -->
    <DoctorProfileDialog v-if="userStore.isDoctor" v-model="profileDialogVisible" />
  </el-container>
</template>
