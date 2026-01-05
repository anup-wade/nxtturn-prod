<script setup lang="ts">
import { RouterLink, useRoute } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import { storeToRefs } from 'pinia';
import { getAvatarUrl } from '@/utils/avatars';
import { HomeIcon, UserGroupIcon, BookmarkIcon } from '@heroicons/vue/24/solid';
import eventBus from '@/services/eventBus';

const authStore = useAuthStore();
const { currentUser } = storeToRefs(authStore);
const route = useRoute();

function handleHomeFeedClick(event: MouseEvent) {
  if (route.path === '/') {
    event.preventDefault();
    eventBus.emit('scroll-to-top');
  }
}

// --- THIS IS THE CORRECTED FUNCTION ---
function handleMyGroupsClick(event: MouseEvent) {
  // Use the correct route name from your router file
  if (route.name === 'group-list') { 
    event.preventDefault();
    eventBus.emit('scroll-groups-to-top');
  }
}

function handleSavedPostsClick(event: MouseEvent) {
  if (route.name === 'saved-posts') {
    event.preventDefault();
    eventBus.emit('scroll-saved-posts-to-top');
  }
}
</script>

<template>
  <div class="space-y-4">
    <!-- Welcome Card -->
    <div v-if="currentUser" class="bg-white p-4 rounded-lg border border-gray-200 shadow-sm">
      <div class="flex items-start gap-4">
        <img :src="getAvatarUrl(currentUser.picture, currentUser.first_name, currentUser.last_name)" alt="User Avatar" class="h-12 w-12 rounded-full object-cover">
        <div>
          <h2 class="font-bold text-gray-800 text-lg">{{ currentUser.first_name }} {{ currentUser.last_name }}</h2>
          <p class="text-sm text-gray-500">@{{ currentUser.username }}</p>
        </div>
      </div>
    </div>

    <!-- Navigation Card -->
    <div class="bg-white p-4 rounded-lg border border-gray-200 shadow-sm">
      <nav class="space-y-1">
        <RouterLink 
          to="/" 
          @click="handleHomeFeedClick"
          data-cy="sidebar-home-link"
          class="flex items-center gap-3 px-3 py-2 rounded-md text-gray-700 hover:bg-gray-100 font-medium" 
          active-class="bg-blue-50 text-blue-700"
        >
          <HomeIcon class="h-6 w-6" />
          <span>Home Feed</span>
        </RouterLink>
        <RouterLink to="/groups" @click="handleMyGroupsClick" data-cy="sidebar-groups-link" class="flex items-center gap-3 px-3 py-2 rounded-md text-gray-700 hover:bg-gray-100 font-medium" active-class="bg-blue-50 text-blue-700">
          <UserGroupIcon class="h-6 w-6" />
          <span>My Groups</span>
        </RouterLink>
        <RouterLink to="/saved-posts" @click="handleSavedPostsClick" data-cy="sidebar-saved-posts-link" class="flex items-center gap-3 px-3 py-2 rounded-md text-gray-700 hover:bg-gray-100 font-medium" active-class="bg-blue-50 text-blue-700">
          <BookmarkIcon class="h-6 w-6" />
          <span>Saved Posts</span>
        </RouterLink>
      </nav>
    </div>
  </div>
</template>