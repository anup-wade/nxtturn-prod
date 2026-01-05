<script setup lang="ts">
import { ref, watch } from 'vue'
import { getAvatarUrl } from '@/utils/avatars'
import type { UserProfile } from '@/types'
import { useProfileStore } from '@/stores/profile'
import ProfileActions from '@/components/ProfileActions.vue'
import BaseModal from '@/components/common/BaseModal.vue'
import IdentityForm from '@/components/profile/forms/IdentityForm.vue'
import { PencilIcon } from '@heroicons/vue/24/solid'

const props = defineProps<{
  profile: UserProfile
  isOwnProfile: boolean
}>()

const profileStore = useProfileStore()
const isModalOpen = ref(false)
type IdentityFormData = {
  display_name: string | null
  headline: string | null
}
const selectedFile = ref<File | null>(null)
const picturePreviewUrl = ref<string | null>(null)
const isUploadingPicture = ref(false)
const isRemovingPicture = ref(false)
const showPictureOptions = ref(false)
const pictureOptionsRef = ref<HTMLDivElement | null>(null)

async function handleSaveChanges(formData: IdentityFormData) {
  try {
    await profileStore.updateProfile(props.profile.user.username, formData)
    isModalOpen.value = false
  } catch (error) {
    console.error('Failed to update profile:', error)
    alert('Could not update profile. Please try again.')
  }
}
function handleFileChange(event: Event) {
  const file = (event.target as HTMLInputElement).files?.[0]
  if (file) {
    selectedFile.value = file
    picturePreviewUrl.value = URL.createObjectURL(file)
    showPictureOptions.value = false
    uploadProfilePicture()
  }
}
async function uploadProfilePicture() {
  if (!selectedFile.value) return
  isUploadingPicture.value = true
  try {
    await profileStore.updateProfilePicture(props.profile.user.username, selectedFile.value)
    selectedFile.value = null
    picturePreviewUrl.value = null
  } catch (error: any) {
    alert(error.message || 'Failed to upload picture.')
    selectedFile.value = null
    picturePreviewUrl.value = null
  } finally {
    isUploadingPicture.value = false
  }
}
async function handleRemovePicture() {
  if (window.confirm('Are you sure you want to remove your profile picture?')) {
    isRemovingPicture.value = true
    try {
      await profileStore.removeProfilePicture(props.profile.user.username)
    } catch (error) {
      alert('Failed to remove profile picture.')
    } finally {
      isRemovingPicture.value = false
    }
  }
}
const closeOnClickOutside = (event: MouseEvent) => {
  if (pictureOptionsRef.value && !pictureOptionsRef.value.contains(event.target as Node)) {
    showPictureOptions.value = false
  }
}
watch(showPictureOptions, (isOpen) => {
  if (isOpen) document.addEventListener('click', closeOnClickOutside)
  else document.removeEventListener('click', closeOnClickOutside)
})
</script>

<template>
  <div data-cy="profile-card-container" class="bg-white rounded-lg shadow-md p-6 relative">
    <ProfileActions v-if="!isOwnProfile" />
    <button
      v-if="isOwnProfile"
      @click="isModalOpen = true"
      class="absolute top-4 right-4 p-2 rounded-full text-gray-400 hover:bg-gray-100 hover:text-blue-500 transition-colors"
      aria-label="Edit profile summary"
    >
      <PencilIcon class="h-5 w-5" />
    </button>

    <!-- 
            --- FIX #1: VERTICAL ALIGNMENT ---
            Changed 'items-start' to 'items-end' to align the text block with the
            bottom of the profile picture.
        -->
    <div class="flex flex-row items-end space-x-6 py-8">
      <!-- COLUMN 1: Profile Picture -->
      <div
        data-cy="profile-picture-container"
        class="relative w-32 h-32 group flex-shrink-0"
        ref="pictureOptionsRef"
      >
        <img
          data-cy="profile-picture-img"
          :src="
            picturePreviewUrl ||
            getAvatarUrl(profile.picture, profile.user.first_name, profile.user.last_name)
          "
          alt="Profile Picture"
          class="w-full h-full rounded-full object-cover border-4 border-white shadow-lg bg-gray-200"
        />

        <div
          v-if="isOwnProfile"
          @click.stop="showPictureOptions = !showPictureOptions"
          class="absolute inset-0 rounded-full bg-black bg-opacity-0 group-hover:bg-opacity-40 flex items-center justify-center cursor-pointer transition-opacity duration-300"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            class="h-8 w-8 text-white opacity-0 group-hover:opacity-100 transition-opacity duration-300"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            stroke-width="2"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z"
            />
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              d="M15 13a3 3 0 11-6 0 3 3 0 016 0z"
            />
          </svg>
        </div>

        <div
          v-if="showPictureOptions"
          class="origin-top-left absolute left-0 mt-2 w-56 rounded-md shadow-lg bg-white ring-1 ring-black ring-opacity-5 focus:outline-none z-10"
        >
          <ul class="py-1">
            <li>
              <label
                for="picture-upload"
                class="flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 cursor-pointer"
              >
                Upload a photo
              </label>
              <input
                id="picture-upload"
                type="file"
                @change="handleFileChange"
                accept="image/*"
                class="hidden"
              />
            </li>
            <li v-if="profile.picture">
              <button
                data-cy="remove-picture-button"
                @click.stop="handleRemovePicture"
                :disabled="isRemovingPicture"
                class="flex items-center w-full px-4 py-2 text-sm text-red-600 hover:bg-red-50 disabled:opacity-50"
              >
                Remove photo
              </button>
            </li>
          </ul>
        </div>
      </div>

      <!-- COLUMN 2: Name, Username, Headline -->
      <!-- 
                --- FIX #2: TEXT ALIGNMENT ---
                Changed 'text-left' to 'text-center' to center the text.
            -->
      <div class="text-center">
        <!-- 
                    --- FIX #3: FONT SIZE ---
                    Changed 'text-2xl' to 'text-xl' to make the font smaller.
                -->
        <h1 class="text-xl font-bold text-gray-800">
          {{ profile.display_name || `${profile.user.first_name} ${profile.user.last_name}` }}
        </h1>
        <p class="text-md text-gray-500">@{{ profile.user.username }}</p>
        <p v-if="profile.headline" class="mt-2 text-md text-gray-600">
          {{ profile.headline }}
        </p>
      </div>
    </div>

    <BaseModal :show="isModalOpen" title="Edit Profile Summary" @close="isModalOpen = false">
      <IdentityForm
        :initial-data="profile"
        @save="handleSaveChanges"
        @cancel="isModalOpen = false"
      />
    </BaseModal>
  </div>
</template>
