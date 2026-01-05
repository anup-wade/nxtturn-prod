<script setup lang="ts">
import { ref } from 'vue';
import { useAuthStore } from '@/stores/auth';
import { useRouter } from 'vue-router';

const username = ref('');
const password = ref('');
const errorMessage = ref<string | null>(null);
const showPassword = ref(false);
// --- CHANGE 1: Add a new state variable to control the message box style ---
const messageType = ref<'error' | 'info'>('error');

const authStore = useAuthStore();
const router = useRouter();

const togglePasswordVisibility = () => {
  showPassword.value = !showPassword.value;
};

const handleLogin = async () => {
  errorMessage.value = null;
  // Reset message type to default on every new attempt
  messageType.value = 'error';
  try {
    await authStore.login({
      username: username.value,
      password: password.value,
    });
    // On success, navigate to the feed
    router.push({ name: 'feed' });
  } catch (error: any) {
    // --- CHANGE 2: Updated error handling logic ---
    const errors = error?.response?.data?.non_field_errors;
    if (errors && Array.isArray(errors)) {
      const errorString = errors.join(' ');

      // Check for our specific unverified email error
      if (errorString.includes('E-mail is not verified.')) {
        errorMessage.value = 'Your account is not verified. A new verification link has been sent to your email.';
        messageType.value = 'info'; // Set message type to 'info' for a blue box
      } else {
        // Handle other backend errors (e.g., wrong password)
        errorMessage.value = errorString;
      }
    } else {
      // Fallback for network errors or unexpected responses
      errorMessage.value = 'Login failed. Please check your credentials or network connection.';
    }
  }
};
</script>

<template>
  <div class="flex items-center justify-center min-h-[calc(100vh-150px)] bg-gray-50">
    <div class="w-full max-w-md p-8 space-y-6 bg-white rounded-lg shadow-md">
      <h1 class="text-2xl font-bold text-center text-gray-900">Sign in to your account</h1>

      <form @submit.prevent="handleLogin" class="space-y-6">
        <div>
          <label for="username" class="block text-sm font-medium text-gray-700">Username or Email</label>
          <div class="mt-1">
            <input type="text" id="username" v-model="username" required
              class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500" />
          </div>
        </div>

        <div>
          <label for="password" class="block text-sm font-medium text-gray-700">Password</label>
          <div class="mt-1 relative">
            <input :type="showPassword ? 'text' : 'password'" id="password" v-model="password" required
              class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500" />
            <button type="button" @click="togglePasswordVisibility"
              class="absolute inset-y-0 right-0 flex items-center px-3 text-gray-500 hover:text-gray-700"
              aria-label="Toggle password visibility">
              <!-- SVG icons for password visibility (unchanged) -->
              <svg v-if="showPassword" xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none"
                viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a9.97 9.97 0 01-1.563 3.029m-2.177-4.573A3 3 0 0012 9.5m-3.955 3.955A3 3 0 0012 14.5M3 3l18 18" />
              </svg>
              <svg v-else xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24"
                stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
              </svg>
            </button>
          </div>
        </div>

        <div class="flex items-center justify-end">
          <div class="text-sm">
            <router-link :to="{ name: 'ForgotPassword' }" class="font-medium text-blue-600 hover:text-blue-500">
              Forgot your password?
            </router-link>
          </div>
        </div>

        <!-- --- CHANGE 3: The alert box now uses dynamic classes --- -->
        <div v-if="errorMessage" :class="{
          'bg-red-100 border-l-4 border-red-500 text-red-700 p-4': messageType === 'error',
          'bg-blue-100 border-l-4 border-blue-500 text-blue-700 p-4': messageType === 'info'
        }" role="alert" data-cy="login-message-box">
          <p>{{ errorMessage }}</p>
        </div>

        <div>
          <button type="submit" :disabled="authStore.isLoading"
            class="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:bg-blue-300">
            {{ authStore.isLoading ? 'Signing in...' : 'Sign in' }}
          </button>
        </div>
      </form>

      <p class="mt-6 text-center text-sm text-gray-600">
        Not a member?
        <router-link :to="{ name: 'register' }" class="font-medium text-blue-600 hover:text-blue-500">
          Create an account
        </router-link>
      </p>
    </div>
  </div>
</template>