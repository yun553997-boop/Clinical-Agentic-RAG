<script setup lang="ts">
import PrescriptionForm from '@/components/PrescriptionForm.vue'
import type { PrescriptionData } from '@/components/PrescriptionForm.vue'

export type { PrescriptionData, MedicationItem } from '@/components/PrescriptionForm.vue'

defineProps<{
  modelValue: PrescriptionData
  disabled?: boolean
  patientName?: string
  patientAge?: number | string
  prescriptionFilled?: boolean
  appointmentId?: number | null
  hasAiReport?: boolean
  submitting?: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: PrescriptionData]
  'autoFill': []
  'submit': []
}>()

const today = new Date().toLocaleDateString('zh-CN', {
  year: 'numeric',
  month: 'long',
  day: 'numeric',
})
</script>

<template>
  <div class="prescription-pad bg-white">
    <!-- 处方筏标题 -->
    <div class="border-2 border-green-700 p-6 bg-green-50/30">
      <!-- 医院信息 -->
      <div class="text-center border-b-2 border-green-700 pb-3 mb-4">
        <h2 class="text-xl font-bold text-green-800 tracking-widest">门诊处方笺</h2>
        <p class="text-xs text-green-600 mt-1">临床智能诊疗辅助系统 · AI 辅助开具</p>
      </div>

      <!-- 患者信息行 -->
      <div class="grid grid-cols-4 gap-4 text-sm mb-4 pb-3 border-b border-dashed border-green-300">
        <div>
          <span class="text-green-700 font-semibold">姓名：</span>
          <span class="border-b border-green-400 px-2 min-w-[60px] inline-block">
            {{ patientName || '________' }}
          </span>
        </div>
        <div>
          <span class="text-green-700 font-semibold">年龄：</span>
          <span class="border-b border-green-400 px-2 min-w-[40px] inline-block">
            {{ patientAge || '__' }}
          </span>
        </div>
        <div>
          <span class="text-green-700 font-semibold">科室：</span>
          <span class="border-b border-green-400 px-2 min-w-[60px] inline-block">
            全科
          </span>
        </div>
        <div>
          <span class="text-green-700 font-semibold">日期：</span>
          <span class="border-b border-green-400 px-2 min-w-[80px] inline-block">
            {{ today }}
          </span>
        </div>
      </div>

      <!-- 处方表单 -->
      <div class="mb-4">
        <div class="flex items-center justify-between mb-3">
          <h3 class="text-base font-bold text-green-800">Rp. 处方药品</h3>
          <el-button
            v-if="hasAiReport"
            type="success"
            size="small"
            :disabled="disabled"
            @click="emit('autoFill')"
          >
            🤖 从 AI 报告一键填入
          </el-button>
        </div>

        <PrescriptionForm
          :model-value="modelValue"
          :disabled="disabled"
          @update:model-value="emit('update:modelValue', $event)"
        />
      </div>

      <!-- 底部签名区 -->
      <div class="border-t border-dashed border-green-300 pt-4">
        <div class="flex justify-between text-sm text-green-700">
          <div>
            <span class="font-semibold">医师签名：</span>
            <span class="border-b border-green-400 px-4 min-w-[80px] inline-block"></span>
          </div>
          <div>
            <span class="font-semibold">审核药师：</span>
            <span class="border-b border-green-400 px-4 min-w-[80px] inline-block"></span>
          </div>
          <div>
            <span class="font-semibold">调配药师：</span>
            <span class="border-b border-green-400 px-4 min-w-[80px] inline-block"></span>
          </div>
        </div>
        <div class="text-xs text-green-500 text-center mt-3">
          本处方由 AI 辅助生成，最终由执业医师审核确认
        </div>
      </div>
    </div>
  </div>
</template>
