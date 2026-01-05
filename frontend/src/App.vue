<!-- C:\Users\Vinay\Project\frontend\src\App.vue -->
<!-- FIXED AUTH INITIALIZATION -->
<script setup lang="ts">
import { watch, onMounted, onUnmounted } from 'vue';
import { RouterView, useRouter } from 'vue-router';
import { notificationService } from '@/services/notificationService';
import { useAuthStore } from '@/stores/auth';

const authStore = useAuthStore();
const router = useRouter();

// This watcher is correct. It will react to the auth state once
// the router has finished initializing it.
watch(() => authStore.isAuthenticated, (isNowAuthenticated) => {
  if (isNowAuthenticated) {
    console.log("Watcher Triggered: Auth state is TRUE. Connecting to WebSocket.");
    notificationService.connect();
  } else {
    console.log("Watcher Triggered: Auth state is FALSE. Disconnecting from WebSocket.");
    notificationService.disconnect();
  }
}, {
  immediate: true
});

const handleStorageChange = (event: StorageEvent) => {
  if (event.key === 'authToken' && !event.newValue) {
    console.log('Auth token removed in another tab. Forcing logout and redirect.');
    authStore.resetAuthState(); 
    router.push({ name: 'login' });
  }
};

onMounted(() => {
  // [THE FIX] Remove the initialization call from here.
  // The router's beforeEach guard is now the single source of truth for initialization.
  // authStore.initializeAuth(); <-- REMOVE THIS LINE

  window.addEventListener('storage', handleStorageChange);
});

onUnmounted(() => {
  window.removeEventListener('storage', handleStorageChange);
});
</script>

<template>
  <RouterView />
</template>