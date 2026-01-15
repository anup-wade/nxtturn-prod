<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import type { Experience } from '@/types'

// --- Props & Emits ---
const props = defineProps<{
  initialData?: Experience | null // If null, we are in "Add" mode
  isSubmitting?: boolean
}>()

const emit = defineEmits<{
  (e: 'submit', payload: Omit<Experience, 'id'>): void
  (e: 'cancel'): void
}>()

// --- Constants ---
const MONTHS = [
  { value: '01', label: 'January' },
  { value: '02', label: 'February' },
  { value: '03', label: 'March' },
  { value: '04', label: 'April' },
  { value: '05', label: 'May' },
  { value: '06', label: 'June' },
  { value: '07', label: 'July' },
  { value: '08', label: 'August' },
  { value: '09', label: 'September' },
  { value: '10', label: 'October' },
  { value: '11', label: 'November' },
  { value: '12', label: 'December' },
]

// --- Form State ---
const title = ref('')
const company = ref('')
const location = ref('')
const description = ref('')
const isCurrentRole = ref(false)

// Date State (Split into Month/Year for better UX)
const startMonth = ref('')
const startYear = ref<number | null>(null)
const endMonth = ref('')
const endYear = ref<number | null>(null)

// --- Validation Errors ---
const errors = ref({
  title: '',
  company: '',
  startDate: '',
  endDate: '',
})

// --- Initialize Data ---
onMounted(() => {
  if (props.initialData) {
    title.value = props.initialData.title
    company.value = props.initialData.company
    location.value = props.initialData.location || ''
    description.value = props.initialData.description || ''

    // Parse Start Date
    if (props.initialData.start_date) {
      const [y, m] = props.initialData.start_date.split('-')
      startYear.value = parseInt(y)
      startMonth.value = m
    }

    // Parse End Date
    if (props.initialData.end_date) {
      const [y, m] = props.initialData.end_date.split('-')
      endYear.value = parseInt(y)
      endMonth.value = m
      isCurrentRole.value = false
    } else {
      isCurrentRole.value = true
    }
  }
})

// --- Helper: Format Date for API (YYYY-MM-01) ---
function formatDatePayload(year: number | null, month: string): string {
  if (!year || !month) return ''
  return `${year}-${month}-01`
}

// --- Submit Handler ---
function handleSubmit() {
  // 1. Reset Errors
  errors.value = { title: '', company: '', startDate: '', endDate: '' }
  let isValid = true

  // 2. Validate Required Fields
  if (!title.value.trim()) {
    errors.value.title = 'Job title is required'
    isValid = false
  }
  if (!company.value.trim()) {
    errors.value.company = 'Company name is required'
    isValid = false
  }
  if (!startYear.value || !startMonth.value) {
    errors.value.startDate = 'Start date is required'
    isValid = false
  }

  // 3. Validate End Date Logic
  if (!isCurrentRole.value) {
    if (!endYear.value || !endMonth.value) {
      errors.value.endDate = 'End date is required for past roles'
      isValid = false
    } else {
      // Check if End Date is before Start Date
      const start = new Date(startYear.value!, parseInt(startMonth.value) - 1)
      const end = new Date(endYear.value!, parseInt(endMonth.value) - 1)
      if (end < start) {
        errors.value.endDate = 'End date cannot be before start date'
        isValid = false
      }
    }
  }

  if (!isValid) return

  // 4. Construct Payload
  const payload: Omit<Experience, 'id'> = {
    title: title.value,
    company: company.value,
    location: location.value || null,
    description: description.value || null,
    start_date: formatDatePayload(startYear.value, startMonth.value),
    end_date: isCurrentRole.value ? null : formatDatePayload(endYear.value, endMonth.value),
  }

  emit('submit', payload)
}
</script>

<template>
  <form @submit.prevent="handleSubmit" class="space-y-4">
    <!-- Title -->
    <div>
      <label class="block text-sm font-medium text-gray-700"
        >Job Title <span class="text-red-500">*</span></label
      >
      <input
        v-model="title"
        type="text"
        class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm p-2 border"
        placeholder="e.g. Senior Software Engineer"
      />
      <p v-if="errors.title" class="text-red-500 text-xs mt-1">{{ errors.title }}</p>
    </div>

    <!-- Company -->
    <div>
      <label class="block text-sm font-medium text-gray-700"
        >Company Name <span class="text-red-500">*</span></label
      >
      <input
        v-model="company"
        type="text"
        class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm p-2 border"
        placeholder="e.g. Microsoft"
      />
      <p v-if="errors.company" class="text-red-500 text-xs mt-1">{{ errors.company }}</p>
    </div>

    <!-- Location -->
    <div>
      <label class="block text-sm font-medium text-gray-700">Location</label>
      <input
        v-model="location"
        type="text"
        class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm p-2 border"
        placeholder="e.g. Bangalore, India (Optional)"
      />
    </div>

    <!-- Checkbox: Current Role -->
    <div class="flex items-center gap-2 mt-2">
      <input
        id="isCurrent"
        v-model="isCurrentRole"
        type="checkbox"
        class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
      />
      <label for="isCurrent" class="text-sm text-gray-700 select-none">I currently work here</label>
    </div>

    <!-- Dates Grid -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <!-- Start Date -->
      <div>
        <label class="block text-sm font-medium text-gray-700"
          >Start Date <span class="text-red-500">*</span></label
        >
        <div class="flex gap-2 mt-1">
          <select
            v-model="startMonth"
            class="block w-1/2 rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm p-2 border"
          >
            <option value="" disabled>Month</option>
            <option v-for="m in MONTHS" :key="m.value" :value="m.value">{{ m.label }}</option>
          </select>
          <input
            v-model="startYear"
            type="number"
            placeholder="Year"
            min="1960"
            :max="new Date().getFullYear() + 1"
            class="block w-1/2 rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm p-2 border"
          />
        </div>
        <p v-if="errors.startDate" class="text-red-500 text-xs mt-1">{{ errors.startDate }}</p>
      </div>

      <!-- End Date -->
      <div v-if="!isCurrentRole">
        <label class="block text-sm font-medium text-gray-700"
          >End Date <span class="text-red-500">*</span></label
        >
        <div class="flex gap-2 mt-1">
          <select
            v-model="endMonth"
            class="block w-1/2 rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm p-2 border"
          >
            <option value="" disabled>Month</option>
            <option v-for="m in MONTHS" :key="m.value" :value="m.value">{{ m.label }}</option>
          </select>
          <input
            v-model="endYear"
            type="number"
            placeholder="Year"
            min="1960"
            :max="new Date().getFullYear() + 5"
            class="block w-1/2 rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm p-2 border"
          />
        </div>
        <p v-if="errors.endDate" class="text-red-500 text-xs mt-1">{{ errors.endDate }}</p>
      </div>
    </div>

    <!-- Description -->
    <div>
      <label class="block text-sm font-medium text-gray-700">Description</label>
      <textarea
        v-model="description"
        rows="4"
        class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm p-2 border"
        placeholder="Describe your role, responsibilities, and achievements..."
      ></textarea>
    </div>

    <!-- Actions -->
    <div class="flex justify-end gap-3 pt-2">
      <button
        type="button"
        @click="emit('cancel')"
        class="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
      >
        Cancel
      </button>
      <button
        type="submit"
        :disabled="isSubmitting"
        class="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {{ isSubmitting ? 'Saving...' : 'Save' }}
      </button>
    </div>
  </form>
</template>
