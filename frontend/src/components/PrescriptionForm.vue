<script setup lang="ts">
import { computed } from 'vue'

export interface MedicationItem {
  drug_name: string
  specification: string
  dosage: string
  usage_method: string
  frequency: string
  days: number
}

export interface PrescriptionData {
  diagnosis: string
  medications: MedicationItem[]
  notes: string
}

const props = defineProps<{
  modelValue: PrescriptionData
  disabled?: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: PrescriptionData]
}>()

const usageOptions = ['口服', '静脉注射', '肌内注射', '皮下注射', '外用', '舌下含服', '雾化吸入']
const frequencyOptions = ['每日1次', '每日2次', '每日3次', '每日4次', '必要时', '睡前']

const medications = computed({
  get: () => props.modelValue.medications,
  set: (val) => emit('update:modelValue', { ...props.modelValue, medications: val }),
})

function updateField(field: keyof PrescriptionData, value: string) {
  emit('update:modelValue', { ...props.modelValue, [field]: value })
}

function addDrug() {
  const updated = [...medications.value, {
    drug_name: '',
    specification: '',
    dosage: '',
    usage_method: '口服',
    frequency: '每日1次',
    days: 7,
  }]
  medications.value = updated
}

function removeDrug(index: number) {
  const updated = medications.value.filter((_, i) => i !== index)
  medications.value = updated
}
</script>

<template>
  <div class="prescription-form">
    <!-- 诊断 -->
    <div class="mb-4">
      <label class="block text-sm font-semibold text-slate-700 mb-1.5">诊断结论</label>
      <el-input
        :model-value="modelValue.diagnosis"
        type="textarea"
        :rows="2"
        placeholder="请输入诊断结论"
        :disabled="disabled"
        @input="updateField('diagnosis', $event as string)"
      />
    </div>

    <!-- 药品列表 -->
    <div class="mb-4">
      <div class="flex items-center justify-between mb-2">
        <label class="text-sm font-semibold text-slate-700">药品清单</label>
        <el-button
          v-if="!disabled"
          type="primary"
          size="small"
          text
          @click="addDrug"
        >
          ＋ 添加药品
        </el-button>
      </div>

      <div
        v-for="(drug, i) in medications"
        :key="i"
        class="border border-slate-200 rounded-lg p-3 mb-2 relative bg-white"
      >
        <!-- 第一行：药品名称 + 规格 -->
        <div class="grid grid-cols-2 gap-2 mb-2">
          <div>
            <label class="text-xs text-slate-500 mb-0.5 block">药品名称</label>
            <el-input
              v-model="drug.drug_name"
              size="small"
              placeholder="如：阿莫西林"
              :disabled="disabled"
            />
          </div>
          <div>
            <label class="text-xs text-slate-500 mb-0.5 block">规格</label>
            <el-input
              v-model="drug.specification"
              size="small"
              placeholder="如：0.5g/粒"
              :disabled="disabled"
            />
          </div>
        </div>

        <!-- 第二行：用量 + 用法 -->
        <div class="grid grid-cols-2 gap-2 mb-2">
          <div>
            <label class="text-xs text-slate-500 mb-0.5 block">单次用量</label>
            <el-input
              v-model="drug.dosage"
              size="small"
              placeholder="如：1粒"
              :disabled="disabled"
            />
          </div>
          <div>
            <label class="text-xs text-slate-500 mb-0.5 block">用法</label>
            <el-select
              v-model="drug.usage_method"
              size="small"
              class="w-full"
              :disabled="disabled"
            >
              <el-option
                v-for="u in usageOptions"
                :key="u"
                :label="u"
                :value="u"
              />
            </el-select>
          </div>
        </div>

        <!-- 第三行：频次 + 天数 -->
        <div class="grid grid-cols-2 gap-2">
          <div>
            <label class="text-xs text-slate-500 mb-0.5 block">频次</label>
            <el-select
              v-model="drug.frequency"
              size="small"
              class="w-full"
              :disabled="disabled"
            >
              <el-option
                v-for="f in frequencyOptions"
                :key="f"
                :label="f"
                :value="f"
              />
            </el-select>
          </div>
          <div>
            <label class="text-xs text-slate-500 mb-0.5 block">天数</label>
            <el-input-number
              v-model="drug.days"
              size="small"
              :min="1"
              :max="90"
              :disabled="disabled"
              class="w-full"
            />
          </div>
        </div>

        <!-- 删除按钮 -->
        <el-button
          v-if="!disabled && medications.length > 1"
          type="danger"
          size="small"
          text
          class="absolute -top-1 -right-1"
          @click="removeDrug(i)"
        >
          ✕
        </el-button>
      </div>

      <p
        v-if="medications.length === 0"
        class="text-sm text-slate-400 text-center py-3"
      >
        暂无药品，请点击"添加药品"或从AI报告一键填入
      </p>
    </div>

    <!-- 医嘱备注 -->
    <div>
      <label class="block text-sm font-semibold text-slate-700 mb-1.5">医嘱备注</label>
      <el-input
        :model-value="modelValue.notes"
        type="textarea"
        :rows="3"
        placeholder="如：饭后服用、避免饮酒、定期复查肝功能..."
        :disabled="disabled"
        @input="updateField('notes', $event as string)"
      />
    </div>
  </div>
</template>
