<!-- C:\Users\Vinay\Project\frontend\src\components\profile\cards\LocationCard.vue -->
<!-- --- PASTE THIS INTO THE NEW FILE --- -->

<script setup lang="ts">
import { ref, computed } from 'vue'
import type { UserProfile, ProfileUpdatePayload } from '@/types'
import { useProfileStore } from '@/stores/profile'
import { PencilIcon, MapPinIcon, BriefcaseIcon, GlobeAltIcon } from '@heroicons/vue/24/solid'
import BaseModal from '@/components/common/BaseModal.vue'
import BaseButton from '@/components/common/BaseButton.vue'

const props = defineProps<{
  profile: UserProfile
  isOwnProfile: boolean
}>()

const profileStore = useProfileStore()
const isModalOpen = ref(false)
const isLoading = ref(false)

// Form state for the editing modal
const locationData = ref<ProfileUpdatePayload>({
  location_city: props.profile.location_city || '',
  location_administrative_area: props.profile.location_administrative_area || '',
  location_country: props.profile.location_country || '',
  current_work_style: props.profile.current_work_style || '',
  is_open_to_relocation: props.profile.is_open_to_relocation || false,
})

// A computed property to format the location for display, filtering out empty parts.
const displayLocation = computed(() => {
  return [
    props.profile.location_city,
    props.profile.location_administrative_area,
    props.profile.location_country,
  ]
    .filter(Boolean) // Removes any null, undefined, or empty strings
    .join(', ')
})

const workStyleDisplay = computed(() => {
  const styles = {
    on_site: 'On-Site',
    hybrid: 'Hybrid',
    remote: 'Remote',
  }
  const styleKey = props.profile.current_work_style
  return styleKey ? styles[styleKey] : ''
})

async function handleSaveChanges() {
  if (isLoading.value) return
  isLoading.value = true
  try {
    const payload: ProfileUpdatePayload = { ...locationData.value }
    await profileStore.updateProfile(props.profile.user.username, payload)
    isModalOpen.value = false
  } catch (error) {
    console.error('Failed to update location:', error)
  } finally {
    isLoading.value = false
  }
}

function openModal() {
  // Sync form data with the latest profile props when opening the modal
  locationData.value = {
    location_city: props.profile.location_city || '',
    location_administrative_area: props.profile.location_administrative_area || '',
    location_country: props.profile.location_country || '',
    current_work_style: props.profile.current_work_style || '',
    is_open_to_relocation: props.profile.is_open_to_relocation || false,
  }
  isModalOpen.value = true
}
</script>

<template>
  <div data-cy="location-card" class="bg-white rounded-lg shadow-md p-6 relative">
    <!-- Header -->
    <div class="flex justify-between items-center mb-4">
      <h3 class="text-xl font-bold text-gray-800">Location</h3>
      <button
        data-cy="edit-location-button"
        v-if="isOwnProfile"
        @click="openModal"
        class="text-gray-400 hover:text-blue-500 transition-colors"
        aria-label="Edit location"
      >
        <PencilIcon class="h-5 w-5" />
      </button>
    </div>

    <!-- Display -->
    <div class="space-y-4 text-gray-700">
      <div v-if="displayLocation" class="flex items-center">
        <MapPinIcon class="h-5 w-5 text-gray-400 mr-3 flex-shrink-0" />
        <span>{{ displayLocation }}</span>
      </div>

      <div v-if="workStyleDisplay" class="flex items-center">
        <BriefcaseIcon class="h-5 w-5 text-gray-400 mr-3 flex-shrink-0" />
        <span
          >Currently working <strong>{{ workStyleDisplay }}</strong></span
        >
      </div>

      <div v-if="profile.is_open_to_relocation" class="flex items-center">
        <GlobeAltIcon class="h-5 w-5 text-gray-400 mr-3 flex-shrink-0" />
        <span>Open to relocation</span>
      </div>

      <p
        v-if="!displayLocation && !workStyleDisplay && !profile.is_open_to_relocation"
        class="text-gray-500 italic"
      >
        No location information provided.
      </p>
    </div>

    <!-- Modal for Editing -->
    <BaseModal
      :show="isModalOpen"
      title="Edit Location & Work Preferences"
      @close="isModalOpen = false"
    >
      <div class="space-y-6">
        <!-- Physical Location -->
        <fieldset class="space-y-4">
          <legend class="text-base font-medium text-gray-900">Primary Location</legend>
          <div>
            <label for="country" class="block text-sm font-medium text-gray-700">Country</label>
            <input
              v-model="locationData.location_country"
              type="text"
              id="country"
              class="mt-1 w-full p-2 border border-gray-300 rounded-md"
            />
          </div>
          <div>
            <label for="state" class="block text-sm font-medium text-gray-700"
              >State / Province</label
            >
            <input
              v-model="locationData.location_administrative_area"
              type="text"
              id="state"
              class="mt-1 w-full p-2 border border-gray-300 rounded-md"
            />
          </div>
          <div>
            <label for="city" class="block text-sm font-medium text-gray-700">City</label>
            <input
              v-model="locationData.location_city"
              type="text"
              id="city"
              class="mt-1 w-full p-2 border border-gray-300 rounded-md"
            />
          </div>
        </fieldset>

        <!-- Work Preferences -->
        <fieldset class="space-y-4">
          <legend class="text-base font-medium text-gray-900">Work Preferences (Optional)</legend>
          <div>
            <label for="work-style" class="block text-sm font-medium text-gray-700"
              >Current Work Style</label
            >
            <select
              v-model="locationData.current_work_style"
              id="work-style"
              class="mt-1 w-full p-2 border border-gray-300 rounded-md"
            >
              <option value="">Not Applicable</option>
              <option value="on_site">On-Site</option>
              <option value="hybrid">Hybrid</option>
              <option value="remote">Remote</option>
            </select>
          </div>
          <div class="flex items-center">
            <input
              v-model="locationData.is_open_to_relocation"
              type="checkbox"
              id="relocation"
              class="h-4 w-4 text-blue-600 border-gray-300 rounded"
            />
            <label for="relocation" class="ml-2 block text-sm text-gray-900"
              >I'm open to relocation opportunities</label
            >
          </div>
        </fieldset>
      </div>

      <template #footer>
        <div class="flex justify-end space-x-3">
          <BaseButton @click="isModalOpen = false" variant="secondary">Cancel</BaseButton>
          <BaseButton @click="handleSaveChanges" :is-loading="isLoading">Save Changes</BaseButton>
        </div>
      </template>
    </BaseModal>
  </div>
</template>
