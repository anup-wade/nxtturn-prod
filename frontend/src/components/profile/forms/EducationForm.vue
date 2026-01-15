<!-- C:\Users\Vinay\Project\frontend\src\components\profile\forms\EducationForm.vue -->
<!-- --- THIS IS THE DEFINITIVE VERSION WITH VERTICAL LAYOUT --- -->

<script setup lang="ts">
import { ref, watch } from 'vue'
import type { EducationEntry } from '@/types'

// Omit 'id' as the backend handles that.
type EducationFormData = Omit<EducationEntry, 'id'>

const props = defineProps<{
  initialData?: EducationEntry | null
}>()

const emit = defineEmits(['save', 'cancel'])

// --- UI state for year/month ---
const startYear = ref<number | null>(null)
const startMonth = ref<number | null>(null)
const endYear = ref<number | null>(null)
const endMonth = ref<number | null>(null)

// --- State for other form data ---
const form = ref({
  institution: '',
  degree: '',
  field_of_study: '',
  university: '',
  board: '',
  description: '',
  location: '',
  achievements: '',
})

// Helper to combine year/month into a YYYY-MM-DD string
function combineDate(year: number | null, month: number | null): string | null {
  if (!year) {
    return null
  }
  const monthStr = month ? String(month).padStart(2, '0') : '01'
  return `${year}-${monthStr}-01`
}

// Watcher to populate the form for editing
watch(
  () => props.initialData,
  (newData) => {
    if (newData) {
      if (newData.start_date) {
        const startDate = new Date(newData.start_date)
        startYear.value = startDate.getUTCFullYear()
        startMonth.value = startDate.getUTCMonth() + 1
      } else {
        startYear.value = null
        startMonth.value = null
      }

      if (newData.end_date) {
        const endDate = new Date(newData.end_date)
        endYear.value = endDate.getUTCFullYear()
        endMonth.value = endDate.getUTCMonth() + 1
      } else {
        endYear.value = null
        endMonth.value = null
      }

      form.value = {
        institution: newData.institution || '',
        degree: newData.degree || '',
        field_of_study: newData.field_of_study || '',
        university: newData.university || '',
        board: newData.board || '',
        description: newData.description || '',
        location: newData.location || '',
        achievements: newData.achievements || '',
      }
    } else {
      // Reset form
      startYear.value = null
      startMonth.value = null
      endYear.value = null
      endMonth.value = null
      form.value = {
        institution: '',
        degree: '',
        field_of_study: '',
        university: '',
        board: '',
        description: '',
        location: '',
        achievements: '',
      }
    }
  },
  { immediate: true },
)

function handleSubmit() {
  const payload: EducationFormData = {
    ...form.value,
    start_date: combineDate(startYear.value, startMonth.value),
    end_date: combineDate(endYear.value, endMonth.value),
  }
  emit('save', payload)
}

const monthOptions = [
  { value: 1, name: 'January' },
  { value: 2, name: 'February' },
  { value: 3, name: 'March' },
  { value: 4, name: 'April' },
  { value: 5, name: 'May' },
  { value: 6, name: 'June' },
  { value: 7, name: 'July' },
  { value: 8, name: 'August' },
  { value: 9, name: 'September' },
  { value: 10, name: 'October' },
  { value: 11, name: 'November' },
  { value: 12, name: 'December' },
]
</script>

<template>
  <form @submit.prevent="handleSubmit">
    <div class="space-y-4">
      <!-- Institution -->
      <div>
        <label for="institution" class="block text-sm font-medium text-gray-700"
          >Institution / School</label
        >
        <input
          v-model="form.institution"
          type="text"
          id="institution"
          required
          class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm"
        />
      </div>

      <!-- Degree & Field of Study -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label for="degree" class="block text-sm font-medium text-gray-700">Degree</label>
          <input
            v-model="form.degree"
            type="text"
            id="degree"
            class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm"
          />
        </div>
        <div>
          <label for="field_of_study" class="block text-sm font-medium text-gray-700"
            >Field of Study</label
          >
          <input
            v-model="form.field_of_study"
            type="text"
            id="field_of_study"
            class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm"
          />
        </div>
      </div>

      <!-- Year and Optional Month Inputs -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <!-- Start Date Section -->
        <div>
          <label class="block text-sm font-medium text-gray-700">Start Date</label>
          <!-- THE FIX: Inputs are now stacked in a div with vertical spacing -->
          <div class="mt-1 space-y-2">
            <select
              v-model.number="startMonth"
              class="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm"
            >
              <option :value="null">Month (Optional)</option>
              <option v-for="month in monthOptions" :key="month.value" :value="month.value">
                {{ month.name }}
              </option>
            </select>
            <input
              v-model.number="startYear"
              type="number"
              placeholder="Year"
              class="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm"
            />
          </div>
        </div>
        <!-- End Date Section -->
        <div>
          <label class="block text-sm font-medium text-gray-700">End Date</label>
          <!-- THE FIX: Inputs are now stacked in a div with vertical spacing -->
          <div class="mt-1 space-y-2">
            <select
              v-model.number="endMonth"
              class="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm"
            >
              <option :value="null">Month (Optional)</option>
              <option v-for="month in monthOptions" :key="month.value" :value="month.value">
                {{ month.name }}
              </option>
            </select>
            <input
              v-model.number="endYear"
              type="number"
              placeholder="Year"
              class="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm"
            />
          </div>
        </div>
      </div>

      <!-- Other fields... -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label for="university" class="block text-sm font-medium text-gray-700"
            >University (Optional)</label
          >
          <input
            v-model="form.university"
            type="text"
            id="university"
            class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm"
          />
        </div>
        <div>
          <label for="board" class="block text-sm font-medium text-gray-700"
            >Board (Optional)</label
          >
          <input
            v-model="form.board"
            type="text"
            id="board"
            class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm"
          />
        </div>
      </div>
      <div>
        <label for="location" class="block text-sm font-medium text-gray-700"
          >Location (e.g., City, Country)</label
        >
        <input
          v-model="form.location"
          type="text"
          id="location"
          class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm"
        />
      </div>
      <div>
        <label for="description" class="block text-sm font-medium text-gray-700">Description</label>
        <textarea
          v-model="form.description"
          id="description"
          rows="3"
          class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm"
        ></textarea>
      </div>
      <div>
        <label for="achievements" class="block text-sm font-medium text-gray-700"
          >Achievements / Activities</label
        >
        <textarea
          v-model="form.achievements"
          id="achievements"
          rows="3"
          class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm"
        ></textarea>
      </div>
    </div>

    <!-- Form Actions -->
    <div class="mt-6 flex justify-end space-x-3">
      <button
        type="button"
        @click="$emit('cancel')"
        class="px-4 py-2 bg-white border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 hover:bg-gray-50"
      >
        Cancel
      </button>
      <button
        type="submit"
        class="px-4 py-2 bg-blue-600 border border-transparent rounded-md shadow-sm text-sm font-medium text-white hover:bg-blue-700"
      >
        Save
      </button>
    </div>
  </form>
</template>
