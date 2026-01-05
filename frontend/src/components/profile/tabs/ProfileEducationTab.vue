<!-- C:\Users\Vinay\Project\frontend\src\components\profile\tabs\ProfileEducationTab.vue -->
<!-- --- THIS IS THE REFACTORED AND SIMPLIFIED VERSION --- -->

<script setup lang="ts">
import { ref, computed } from 'vue'
import type { UserProfile, EducationEntry } from '@/types'
import { PlusIcon } from '@heroicons/vue/24/solid'

import BaseModal from '@/components/common/BaseModal.vue'
import EducationForm from '@/components/profile/forms/EducationForm.vue'
// IMPORT THE NEW CHILD COMPONENT
import EducationCard from '@/components/profile/cards/EducationCard.vue'
import { useProfileStore } from '@/stores/profile'

const props = defineProps<{
  profile: UserProfile
  isOwnProfile: boolean
}>()

const profileStore = useProfileStore()

const editingEducation = ref<EducationEntry | null>(null)
const isModalOpen = ref(false)

const modalTitle = computed(() => {
  return editingEducation.value ? 'Edit Education' : 'Add Education'
})

function openAddModal() {
  editingEducation.value = null
  isModalOpen.value = true
}

// This function now just opens the modal
function openEditModal(educationItem: EducationEntry) {
  editingEducation.value = educationItem
  isModalOpen.value = true
}

function closeModal() {
  isModalOpen.value = false
  editingEducation.value = null
}

async function handleSaveEducation(formData: Omit<EducationEntry, 'id'>) {
  try {
    const username = props.profile.user.username
    if (editingEducation.value) {
      await profileStore.updateEducation(username, editingEducation.value.id, formData)
    } else {
      await profileStore.addEducation(username, formData)
    }
    closeModal()
  } catch (error) {
    console.error('Failed to save education:', error)
    alert('Could not save education details. Please try again.')
  }
}

// The handleDeleteEducation function has been REMOVED from this file.
</script>

<template>
  <div class="bg-white rounded-lg shadow-md p-6">
    <!-- Header Section (Unchanged) -->
    <div class="flex justify-between items-center mb-4 pb-4 border-b">
      <h3 class="text-xl font-bold text-gray-800">Education</h3>
      <button
        v-if="isOwnProfile"
        @click="openAddModal"
        class="p-1 rounded-full text-gray-400 hover:bg-gray-100 hover:text-blue-500 transition-colors duration-200"
        aria-label="Add new education"
      >
        <PlusIcon class="h-6 w-6" />
      </button>
    </div>

    <!-- Education List (Now much cleaner) -->
    <div v-if="profile.education && profile.education.length > 0">
      <ul class="space-y-6">
        <!-- THE LOOP IS NOW VERY SIMPLE -->
        <EducationCard
          v-for="item in profile.education"
          :key="item.id"
          :education-entry="item"
          :is-own-profile="isOwnProfile"
          @edit="openEditModal"
        />
      </ul>
    </div>

    <!-- Placeholder (Unchanged) -->
    <div v-else class="text-center text-gray-500 py-8">
      <p>No education information has been added yet.</p>
    </div>

    <!-- Modal (Unchanged) -->
    <BaseModal :show="isModalOpen" :title="modalTitle" @close="closeModal">
      <EducationForm
        :initial-data="editingEducation"
        @save="handleSaveEducation"
        @cancel="closeModal"
      />
    </BaseModal>
  </div>
</template>
