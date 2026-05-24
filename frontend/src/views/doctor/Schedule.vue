<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import request from '@/utils/request'

interface ScheduleItem {
  id: number
  doctor_id: number
  slot_date: string
  slot_time: string
  is_booked: boolean
}

const SCHEDULE_DATE_KEY = 'schedule_selected_date'
const selectedDate = ref(localStorage.getItem(SCHEDULE_DATE_KEY) || '')
const newTime = ref('')
const schedules = ref<ScheduleItem[]>([])
const loading = ref(false)
const adding = ref(false)

const today = new Date().toISOString().slice(0, 10)

onMounted(() => {
  if (selectedDate.value) {
    fetchSchedules()
  }
})

async function fetchSchedules() {
  if (!selectedDate.value) return
  loading.value = true
  try {
    const res = await request.get<ScheduleItem[]>('/api/schedules/my', {
      params: { date: selectedDate.value },
    })
    schedules.value = res.data
  } finally {
    loading.value = false
  }
}

watch(selectedDate, (val) => {
  if (val) {
    localStorage.setItem(SCHEDULE_DATE_KEY, val)
  } else {
    localStorage.removeItem(SCHEDULE_DATE_KEY)
  }
  fetchSchedules()
})

async function addSlot() {
  if (!newTime.value) {
    ElMessage.warning('请选择时间')
    return
  }
  if (!selectedDate.value) {
    ElMessage.warning('请先选择日期')
    return
  }
  adding.value = true
  try {
    await request.post('/api/schedules/', {
      slot_date: selectedDate.value,
      slot_time: newTime.value,
    })
    ElMessage.success('已添加时段')
    newTime.value = ''
    await fetchSchedules()
  } catch {
    ElMessage.error('添加失败')
  } finally {
    adding.value = false
  }
}

async function deleteSlot(id: number) {
  try {
    await request.delete(`/api/schedules/${id}`)
    ElMessage.success('已删除')
    await fetchSchedules()
  } catch {
    ElMessage.error('删除失败')
  }
}

function weekDay(dateStr: string) {
  const d = new Date(dateStr)
  const days = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']
  return days[d.getDay()]
}
</script>

<template>
  <div class="p-6 min-h-screen bg-slate-100/50">
    <h1 class="text-xl font-bold text-slate-800 mb-4">出诊排班管理</h1>

    <div class="flex gap-4 mb-6">
      <el-card shadow="hover" class="w-80 flex-shrink-0">
        <template #header>
          <span class="font-semibold text-slate-700">选择日期</span>
        </template>
        <el-date-picker
          v-model="selectedDate"
          type="date"
          placeholder="请选择日期"
          value-format="YYYY-MM-DD"
          :disabled-date="(d: Date) => {
            const today = new Date()
            today.setHours(0, 0, 0, 0)
            return d < today
          }"
          class="w-full"
        />
        <div
          v-if="selectedDate"
          class="mt-4 p-3 bg-blue-50 rounded-lg"
        >
          <div class="text-sm text-blue-700 font-semibold">
            {{ selectedDate }} {{ weekDay(selectedDate) }}
          </div>
        </div>
      </el-card>

      <el-card shadow="hover" class="flex-1">
        <template #header>
          <div class="flex items-center justify-between">
            <span class="font-semibold text-slate-700">
              时间段列表
              <span v-if="selectedDate" class="text-sm text-slate-400 font-normal ml-2">
                （共 {{ schedules.length }} 个时段）
              </span>
            </span>
          </div>
        </template>

        <!-- 空状态 -->
        <div
          v-if="!selectedDate"
          class="text-center text-slate-400 py-8"
        >
          <div class="text-3xl mb-2">📅</div>
          <p>请先在左侧选择日期</p>
        </div>

        <div v-else>
          <!-- 添加时段 -->
          <div class="flex items-center gap-3 mb-4 pb-4 border-b border-gray-100">
            <el-time-picker
              v-model="newTime"
              format="HH:mm"
              value-format="HH:mm"
              placeholder="选择时间"
              :disabled="adding"
            />
            <el-button
              type="primary"
              :loading="adding"
              :disabled="!newTime"
              @click="addSlot"
            >
              添加时段
            </el-button>
          </div>

          <!-- 时段列表 -->
          <div v-loading="loading">
            <div v-if="schedules.length === 0" class="text-center text-slate-400 py-6">
              暂无时段，请添加
            </div>
            <div
              v-for="s in schedules"
              :key="s.id"
              class="flex items-center justify-between py-3 px-4 rounded-lg mb-2"
              :class="s.is_booked
                ? 'bg-orange-50 border border-orange-200'
                : 'bg-green-50 border border-green-200'"
            >
              <div class="flex items-center gap-3">
                <el-tag
                  :type="s.is_booked ? 'warning' : 'success'"
                  size="small"
                  effect="dark"
                >
                  {{ s.is_booked ? '已预约' : '可用' }}
                </el-tag>
                <span class="text-slate-700 font-mono font-semibold">
                  {{ s.slot_time }}
                </span>
                <span class="text-xs text-slate-400">{{ s.slot_date }}</span>
              </div>
              <el-button
                v-if="!s.is_booked"
                type="danger"
                size="small"
                link
                @click="deleteSlot(s.id)"
              >
                删除
              </el-button>
            </div>
          </div>
        </div>
      </el-card>
    </div>
  </div>
</template>
