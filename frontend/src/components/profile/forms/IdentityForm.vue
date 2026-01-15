<script setup lang="ts">
import { ref, watch } from 'vue';
import type { UserProfile } from '@/types';

// Define the shape of the data for this specific form.
// Bio has been REMOVED from this form.
type IdentityFormData = {
    display_name: string | null;
    headline: string | null;
};

const props = defineProps<{
    initialData: UserProfile;
}>();

const emit = defineEmits(['save', 'cancel']);

const form = ref<IdentityFormData>({
    display_name: '',
    headline: '',
});

// Watch for changes to pre-fill the form.
// Bio has been REMOVED from this logic.
watch(() => props.initialData, (newData) => {
    if (newData) {
        form.value = {
            display_name: newData.display_name || '',
            headline: newData.headline || '',
        };
    }
}, { immediate: true });

function handleSubmit() {
    emit('save', form.value);
}
</script>

<template>
    <form @submit.prevent="handleSubmit">
        <div class="space-y-4">
            <!-- Display Name -->
            <div>
                <label for="display_name" class="block text-sm font-medium text-gray-700">Display Name</label>
                <input v-model="form.display_name" type="text" id="display_name" placeholder="e.g., Vinay S."
                    class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500" />
            </div>

            <!-- Headline -->
            <div>
                <label for="headline" class="block text-sm font-medium text-gray-700">Headline</label>
                <input v-model="form.headline" type="text" id="headline"
                    placeholder="e.g., Computer Science Student | Aspiring AI Engineer"
                    class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500" />
            </div>

            <!-- The Bio textarea has been completely REMOVED from this template -->

        </div>

        <!-- Form Actions -->
        <div class="mt-6 flex justify-end space-x-3">
            <button type="button" @click="$emit('cancel')"
                class="px-4 py-2 bg-white border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 hover:bg-gray-50">
                Cancel
            </button>
            <button type="submit"
                class="px-4 py-2 bg-blue-600 border border-transparent rounded-md shadow-sm text-sm font-medium text-white hover:bg-blue-700">
                Save Changes
            </button>
        </div>
    </form>
</template>