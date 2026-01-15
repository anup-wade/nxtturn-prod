<script setup lang="ts">
import { ref, computed } from 'vue';
import { useAuthStore } from '@/stores/auth';
import { useRouter } from 'vue-router';
import type { AxiosError } from 'axios';
import { storeToRefs } from 'pinia';
import { useToast } from 'vue-toastification';

const authStore = useAuthStore();
const router = useRouter();
const toast = useToast();

const { isLoading } = storeToRefs(authStore);
const email = ref('');
const username = ref('');
const password = ref('');
const password2 = ref('');
const errorMessage = ref<string | null>(null);

// --- START: Added state for password visibility ---
const showPassword1 = ref(false);
const showPassword2 = ref(false);
// --- END: Added state for password visibility ---

const passwordsMismatch = computed(() => {
  return password.value && password2.value && password.value !== password2.value;
});

const isSubmitDisabled = computed(() => {
  return isLoading.value || passwordsMismatch.value;
});

const parseError = (error: unknown): string => {
  const axiosError = error as AxiosError<Record<string, string[]>>;
  if (axiosError.response?.data) {
    const errorMessages = Object.entries(axiosError.response.data)
      .map(([field, messages]) => `${field}: ${messages.join(', ')}`)
      .join('; ');
    if (axiosError.response.data.non_field_errors) {
      return axiosError.response.data.non_field_errors.join('; ');
    }
    return errorMessages;
  }
  return 'An unexpected error occurred during registration.';
};

const handleRegister = async () => {
  errorMessage.value = null;

  if (passwordsMismatch.value) {
    errorMessage.value = 'Passwords do not match.';
    return;
  }

  try {
    await authStore.register({
      email: email.value,
      username: username.value,
      password1: password.value, // This is correct, no change needed
      password2: password2.value, // This is correct, no change needed
    });
    toast.success('Registration successful! Please check your email to verify your account.');
    router.push({ name: 'CheckEmail' });
  } catch (error) {
    errorMessage.value = parseError(error);
  }
};
</script>

<template>
  <div class="flex items-center justify-center min-h-[calc(100vh-150px)] bg-gray-50">
    <div class="w-full max-w-md p-8 space-y-6 bg-white rounded-lg shadow-md">
      <h1 class="text-2xl font-bold text-center text-gray-900">Create your account</h1>

      <form @submit.prevent="handleRegister" class="space-y-6">

        <div v-if="errorMessage" class="bg-red-100 border-l-4 border-red-500 text-red-700 p-4" role="alert">
          <p class="font-bold">Error</p>
          <p>{{ errorMessage }}</p>
        </div>

        <div>
          <label for="email" class="block text-sm font-medium text-gray-700">Email</label>
          <div class="mt-1">
            <input type="email" id="email" v-model="email" required
              class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500" />
          </div>
        </div>

        <div>
          <label for="username" class="block text-sm font-medium text-gray-700">Username</label>
          <div class="mt-1">
            <input type="text" id="username" v-model="username" required
              class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500" />
          </div>
        </div>

        <div>
          <label for="password" class="block text-sm font-medium text-gray-700">Password</label>
          <!-- START: Modified password input -->
          <div class="mt-1 relative">
            <input :type="showPassword1 ? 'text' : 'password'" id="password" v-model="password" required
              class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500" />
            <button type="button" @click="showPassword1 = !showPassword1"
              class="absolute inset-y-0 right-0 flex items-center px-3 text-gray-500 hover:text-gray-700"
              aria-label="Toggle password visibility">
              <svg v-if="showPassword1" xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none"
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
          <!-- END: Modified password input -->
        </div>

        <div>
          <label for="password2" class="block text-sm font-medium text-gray-700">Confirm Password</label>
          <!-- START: Modified confirm password input -->
          <div class="mt-1 relative">
            <input :type="showPassword2 ? 'text' : 'password'" id="password2" v-model="password2" required
              class="w-full px-3 py-2 border rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500"
              :class="passwordsMismatch ? 'border-red-500' : 'border-gray-300'" />
            <button type="button" @click="showPassword2 = !showPassword2"
              class="absolute inset-y-0 right-0 flex items-center px-3 text-gray-500 hover:text-gray-700"
              aria-label="Toggle password visibility">
              <svg v-if="showPassword2" xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none"
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
          <!-- END: Modified confirm password input -->
          <p v-if="passwordsMismatch" class="mt-2 text-xs text-red-600">
            Passwords do not match.
          </p>
        </div>

        <div>
          <button type="submit" :disabled="Boolean(isSubmitDisabled)"
            class="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:bg-blue-300 disabled:cursor-not-allowed">
            {{ isLoading ? 'Registering...' : 'Create Account' }}
          </button>
        </div>
      </form>

      <p class="mt-6 text-center text-sm text-gray-600">
        Already have an account?
        <router-link :to="{ name: 'login' }" class="font-medium text-blue-600 hover:text-blue-500">
          Sign in
        </router-link>
      </p>
    </div>
  </div>
</template>