<!-- C:\Users\Vinay\Project\frontend\src/components/profile/cards/BioCard.vue -->
<!-- --- THIS IS THE COMPLETE, CORRECTED CONTENT --- -->

<script setup lang="ts">
import { ref } from 'vue'
import type { UserProfile, ProfileUpdatePayload } from '@/types'
import { useProfileStore } from '@/stores/profile'
import { PencilIcon } from '@heroicons/vue/24/solid'
import BaseModal from '@/components/common/BaseModal.vue'
import BaseButton from '@/components/common/BaseButton.vue'

const props = defineProps<{
  profile: UserProfile
  isOwnProfile: boolean
}>()

const profileStore = useProfileStore()
const isModalOpen = ref(false)
const isLoading = ref(false)

// Use a separate ref for the form data to avoid directly mutating the prop
const bioData = ref({
  bio: props.profile.bio || '',
})

async function handleSaveChanges() {
  if (isLoading.value) return
  isLoading.value = true
  try {
    const payload: ProfileUpdatePayload = {
      bio: bioData.value.bio,
    }
    await profileStore.updateProfile(props.profile.user.username, payload)
    isModalOpen.value = false
  } catch (error) {
    console.error('Failed to update bio:', error)
    // You can add a user-facing error message here
  } finally {
    isLoading.value = false
  }
}

function openModal() {
  // When opening the modal, sync the form data with the latest profile prop
  bioData.value.bio = props.profile.bio || ''
  isModalOpen.value = true
}
</script>

<template>
  <div data-cy="bio-card" class="bg-white rounded-lg shadow-md p-6 relative">
    <!-- Header -->
    <div class="flex justify-between items-center mb-4">
      <h3 class="text-xl font-bold text-gray-800">Bio</h3>
      <button
        data-cy="edit-bio-button"
        v-if="isOwnProfile"
        @click="openModal"
        class="text-gray-400 hover:text-blue-500 transition-colors"
        aria-label="Edit bio"
      >
        <PencilIcon class="h-5 w-5" />
      </button>
    </div>

    <!-- Display -->
    <div class="text-gray-700">
      <p v-if="profile.bio" class="whitespace-pre-wrap">{{ profile.bio }}</p>
      <p v-else class="text-gray-500 italic">No bio available.</p>
    </div>

    <!-- Modal for Editing -->
    <BaseModal :show="isModalOpen" title="Edit Bio" @close="isModalOpen = false">
      <div class="space-y-4">
        <label for="bio-textarea" class="block text-sm font-medium text-gray-700">Your Bio</label>
        <textarea
          id="bio-textarea"
          v-model="bioData.bio"
          rows="6"
          class="w-full p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
          placeholder="Tell us a little about yourself..."
        ></textarea>
      </div>

      <!-- Modal Footer with Actions -->
      <template #footer>
        <div class="flex justify-end space-x-3">
          <BaseButton @click="isModalOpen = false" variant="secondary"> Cancel </BaseButton>
          <BaseButton @click="handleSaveChanges" :is-loading="isLoading"> Save Changes </BaseButton>
        </div>
      </template>
    </BaseModal>
  </div>
</template>
