<script setup lang="ts">
import { RouterView } from 'vue-router';
import TopNavBar from '@/components/layout/TopNavBar.vue';
</script>

<template>
  <div class="bg-gray-50 min-h-screen">
    <TopNavBar />
    <!-- 
      This RouterView will render the ProfileView.vue, which contains
      its own internal layout. We will add padding to that view next.
    -->
    <RouterView />
  </div>
</template>