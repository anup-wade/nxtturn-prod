<script setup lang="ts">
import type { UserProfile } from '@/types';
import { PencilIcon } from '@heroicons/vue/24/solid';

defineProps<{
    profile: UserProfile;
    isOwnProfile: boolean;
}>();
</script>

<template>
    <div class="bg-white rounded-lg shadow-md p-6 relative">
        <div class="flex justify-between items-center mb-4">
            <h3 class="text-xl font-bold text-gray-800">Contact Details</h3>
            <button v-if="isOwnProfile" class="text-gray-500 hover:text-gray-800" aria-label="Edit contact section">
                <PencilIcon class="h-5 w-5" />
            </button>
        </div>
        <div class="space-y-4 text-gray-700">
            <div>
                <dt class="text-sm font-medium text-gray-500">Email</dt>
                <dd class="mt-1">{{ profile.user.email }}</dd>
            </div>
            <div>
                <dt class="text-sm font-medium text-gray-500">Phone</dt>
                <dd class="mt-1 italic text-gray-500">Not provided</dd>
            </div>
        </div>
    </div>
</template>