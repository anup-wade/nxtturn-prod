<script setup lang="ts">
import type { UserProfile } from '@/types';
import { ArrowDownTrayIcon, PencilIcon } from '@heroicons/vue/24/solid';
import { ref } from 'vue';

defineProps<{
    profile: UserProfile;
    isOwnProfile: boolean;
}>();

const fileInput = ref<HTMLInputElement | null>(null);

function triggerFileUpload() {
    fileInput.value?.click();
}

function handleFileChange(event: Event) {
    const target = event.target as HTMLInputElement;
    const file = target.files?.[0];
    if (file) {
        // TODO: This will call a profileStore action to upload the file.
        console.log('File selected for upload:', file);
        // After a successful upload, the profile data will refresh and show the new link.
    }
}
</script>

<template>
    <div class="bg-white rounded-lg shadow-md p-6">
        <div class="flex justify-between items-center mb-4 pb-4 border-b">
            <h3 class="text-xl font-bold text-gray-800">Resume / CV</h3>
            <!-- The "Edit" button now triggers the file input -->
            <button v-if="isOwnProfile" @click="triggerFileUpload"
                class="text-gray-400 hover:text-blue-500 transition-colors duration-200"
                aria-label="Upload or replace resume">
                <PencilIcon class="h-5 w-5" />
            </button>
            <!-- Hidden file input that we trigger programmatically -->
            <input v-if="isOwnProfile" type="file" ref="fileInput" @change="handleFileChange" class="hidden"
                accept=".pdf,.doc,.docx" />
        </div>

        <!-- Conditional Content: Show download link or placeholder -->
        <div v-if="profile.resume" class="mt-4">
            <a :href="profile.resume" target="_blank" rel="noopener noreferrer"
                class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500">
                <ArrowDownTrayIcon class="h-5 w-5 mr-2" />
                Download Resume
            </a>
        </div>

        <div v-else class="text-center text-gray-500 py-8">
            <p>No resume has been uploaded yet.</p>
        </div>
    </div>
</template>