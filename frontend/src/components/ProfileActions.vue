<script setup lang="ts">
import { useProfileStore } from '@/stores/profile';
import { storeToRefs } from 'pinia';
import { ref, computed } from 'vue';

import {
    UserPlusIcon,
    ClockIcon,
    CheckCircleIcon,
    UserGroupIcon,
    HeartIcon as HeartIconOutline,
    ChatBubbleOvalLeftEllipsisIcon,
} from '@heroicons/vue/24/outline';
import { HeartIcon as HeartIconSolid } from '@heroicons/vue/24/solid';

const profileStore = useProfileStore();
const { relationshipStatus, currentProfile, isLoadingFollow } = storeToRefs(profileStore);

const showDisconnectConfirm = ref(false);

const followIcon = computed(() => {
    return relationshipStatus.value?.is_followed_by_request_user ? HeartIconSolid : HeartIconOutline;
});

const handleConnect = () => {
    if (currentProfile.value) {
        profileStore.sendConnectRequest(currentProfile.value.user.username);
    }
};

const handleAccept = () => {
    if (currentProfile.value) {
        profileStore.acceptConnectRequest(currentProfile.value.user.username);
    }
};

const handleFollowToggle = () => {
    if (currentProfile.value) {
        if (relationshipStatus.value?.is_followed_by_request_user) {
            profileStore.unfollowUser(currentProfile.value.user.username);
        } else {
            profileStore.followUser(currentProfile.value.user.username);
        }
    }
};

const handleDisconnect = () => {
    if (currentProfile.value) {
        profileStore.unfollowUser(currentProfile.value.user.username);
        showDisconnectConfirm.value = false;
    }
};

const handleMessage = () => {
    console.log("Messaging functionality to be implemented.");
};

</script>

<template>
    <div v-if="relationshipStatus" class="absolute top-4 right-4 flex items-center space-x-3">

        <!-- SLOT 1: CONNECT ICON -->
        <div class="relative text-center">
            <!-- State: Default -->
            <button v-if="relationshipStatus.connection_status === 'not_connected'" @click="handleConnect"
                data-cy="connect-button"
                class="flex flex-col items-center p-1 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors">
                <component :is="UserPlusIcon" class="w-5 h-5" />
                <span class="text-xs font-semibold mt-1">Connect</span>
            </button>

            <!-- State: Request Sent -->
            <button v-else-if="relationshipStatus.connection_status === 'request_sent'" disabled
                data-cy="pending-button" class="flex flex-col items-center p-1 text-gray-400 cursor-not-allowed">
                <component :is="ClockIcon" class="w-5 h-5" />
                <span class="text-xs font-semibold mt-1">Pending</span>
            </button>

            <!-- State: Request Received -->
            <button v-else-if="relationshipStatus.connection_status === 'request_received'" @click="handleAccept"
                data-cy="accept-request-button"
                class="flex flex-col items-center p-1 text-green-600 hover:bg-green-50 rounded-lg transition-colors">
                <component :is="CheckCircleIcon" class="w-5 h-5" />
                <span class="text-xs font-semibold mt-1">Accept</span>
            </button>

            <!-- State: Connected -->
            <div v-else-if="relationshipStatus.connection_status === 'connected'" class="relative">
                <button @click="showDisconnectConfirm = !showDisconnectConfirm" data-cy="connected-button"
                    class="flex flex-col items-center p-1 text-green-600 bg-green-50 rounded-lg">
                    <component :is="UserGroupIcon" class="w-5 h-5" />
                    <span class="text-xs font-semibold mt-1">Connected</span>
                </button>
                <div v-if="showDisconnectConfirm" @mouseleave="showDisconnectConfirm = false"
                    class="absolute top-full right-0 mt-2 w-40 bg-white border border-gray-200 rounded-lg shadow-xl z-10">
                    <button @click="handleDisconnect" data-cy="disconnect-button"
                        class="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50">
                        Disconnect
                    </button>
                </div>
            </div>
        </div>

        <!-- SLOT 2: FOLLOW ICON -->
        <div v-if="relationshipStatus.connection_status !== 'connected'" class="text-center">
            <button @click="handleFollowToggle" :disabled="isLoadingFollow" :class="[
                relationshipStatus.is_followed_by_request_user
                    ? 'text-green-600 hover:bg-green-50'
                    : 'text-gray-600 hover:bg-gray-100'
            ]" class="flex flex-col items-center p-1 rounded-lg transition-colors disabled:opacity-50"
                data-cy="follow-toggle-button">
                <component :is="followIcon" class="w-5 h-5" />
                <span class="text-xs font-semibold mt-1">
                    {{ relationshipStatus.is_followed_by_request_user ? 'Following' : 'Follow' }}
                </span>
            </button>
        </div>

        <!-- SLOT 3: MESSAGE ICON -->
        <div class="text-center">
            <button @click="handleMessage"
                class="flex flex-col items-center p-1 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
                data-cy="message-button">
                <component :is="ChatBubbleOvalLeftEllipsisIcon" class="w-5 h-5" />
                <span class="text-xs font-semibold mt-1">Message</span>
            </button>
        </div>
    </div>
</template>