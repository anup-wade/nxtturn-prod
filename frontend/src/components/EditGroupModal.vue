<script setup lang="ts">
import { ref, watch, computed } from 'vue';
import type { Group } from '@/stores/group'; // Assuming you have a Group type defined

interface Props {
  isOpen: boolean;
  isSubmitting: boolean;
  group: Group | null;
}
const props = withDefaults(defineProps<Props>(), {
  isOpen: false,
  isSubmitting: false,
  group: null,
});

const emit = defineEmits(['close', 'submit']);

const editableGroup = ref({ name: '', description: '' });

// When the modal opens, populate the form with the group's current data
watch(() => props.group, (newGroup) => {
  if (newGroup) {
    editableGroup.value.name = newGroup.name;
    editableGroup.value.description = newGroup.description || '';
  }
}, { immediate: true });

const isFormValid = computed(() => {
  return editableGroup.value.name.trim().length > 0;
});

function handleSubmit() {
  if (isFormValid.value && !props.isSubmitting) {
    emit('submit', { ...editableGroup.value });
  }
}
</script>

<template>
  <div v-if="isOpen" class="fixed inset-0 bg-black bg-opacity-50 z-40 flex justify-center items-center"
    @click.self="emit('close')">
    <div class="bg-white rounded-lg shadow-xl p-6 w-full max-w-md">
      <h2 class="text-xl font-bold text-gray-800 mb-4">Edit Group Details</h2>

      <form @submit.prevent="handleSubmit">
        <div class="mb-4">
          <label for="group-name" class="block text-sm font-medium text-gray-700">Group Name</label>
          <input id="group-name" v-model="editableGroup.name" type="text" required
            class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500" />
        </div>

        <div class="mb-6">
          <label for="group-description" class="block text-sm font-medium text-gray-700">Description</label>
          <textarea id="group-description" v-model="editableGroup.description" rows="4"
            class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"></textarea>
        </div>

        <div class="flex justify-end space-x-3">
          <button type="button" @click="emit('close')"
            class="px-4 py-2 bg-gray-200 text-gray-800 rounded-md hover:bg-gray-300">
            Cancel
          </button>
          <button type="submit" :disabled="!isFormValid || isSubmitting"
            :class="['px-4 py-2 text-white rounded-md',
              isFormValid && !isSubmitting ? 'bg-blue-600 hover:bg-blue-700' : 'bg-blue-300 cursor-not-allowed'
            ]">
            {{ isSubmitting ? 'Saving...' : 'Save Changes' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>