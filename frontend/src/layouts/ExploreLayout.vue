<script setup lang="ts">
import { RouterView } from 'vue-router';
import TopNavBar from '@/components/layout/TopNavBar.vue';
import FilterSidebar from '@/components/layout/FilterSidebar.vue';
</script>

<template>
  <div class="bg-gray-50 min-h-screen">
    <TopNavBar />

    <main class="container mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 pt-20">
      <!-- A 2-column grid for the Explore Hub -->
      <div class="grid grid-cols-12 gap-6 items-start">
        
        <!-- The new Filter Panel, sticky on the left -->
        <aside class="col-span-3 hidden lg:block sticky top-20">
          <FilterSidebar />
        </aside>
  
        <!-- The main results area -->
        <div class="col-span-12 lg:col-span-9 min-w-0">
          <RouterView />
        </div>
  
      </div>
    </main>
  </div>
</template>