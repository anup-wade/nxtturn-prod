<script setup lang="ts">
import { ref, computed } from 'vue';
import type { PropType } from 'vue';
import type { User } from '@/stores/auth'; // Assuming User interface is in auth store

// --- Props ---
// This component receives the list of members and the current creator's ID from its parent.
const props = defineProps({
  isOpen: {
    type: Boolean,
    required: true,
  },
  members: {
    type: Array as PropType<User[]>,
    required: true,
  },
  creatorId: {
    type: Number,
    required: true,
  },
  isSubmitting: {
    type: Boolean,
    default: false,
  },
});

// --- Emits ---
// It can emit two events: 'close' to tell the parent to close it, and 'submit'
// with the ID of the user to transfer ownership to.
const emit = defineEmits<{
  (e: 'close'): void;
  (e: 'submit', newOwnerId: number): void;
}>();

// --- State ---
// This holds the ID of the member selected from the dropdown.
const selectedOwnerId = ref<number | null>(null);

// --- Computed ---
// This creates a filtered list of members that can be transferred to.
// Crucially, it removes the current creator from the list.
const transferableMembers = computed(() => {
  return props.members.filter(member => member.id !== props.creatorId);
});

// --- Methods ---
function handleSubmit() {
  if (selectedOwnerId.value) {
    emit('submit', selectedOwnerId.value);
  }
}

function handleClose() {
  emit('close');
}
</script>

<template>
  <!-- Modal Overlay -->
  <div
    v-if="isOpen"
    class="fixed inset-0 z-40 bg-black bg-opacity-60 flex items-center justify-center"
    @click.self="handleClose"
  >
    <!-- Modal Panel -->
    <div class="bg-white rounded-lg shadow-2xl p-6 w-full max-w-md z-50">
      
      <!-- Modal Header -->
      <div class="mb-4">
        <h2 class="text-xl font-bold text-gray-800">Transfer Group Ownership</h2>
        <p class="text-sm text-gray-500 mt-1">
          Select a new owner for this group. This action is irreversible.
        </p>
      </div>

      <!-- Form Content -->
      <form @submit.prevent="handleSubmit">
        <div class="space-y-4">
          <!-- Member Selection Dropdown -->
          <div>
            <label for="new-owner" class="block text-sm font-medium text-gray-700">New Owner</label>
            <select
              id="new-owner"
              v-model="selectedOwnerId"
              class="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md"
            >
              <option disabled :value="null">-- Please select a member --</option>
              <option v-for="member in transferableMembers" :key="member.id" :value="member.id">
                {{ member.username }} ({{ member.first_name }} {{ member.last_name }})
              </option>
            </select>
            <p v-if="transferableMembers.length === 0" class="text-xs text-gray-500 mt-1">
              There are no other members to transfer ownership to.
            </p>
          </div>
        </div>

        <!-- Action Buttons -->
        <div class="mt-6 flex justify-end space-x-3">
          <button
            type="button"
            @click="handleClose"
            class="px-4 py-2 bg-gray-200 text-gray-800 rounded-md hover:bg-gray-300 transition-colors"
          >
            Cancel
          </button>
          <button
            type="submit"
            :disabled="!selectedOwnerId || isSubmitting || transferableMembers.length === 0"
            :class="[
              'px-4 py-2 text-white rounded-md transition-colors',
              !selectedOwnerId || transferableMembers.length === 0 ? 'bg-blue-300 cursor-not-allowed' : 'bg-blue-600 hover:bg-blue-700',
              isSubmitting ? 'bg-blue-400 opacity-75' : ''
            ]"
          >
            {{ isSubmitting ? 'Transferring...' : 'Transfer Ownership' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>