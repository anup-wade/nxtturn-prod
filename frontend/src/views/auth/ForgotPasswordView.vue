<template>
    <div class="flex flex-col items-center justify-center min-h-screen bg-gray-100 p-4">
        <div class="w-full max-w-md p-8 space-y-6 bg-white rounded-lg shadow-md">
            <div>
                <h2 class="text-2xl font-bold text-center text-gray-800">Forgot Your Password?</h2>
                <p class="mt-2 text-center text-gray-600">
                    No problem. Enter your email address below and we'll send you a link to reset it.
                </p>
            </div>

            <form @submit.prevent="handleRequestReset" class="space-y-6">
                <div v-if="successMessage" class="bg-green-100 border-l-4 border-green-500 text-green-700 p-4"
                    role="alert">
                    <p class="font-bold">Success</p>
                    <p>{{ successMessage }}</p>
                </div>

                <div v-if="errorMessage" class="bg-red-100 border-l-4 border-red-500 text-red-700 p-4" role="alert">
                    <p class="font-bold">Error</p>
                    <p>{{ errorMessage }}</p>
                </div>

                <div>
                    <label for="email" class="block text-sm font-medium text-gray-700">Email Address</label>
                    <div class="mt-1">
                        <input type="email" id="email" v-model="email" required :disabled="isLoading"
                            class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 disabled:bg-gray-50" />
                    </div>
                </div>

                <div>
                    <button type="submit" :disabled="isLoading"
                        class="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:bg-indigo-400 disabled:cursor-not-allowed">
                        {{ isLoading ? 'Sending...' : 'Send Reset Link' }}
                    </button>
                </div>
            </form>
            <p class="mt-6 text-center text-sm text-gray-600">
                Remembered your password?
                <router-link :to="{ name: 'login' }" class="font-medium text-indigo-600 hover:text-indigo-500">
                    Sign in
                </router-link>
            </p>
        </div>
    </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import axiosInstance from '@/services/axiosInstance';
import { useToast } from 'vue-toastification';

const email = ref('');
const isLoading = ref(false);
const errorMessage = ref<string | null>(null);
const successMessage = ref<string | null>(null);
const toast = useToast();

const handleRequestReset = async () => {
    isLoading.value = true;
    errorMessage.value = null;
    successMessage.value = null;

    try {
        const response = await axiosInstance.post('auth/password/reset/', {
            email: email.value,
        });

        // The API always returns a success message for security, as per our pytest test.
        successMessage.value = response.data.detail + " If an account with this email exists, you will receive instructions shortly.";
        toast.success("Password reset request sent successfully.");
        email.value = ''; // Clear the form on success

    } catch (error: any) {
        errorMessage.value = error.response?.data?.detail || 'An unexpected error occurred. Please try again.';
        toast.error(errorMessage.value);
    } finally {
        isLoading.value = false;
    }
};
</script>