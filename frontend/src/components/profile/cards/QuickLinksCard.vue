<!-- C:\Users\Vinay\Project\frontend\src\components\profile\cards\QuickLinksCard.vue -->
<!-- --- THIS IS THE FINAL, COMPLETE REPLACEMENT --- -->

<script setup lang="ts">
import { ref } from 'vue'
import type { UserProfile, SocialLink, ProfileUpdatePayload } from '@/types'
import { useProfileStore } from '@/stores/profile'
import { PencilIcon, TrashIcon } from '@heroicons/vue/24/solid'
import BaseModal from '@/components/common/BaseModal.vue'
import BaseButton from '@/components/common/BaseButton.vue'
import BrandIcon from '@/components/icons/BrandIcon.vue' // <-- Import our new component

interface EditableLink {
  id?: number
  link_type: SocialLink['link_type']
  url: string
}

const props = defineProps<{
  profile: UserProfile
  isOwnProfile: boolean
}>()

const profileStore = useProfileStore()
const isModalOpen = ref(false)
const isLoading = ref(false)

const editableLinks = ref<EditableLink[]>([])

const linkOptions = [
  { value: 'linkedin', text: 'LinkedIn' },
  { value: 'github', text: 'GitHub' },
  { value: 'twitter', text: 'Twitter' },
  { value: 'portfolio', text: 'Personal Portfolio' },
]

function openModal() {
  editableLinks.value = props.profile.social_links?.map((link) => ({ ...link })) || []
  isModalOpen.value = true
}

function addLink() {
  editableLinks.value.push({ link_type: 'linkedin', url: '' })
}

function removeLink(index: number) {
  editableLinks.value.splice(index, 1)
}

async function handleSaveChanges() {
  if (isLoading.value) return
  isLoading.value = true
  try {
    const linksToSave: Omit<SocialLink, 'id'>[] = editableLinks.value
      .filter((link) => link.url && link.url.trim() !== '')
      .map((link) => ({
        link_type: link.link_type,
        url: link.url,
      }))

    const payload: ProfileUpdatePayload = { social_links: linksToSave }
    await profileStore.updateProfile(props.profile.user.username, payload)
    isModalOpen.value = false
  } catch (error) {
    console.error('Failed to update social links:', error)
  } finally {
    isLoading.value = false
  }
}
</script>

<template>
  <div data-cy="quick-links-card" class="bg-white rounded-lg shadow-md p-6 relative">
    <!-- Header -->
    <div class="flex justify-between items-center mb-4">
      <h3 class="text-xl font-bold text-gray-800">Quick Links</h3>
      <button
        data-cy="edit-quick-links-button"
        v-if="isOwnProfile"
        @click="openModal"
        class="text-gray-400 hover:text-blue-500 transition-colors"
        aria-label="Edit quick links"
      >
        <PencilIcon class="h-5 w-5" />
      </button>
    </div>

    <!-- POLISHED Display Section with Icons -->
    <div v-if="profile.social_links && profile.social_links.length > 0" class="space-y-3">
      <a
        v-for="link in profile.social_links"
        :key="link.id"
        :href="link.url"
        target="_blank"
        rel="noopener noreferrer"
        class="flex items-center p-3 -m-3 rounded-lg hover:bg-gray-50 transition-colors group"
      >
        <!-- Icon -->
        <div
          class="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-lg bg-gray-100 text-gray-600 group-hover:bg-blue-500 group-hover:text-white transition-colors"
        >
          <BrandIcon :type="link.link_type" />
        </div>
        <!-- Text -->
        <div class="ml-4">
          <p class="text-base font-medium text-gray-900">
            {{ linkOptions.find((o) => o.value === link.link_type)?.text || 'Link' }}
          </p>
          <p class="mt-1 text-sm text-gray-500 break-all">
            {{ link.url }}
          </p>
        </div>
      </a>
    </div>
    <p v-else class="text-gray-500 italic">No links provided.</p>

    <!-- Modal (Unchanged) -->
    <BaseModal :show="isModalOpen" title="Edit Quick Links" @close="isModalOpen = false">
      <div class="space-y-4 max-h-96 overflow-y-auto pr-2">
        <div
          v-for="(link, index) in editableLinks"
          :key="index"
          class="p-4 border rounded-md relative"
        >
          <button
            data-cy="remove-link-button"
            @click="removeLink(index)"
            aria-label="Remove link"
            class="absolute top-2 right-2 text-gray-400 hover:text-red-500"
          >
            <TrashIcon class="h-5 w-5" />
          </button>
          <div class="space-y-3">
            <div>
              <label :for="`link-type-${index}`" class="block text-sm font-medium text-gray-700"
                >Type</label
              >
              <select
                :id="`link-type-${index}`"
                v-model="link.link_type"
                class="mt-1 w-full p-2 border border-gray-300 rounded-md"
              >
                <option v-for="option in linkOptions" :key="option.value" :value="option.value">
                  {{ option.text }}
                </option>
              </select>
            </div>
            <div>
              <label :for="`link-url-${index}`" class="block text-sm font-medium text-gray-700"
                >URL</label
              >
              <input
                :id="`link-url-${index}`"
                v-model="link.url"
                type="url"
                placeholder="https://..."
                class="mt-1 w-full p-2 border border-gray-300 rounded-md"
              />
            </div>
          </div>
        </div>
        <BaseButton @click="addLink" variant="secondary" class="w-full">
          + Add another link
        </BaseButton>
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
