<!-- C:\Users\Vinay\Project\frontend\src\components\CreateGroupFormModal.vue -->

<script setup lang="ts">
import { ref, watch, computed } from 'vue';
import { useGroupStore } from '@/stores/group';
import { useAuthStore } from '@/stores/auth';
// --- THIS IS THE FIX (Part 1 of 3) ---
// Import the Group type to use in our event definition.
import type { Group } from '@/stores/group';

// --- Component Props ---
const props = defineProps({
  isOpen: {
    type: Boolean,
    required: true,
  },
});

// --- Component Emits ---
// --- THIS IS THE FIX (Part 2 of 3) ---
// Update the 'group-created' event to emit a full 'Group' object, not just a number.
const emit = defineEmits<{
  (e: 'close'): void;
  (e: 'group-created', newGroup: Group): void;
}>();

// --- Pinia Stores ---
const groupStore = useGroupStore();
const authStore = useAuthStore();

// --- Local State ---
const groupData = ref({
  name: '',
  description: '',
  privacy_level: 'public' as 'public' | 'private',
});

const localError = ref('');

const isCreatingGroup = computed(() => groupStore.isCreatingGroup);
const createGroupError = computed(() => groupStore.createGroupError);

const errorMessages = computed(() => {
  const errors: { name: string; description: string; privacy_level: string } = { name: '', description: '', privacy_level: '' };
  const backendError = groupStore.createGroupError;

  if (typeof backendError === 'string') {
      try {
          const parsedError = JSON.parse(backendError);
          if (parsedError.name?.[0]) errors.name = parsedError.name[0];
          if (parsedError.description?.[0]) errors.description = parsedError.description[0];
          if (parsedError.privacy_level?.[0]) errors.privacy_level = parsedError.privacy_level[0];
      } catch (e) {
        // Not a JSON string, will be handled by the general error display.
      }
  } else if (backendError && typeof backendError === 'object') {
      const errObj = backendError as any; 
      if (errObj.name?.[0]) errors.name = errObj.name[0];
      if (errObj.description?.[0]) errors.description = errObj.description[0];
      if (errObj.privacy_level?.[0]) errors.privacy_level = errObj.privacy_level[0];
  }
  return errors;
});


// --- Methods ---
watch(() => props.isOpen, (newVal) => {
  if (newVal) {
    resetForm();
  }
});

function handleClose() {
  emit('close');
  resetForm(); 
}

function resetForm() {
  groupData.value = { 
    name: '',
    description: '',
    privacy_level: 'public',
  };
  localError.value = '';
  groupStore.createGroupError = null;
}

// --- THIS IS THE FIX (Part 3 of 3) ---
async function handleSubmit() {
  if (!groupData.value.name.trim()) {
    localError.value = 'Group name is required.';
    return;
  }
  if (!groupData.value.description.trim()) {
    localError.value = 'Group description is required.';
    return;
  }
  groupStore.createGroupError = null;
  localError.value = ''; 
    
  // Call the store action. The variable is now correctly named `newGroup`
  // as it holds the full Group object returned from the store.
  const newGroup = await groupStore.createGroup(groupData.value);

  if (newGroup) {
    // On success, emit the event with the complete `newGroup` object.
    emit('group-created', newGroup); 
  }
  // On failure, the error is handled by the computed properties and displayed in the form.
}

</script>

<template>
  <div v-if="isOpen" class="fixed inset-0 bg-black bg-opacity-50 z-40 flex items-center justify-center p-4" @click.self="handleClose">
    <div class="bg-white rounded-lg shadow-xl w-full max-w-md" @click.stop>
      <div class="p-6">
        <div class="flex justify-between items-center mb-4">
          <h2 class="text-xl font-bold text-gray-800">Create New Group</h2>
          <button @click="handleClose" class="text-gray-400 hover:text-gray-600">×</button>
        </div>

        <form @submit.prevent="handleSubmit" class="space-y-4">
          <!-- Group Name -->
          <div>
            <label for="group-name" class="block text-sm font-medium text-gray-700">Group Name</label>
            <input
              data-cy="group-name-input" 
              type="text" 
              id="group-name" 
              v-model="groupData.name" 
              required 
              class="mt-1 w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              placeholder="e.g., Python Developers"
            />
            <p v-if="errorMessages.name" class="text-red-500 text-xs mt-1">{{ errorMessages.name }}</p>
          </div>

          <!-- Group Description -->
          <div>
            <label for="group-description" class="block text-sm font-medium text-gray-700">Description</label>
            <textarea
              data-cy="group-description-input"
              id="group-description"
              v-model="groupData.description"
              rows="3"
              class="mt-1 w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              placeholder="Briefly describe your group's purpose"
            ></textarea>
            <p v-if="errorMessages.description" class="text-red-500 text-xs mt-1">{{ errorMessages.description }}</p>
          </div>

          <!-- Privacy Level Selection -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">Privacy Level</label>
            <div class="flex items-center space-x-4">
              <div>
                <input 
                  data-cy="privacy-private-radio"
                  type="radio" 
                  id="privacyPublic" 
                  value="public" 
                  v-model="groupData.privacy_level" 
                  class="form-radio h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300"
                >
                <label for="privacyPublic" class="ml-2 block text-sm font-medium text-gray-700">Public</label>
                <p class="text-xs text-gray-500">Anyone can view and join.</p>
              </div>
              <div>
                <input 
                  type="radio" 
                  id="privacyPrivate" 
                  value="private" 
                  v-model="groupData.privacy_level" 
                  class="form-radio h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300"
                >
                <label for="privacyPrivate" class="ml-2 block text-sm font-medium text-gray-700">Private</label>
                <p class="text-xs text-gray-500">Only members can view; requires approval.</p>
              </div>
            </div>
            <p v-if="errorMessages.privacy_level" class="text-red-500 text-xs mt-1">{{ errorMessages.privacy_level }}</p>
          </div>

          <!-- General Error Message Display -->
          <div v-if="localError" class="bg-red-100 border-l-4 border-red-500 text-red-700 p-3 text-sm">
            <p>{{ localError }}</p>
          </div>

          <div class="pt-4 flex justify-end gap-3">
            <button type="button" @click="handleClose" class="px-4 py-2 bg-gray-200 text-gray-800 rounded-md hover:bg-gray-300">
              Cancel
            </button>
            <button 
              data-cy="create-group-submit-button"
              type="submit" 
              :disabled="isCreatingGroup" 
              class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {{ isCreatingGroup ? 'Creating...' : 'Create Group' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>