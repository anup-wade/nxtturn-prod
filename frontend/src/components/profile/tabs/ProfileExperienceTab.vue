<script setup lang="ts">
import { ref, computed } from 'vue'
import { useProfileStore } from '@/stores/profile'
import { useAuthStore } from '@/stores/auth'
import ExperienceCard from '../cards/ExperienceCard.vue'
import ExperienceForm from '../forms/ExperienceForm.vue'
import BaseModal from '@/components/common/BaseModal.vue'
import { PlusIcon } from '@heroicons/vue/24/solid'
import type { Experience } from '@/types'
import { useToast } from 'vue-toastification'

const profileStore = useProfileStore()
const authStore = useAuthStore()
const toast = useToast()

// --- Computed State ---
const experienceList = computed(() => profileStore.currentProfile?.experience || [])
const isOwner = computed(
  () => authStore.currentUser?.username === profileStore.currentProfile?.user.username,
)

// --- Modal State ---
const showModal = ref(false)
const editingItem = ref<Experience | null>(null)
const isSubmitting = ref(false)

// --- Actions ---
const openAddModal = () => {
  editingItem.value = null // null means "Add Mode"
  showModal.value = true
}

const openEditModal = (id: number) => {
  const item = experienceList.value.find((e) => e.id === id)
  if (item) {
    editingItem.value = JSON.parse(JSON.stringify(item)) // Deep copy to avoid mutation
    showModal.value = true
  }
}

const closeModal = () => {
  showModal.value = false
  editingItem.value = null
}

const handleSave = async (payload: Omit<Experience, 'id'>) => {
  if (!profileStore.currentProfile) return

  isSubmitting.value = true
  try {
    if (editingItem.value) {
      // Update
      await profileStore.updateExperience(
        profileStore.currentProfile.user.username,
        editingItem.value.id,
        payload,
      )
      toast.success('Experience updated successfully')
    } else {
      // Create
      await profileStore.addExperience(profileStore.currentProfile.user.username, payload)
      toast.success('Experience added successfully')
    }
    closeModal()
  } catch (error: any) {
    toast.error(error.message || 'Failed to save experience')
  } finally {
    isSubmitting.value = false
  }
}

const handleDelete = async (id: number) => {
  if (!confirm('Are you sure you want to delete this experience entry?')) return
  if (!profileStore.currentProfile) return

  try {
    await profileStore.deleteExperience(profileStore.currentProfile.user.username, id)
    toast.success('Experience deleted')
  } catch (error: any) {
    toast.error(error.message || 'Failed to delete experience')
  }
}
</script>

<template>
  <div data-cy="experience-tab-content" class="space-y-4">
    <!-- Header / Add Button -->
    <div v-if="isOwner" class="flex justify-end">
      <button
        @click="openAddModal"
        class="flex items-center gap-2 px-4 py-2 bg-blue-50 text-blue-600 rounded-lg hover:bg-blue-100 font-medium transition-colors"
      >
        <PlusIcon class="w-5 h-5" />
        Add Experience
      </button>
    </div>

    <!-- Empty State -->
    <div
      v-if="experienceList.length === 0"
      class="text-center py-12 bg-gray-50 rounded-lg border border-dashed border-gray-300"
    >
      <p class="text-gray-500">No experience added yet.</p>
    </div>

    <!-- List -->
    <div v-else class="space-y-4">
      <ExperienceCard
        v-for="item in experienceList"
        :key="item.id"
        :experience="item"
        :is-owner="isOwner"
        @edit="openEditModal"
        @delete="handleDelete"
      />
    </div>

    <!-- Add/Edit Modal -->
    <BaseModal
      :show="showModal"
      @close="closeModal"
      :title="editingItem ? 'Edit Experience' : 'Add Experience'"
    >
      <ExperienceForm
        :initial-data="editingItem"
        :is-submitting="isSubmitting"
        @submit="handleSave"
        @cancel="closeModal"
      />
    </BaseModal>
  </div>
</template>
