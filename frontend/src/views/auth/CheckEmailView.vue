<template>
    <div class="flex flex-col items-center justify-center min-h-screen bg-gray-100 p-4">
        <div class="w-full max-w-md p-8 space-y-6 bg-white rounded-lg shadow-md text-center">
            <div>
                <h2 class="text-2xl font-bold text-gray-800">Please Verify Your Email</h2>
                <p class="mt-2 text-gray-600">
                    We have sent a verification link to your email address. Please click the link to complete your
                    registration.
                </p>
            </div>
            <div class="mt-6">
                <p class="text-sm text-gray-500">
                    Didn't receive the email? Check your spam folder or
                    <button @click="resendVerification" :disabled="isResending"
                        class="text-indigo-600 hover:underline disabled:opacity-50 disabled:cursor-not-allowed">
                        resend the verification link
                    </button>.
                </p>
                <p class="mt-4 text-sm">
                    <router-link :to="{ name: 'login' }" class="font-medium text-blue-600 hover:text-blue-500">
                        Back to Login
                    </router-link>
                </p>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useToast } from 'vue-toastification';
import { useRouter } from 'vue-router'; // Import useRouter

const toast = useToast();
const router = useRouter(); // Initialize router
const isResending = ref(false);

const resendVerification = () => {
    isResending.value = true;
    // NOTE: The resend functionality is not yet built in the backend.
    // This is a placeholder for a future feature.
    setTimeout(() => {
        toast.info("Resend functionality is not yet implemented.");
        isResending.value = false;
    }, 1000);
};
</script>