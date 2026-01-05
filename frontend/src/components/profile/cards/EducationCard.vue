<!-- C:\Users\Vinay\Project\frontend\src\components\profile\cards\EducationCard.vue -->
<!-- --- THIS IS THE FINAL, DEFINITIVE CODE --- -->

<script setup lang="ts">
import type { PropType } from 'vue'
import type { EducationEntry } from '@/types'
import { PencilIcon, TrashIcon } from '@heroicons/vue/24/solid'
// CORRECTED IMPORT
import { format, getMonth } from 'date-fns'
import { useProfileStore } from '@/stores/profile'

const props = defineProps({
  educationEntry: {
    type: Object as PropType<EducationEntry>,
    required: true,
  },
  isOwnProfile: {
    type: Boolean,
    required: true,
  },
})

const emit = defineEmits(['edit'])

const profileStore = useProfileStore()

async function handleDelete() {
  if (confirm('Are you sure you want to delete this education entry?')) {
    try {
      const username = profileStore.currentProfile?.user.username
      if (username) {
        await profileStore.deleteEducation(username, props.educationEntry.id)
      }
    } catch (error) {
      console.error('Failed to delete education:', error)
      alert('Could not delete education entry. Please try again.')
    }
  }
}

function formatDateRange(startDateStr: string | null, endDateStr: string | null): string {
  if (!startDateStr) return ''

  const formatSingleDate = (dateStr: string) => {
    const date = new Date(dateStr)
    // CORRECTED FUNCTION CALL
    if (getMonth(date) === 0) {
      // getMonth is 0 for January
      return format(date, 'yyyy')
    }
    return format(date, 'MMM yyyy')
  }

  const start = formatSingleDate(startDateStr)
  const end = endDateStr ? formatSingleDate(endDateStr) : 'Present'

  return `${start} - ${end}`
}
</script>

<template>
  <li class="flex justify-between items-start">
    <div>
      <h4 class="font-bold text-gray-800">{{ educationEntry.institution }}</h4>
      <p
        v-if="educationEntry.degree || educationEntry.field_of_study"
        class="text-sm text-gray-600"
      >
        {{ educationEntry.degree
        }}<span v-if="educationEntry.degree && educationEntry.field_of_study">, </span
        >{{ educationEntry.field_of_study }}
      </p>
      <p v-if="educationEntry.university" class="text-sm text-gray-600">
        University: {{ educationEntry.university }}
      </p>
      <p v-if="educationEntry.board" class="text-sm text-gray-600">
        Board: {{ educationEntry.board }}
      </p>
      <p class="text-xs text-gray-500 mt-1">
        {{ formatDateRange(educationEntry.start_date, educationEntry.end_date) }}
        <span v-if="educationEntry.location"> · {{ educationEntry.location }}</span>
      </p>
      <p v-if="educationEntry.description" class="mt-2 text-sm text-gray-700 whitespace-pre-wrap">
        {{ educationEntry.description }}
      </p>
      <p v-if="educationEntry.achievements" class="mt-2 text-sm text-gray-700">
        <span class="font-semibold">Achievements:</span> {{ educationEntry.achievements }}
      </p>
    </div>
    <div v-if="isOwnProfile" class="flex items-center space-x-2 ml-4 flex-shrink-0">
      <button
        @click="$emit('edit', educationEntry)"
        class="text-gray-400 hover:text-blue-500 transition-colors duration-200"
        aria-label="Edit education"
      >
        <PencilIcon class="h-5 w-5" />
      </button>
      <button
        @click="handleDelete"
        class="text-gray-400 hover:text-red-500 transition-colors duration-200"
        aria-label="Delete education"
      >
        <TrashIcon class="h-5 w-5" />
      </button>
    </div>
  </li>
</template>
