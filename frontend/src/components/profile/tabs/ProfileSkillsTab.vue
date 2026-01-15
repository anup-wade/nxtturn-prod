<script setup lang="ts">
import type { UserProfile, Skill } from '@/types';
import { PlusIcon, TrashIcon } from '@heroicons/vue/24/solid';

defineProps<{
    profile: UserProfile;
    isOwnProfile: boolean;
}>();

// --- Placeholder functions for future CRUD operations ---
function handleAddSkill() {
    // TODO: This will open a modal to add a new skill.
    console.log('Open modal to add skill');
}

function handleDeleteSkill(skillId: number) {
    // TODO: This will show a confirmation and then make an API call to delete.
    console.log('Trigger delete for skill ID:', skillId);
}
</script>

<template>
    <div class="bg-white rounded-lg shadow-md p-6">
        <!-- Header Section with "Add" button for owner -->
        <div class="flex justify-between items-center mb-4 pb-4 border-b">
            <h3 class="text-xl font-bold text-gray-800">Skills</h3>
            <button v-if="isOwnProfile" @click="handleAddSkill"
                class="p-1 rounded-full text-gray-400 hover:bg-gray-100 hover:text-blue-500 transition-colors duration-200"
                aria-label="Add new skill">
                <PlusIcon class="h-6 w-6" />
            </button>
        </div>

        <!-- Conditional Content: Show list or placeholder -->
        <div v-if="profile.skills && profile.skills.length > 0">
            <ul class="flex flex-wrap gap-2">
                <!-- Looping through an array of objects now -->
                <li v-for="skill in profile.skills" :key="skill.id"
                    class="flex items-center bg-gray-200 text-gray-800 text-sm font-medium px-3 py-1 rounded-full">
                    <!-- Displaying the 'name' property of the skill object -->
                    <span>{{ skill.name }}</span>

                    <!-- Delete button for owner -->
                    <button v-if="isOwnProfile" @click="handleDeleteSkill(skill.id)"
                        class="ml-2 text-gray-500 hover:text-red-500 transition-colors duration-200"
                        aria-label="Delete skill">
                        <TrashIcon class="h-3 w-3" />
                    </button>
                </li>
            </ul>
        </div>

        <!-- Placeholder when no skills exist -->
        <div v-else class="text-center text-gray-500 py-8">
            <p>No skills have been added yet.</p>
        </div>
    </div>
</template>