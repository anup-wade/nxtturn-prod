<script setup lang="ts">
import { computed } from 'vue'
import { PencilIcon, TrashIcon, MapPinIcon, BriefcaseIcon } from '@heroicons/vue/24/outline'
import type { Experience } from '@/types'
import { format, parseISO } from 'date-fns'

const props = defineProps<{
  experience: Experience
  isOwner: boolean
}>()

const emit = defineEmits<{
  (e: 'edit', id: number): void
  (e: 'delete', id: number): void
}>()

// --- Date Formatting Logic ---
const formattedDateRange = computed(() => {
  if (!props.experience.start_date) return ''

  const startDate = parseISO(props.experience.start_date)
  const startStr = format(startDate, 'MMM yyyy')

  let endStr = 'Present'
  if (props.experience.end_date) {
    const endDate = parseISO(props.experience.end_date)
    endStr = format(endDate, 'MMM yyyy')
  }

  return `${startStr} - ${endStr}`
})

// --- Duration Calculation (Optional but nice) ---
const durationString = computed(() => {
  if (!props.experience.start_date) return ''

  const start = parseISO(props.experience.start_date)
  const end = props.experience.end_date ? parseISO(props.experience.end_date) : new Date()

  // Calculate difference in months
  let months = (end.getFullYear() - start.getFullYear()) * 12
  months -= start.getMonth()
  months += end.getMonth()
  // Add 1 month to be inclusive (e.g., Jan to Jan is 1 month of work)
  months += 1

  const years = Math.floor(months / 12)
  const remainingMonths = months % 12

  const parts = []
  if (years > 0) parts.push(`${years} yr${years > 1 ? 's' : ''}`)
  if (remainingMonths > 0) parts.push(`${remainingMonths} mo${remainingMonths > 1 ? 's' : ''}`)

  return parts.length > 0 ? `· ${parts.join(' ')}` : ''
})
</script>

<template>
  <div
    class="bg-white p-4 rounded-lg border border-gray-200 shadow-sm hover:shadow-md transition-shadow"
  >
    <div class="flex justify-between items-start">
      <div class="flex gap-3">
        <!-- Icon Placeholder -->
        <div
          class="mt-1 w-10 h-10 rounded-full bg-blue-50 flex items-center justify-center flex-shrink-0 text-blue-600"
        >
          <BriefcaseIcon class="w-6 h-6" />
        </div>

        <div>
          <!-- Title & Company -->
          <h3 class="text-lg font-bold text-gray-900">{{ experience.title }}</h3>
          <p class="text-base font-medium text-gray-700">{{ experience.company }}</p>

          <!-- Meta Data Row -->
          <div class="flex flex-wrap items-center gap-x-2 text-sm text-gray-500 mt-1">
            <span>{{ formattedDateRange }}</span>
            <span v-if="durationString" class="text-gray-400">{{ durationString }}</span>

            <template v-if="experience.location">
              <span class="text-gray-300">•</span>
              <span class="flex items-center gap-0.5">
                <MapPinIcon class="w-3.5 h-3.5" />
                {{ experience.location }}
              </span>
            </template>
          </div>

          <!-- Description -->
          <p
            v-if="experience.description"
            class="mt-3 text-sm text-gray-600 whitespace-pre-wrap leading-relaxed"
          >
            {{ experience.description }}
          </p>
        </div>
      </div>

      <!-- Action Buttons (Owner Only) -->
      <div v-if="isOwner" class="flex gap-2">
        <button
          @click="emit('edit', experience.id)"
          class="p-1.5 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-full transition-colors"
          title="Edit Experience"
        >
          <PencilIcon class="w-5 h-5" />
        </button>
        <button
          @click="emit('delete', experience.id)"
          class="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-full transition-colors"
          title="Delete Experience"
        >
          <TrashIcon class="w-5 h-5" />
        </button>
      </div>
    </div>
  </div>
</template>
