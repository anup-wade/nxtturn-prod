// In CommunityLayout.vue
<script setup lang="ts">
import { RouterView } from 'vue-router';
import TopNavBar from '@/components/layout/TopNavBar.vue';
import CommunitySidebar from '@/components/layout/CommunitySidebar.vue';
import RightSidebar from '@/components/layout/RightSidebar.vue';
</script>

<template>
  <div class="bg-gray-50 min-h-screen">
    <TopNavBar />
    <main class="container mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 pt-20">
      <div class="grid grid-cols-12 gap-6 items-start">
        <aside class="col-span-3 hidden lg:block sticky top-20">
          <CommunitySidebar />
        </aside>
        <div class="col-span-12 lg:col-span-6 min-w-0">
          <!-- 
            This key binding ensures that when the URL changes, even if the
            same component is used (e.g., /profile/user1 -> /profile/user2),
            Vue will destroy the old component and create a new one.
            This prevents stale data within a single user session.
          -->
          <RouterView :key="$route.fullPath" />
        </div>
        <aside class="col-span-3 hidden lg:block sticky top-20">
          <RightSidebar />
        </aside>
      </div>
    </main>
  </div>
</template>