<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import axiosInstance from '@/services/axiosInstance';
import { useToast } from 'vue-toastification';

const route = useRoute();
const router = useRouter();
const toast = useToast();

const newPassword1 = ref('');
const newPassword2 = ref('');
const isLoading = ref(false);
const errorMessage = ref<string | null>(null);
const successMessage = ref<string | null>(null);

// State for the password visibility toggles
const showPassword1 = ref(false);
const showPassword2 = ref(false);

const uid = ref<string | string[]>('');
const token = ref<string | string[]>('');

onMounted(() => {
    uid.value = route.params.uid;
    token.value = route.params.token;
});

const handleResetConfirm = async () => {
    if (newPassword1.value !== newPassword2.value) {
        errorMessage.value = 'Passwords do not match.';
        toast.error('Passwords do not match.');
        return;
    }

    isLoading.value = true;
    errorMessage.value = null;

    try {
        const payload = {
            uid: uid.value,
            token: token.value,
            new_password1: newPassword1.value,
            new_password2: newPassword2.value,
        };

        await axiosInstance.post('auth/password/reset/confirm/', payload);

        toast.success("Your password has been reset successfully! Redirecting to login...");

        setTimeout(() => {
            router.push({ name: 'login' });
        }, 2000);

    } catch (error: any) {
        const errorData = error.response?.data;
        if (errorData) {
            errorMessage.value = Object.values(errorData).flat().join(' ');
        } else {
            errorMessage.value = 'An unexpected error occurred. The link may be invalid or expired.';
        }
        toast.error(errorMessage.value);
    } finally {
        isLoading.value = false;
    }
};
</script>

<template>
    <div class="flex flex-col items-center justify-center min-h-screen bg-gray-100 p-4">
        <div class="w-full max-w-md p-8 space-y-6 bg-white rounded-lg shadow-md">
            <div>
                <h2 class="text-2xl font-bold text-center text-gray-800">Choose a New Password</h2>
            </div>

            <form @submit.prevent="handleResetConfirm" class="space-y-6">
                <div v-if="successMessage" class="bg-green-100 border-l-4 border-green-500 text-green-700 p-4"
                    role="alert">
                    <p class="font-bold">Success!</p>
                    <p>{{ successMessage }} You can now <router-link :to="{ name: 'login' }"
                            class="font-bold underline">log in</router-link>.</p>
                </div>

                <div v-if="errorMessage" class="bg-red-100 border-l-4 border-red-500 text-red-700 p-4" role="alert">
                    <p class="font-bold">Error</p>
                    <p>{{ errorMessage }}</p>
                </div>

                <template v-if="!successMessage">
                    <div>
                        <label for="new_password1" class="block text-sm font-medium text-gray-700">New Password</label>
                        <div class="mt-1 relative">
                            <input :type="showPassword1 ? 'text' : 'password'" id="new_password1" v-model="newPassword1"
                                required class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm" />
                            <button type="button" @click="showPassword1 = !showPassword1"
                                class="absolute inset-y-0 right-0 flex items-center px-3 text-gray-500 hover:text-gray-700"
                                aria-label="Toggle password visibility">
                                <svg v-if="showPassword1" xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none"
                                    viewBox="0 0 24 24" stroke="currentColor">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                        d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a9.97 9.97 0 01-1.563 3.029m-2.177-4.573A3 3 0 0012 9.5m-3.955 3.955A3 3 0 0012 14.5M3 3l18 18" />
                                </svg>
                                <svg v-else xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none"
                                    viewBox="0 0 24 24" stroke="currentColor">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                        d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                        d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                                </svg>
                            </button>
                        </div>
                    </div>

                    <div>
                        <label for="new_password2" class="block text-sm font-medium text-gray-700">Confirm New
                            Password</label>
                        <div class="mt-1 relative">
                            <input :type="showPassword2 ? 'text' : 'password'" id="new_password2" v-model="newPassword2"
                                required class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm" />
                            <button type="button" @click="showPassword2 = !showPassword2"
                                class="absolute inset-y-0 right-0 flex items-center px-3 text-gray-500 hover:text-gray-700"
                                aria-label="Toggle password visibility">
                                <svg v-if="showPassword2" xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none"
                                    viewBox="0 0 24 24" stroke="currentColor">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                        d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a9.97 9.97 0 01-1.563 3.029m-2.177-4.573A3 3 0 0012 9.5m-3.955 3.955A3 3 0 0012 14.5M3 3l18 18" />
                                </svg>
                                <svg v-else xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none"
                                    viewBox="0 0 24 24" stroke="currentColor">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                        d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                        d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                                </svg>
                            </button>
                        </div>
                    </div>

                    <div>
                        <button type="submit" :disabled="isLoading"
                            class="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-400">
                            {{ isLoading ? 'Resetting...' : 'Reset Password' }}
                        </button>
                    </div>
                </template>
            </form>
        </div>
    </div>
</template>