<script setup lang="ts">
import { useRoute, useRouter, RouterLink } from 'vue-router';
import { onMounted, computed, ref } from 'vue';
import { useGroupStore } from '@/stores/group';
import { useAuthStore } from '@/stores/auth';
import { storeToRefs } from 'pinia';
import { formatDistanceToNow } from 'date-fns';
import defaultAvatar from '@/assets/images/default-avatar.svg';

const route = useRoute();
const router = useRouter();
const groupStore = useGroupStore();
const authStore = useAuthStore();

const activeTab = ref<'requests' | 'blocked'>('requests');
const openDropdowns = ref<Map<number, boolean>>(new Map());

const {
  joinRequests,
  isLoadingRequests,
  requestsError,
  isManagingRequest,
  manageRequestError,
  currentGroup,
  blockedUsers,
  isLoadingBlockedUsers,
  blockedUsersError
} = storeToRefs(groupStore);

const { currentUser } = storeToRefs(authStore);

const isCreator = computed(() => {
  return currentUser.value && currentGroup.value && currentUser.value.id === currentGroup.value.creator.id;
});

onMounted(async () => {
  const slug = route.params.slug as string;
  if (!currentGroup.value || currentGroup.value.slug !== slug) {
    await groupStore.fetchGroupDetails(slug);
  }
  if (!isCreator.value) {
    router.push({ name: 'group-detail', params: { slug } });
    return;
  }
  await groupStore.fetchJoinRequests(slug);
  await groupStore.fetchBlockedUsers(slug);
});

async function handleApprove(requestId: number) {
  const slug = route.params.slug as string;
  await groupStore.manageJoinRequest(slug, requestId, 'approve');
  openDropdowns.value.set(requestId, false);
}

async function handleDeny(requestId: number) {
  const slug = route.params.slug as string;
  await groupStore.manageJoinRequest(slug, requestId, 'deny');
  openDropdowns.value.set(requestId, false);
}

async function handleDenyAndBlock(requestId: number) {
  if (confirm('Are you sure you want to deny this user and permanently block them from re-requesting?')) {
    const slug = route.params.slug as string;
    await groupStore.manageJoinRequest(slug, requestId, 'deny_and_block');
  }
  openDropdowns.value.set(requestId, false);
}

async function handleUnblock(userId: number) {
  if (confirm('Are you sure you want to unblock this user? They will be able to request to join the group again.')) {
    const slug = route.params.slug as string;
    await groupStore.unblockUser(slug, userId);
  }
}

function toggleDropdown(requestId: number) {
  const currentState = openDropdowns.value.get(requestId) || false;
  openDropdowns.value.set(requestId, !currentState);
}

function formatTimestamp(dateString: string) {
  return formatDistanceToNow(new Date(dateString), { addSuffix: true });
}
</script>

<template>
  <div class="max-w-4xl mx-auto">
    <header class="bg-white p-4 rounded-lg shadow-sm border border-gray-200 mb-6">
      <RouterLink v-if="currentGroup" :to="{ name: 'group-detail', params: { slug: currentGroup.slug } }" class="text-sm text-blue-600 hover:underline">
        &larr; Back to {{ currentGroup.name }}
      </RouterLink>
      <h1 class="text-2xl font-bold text-gray-800 mt-1">
        Manage Group Members
      </h1>
      <div class="border-b border-gray-200 mt-4">
        <nav class="-mb-px flex space-x-6" aria-label="Tabs">
          <button @click="activeTab = 'requests'" :class="[
            'whitespace-nowrap py-3 px-1 border-b-2 font-medium text-sm',
            activeTab === 'requests'
              ? 'border-blue-500 text-blue-600'
              : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300',
          ]">
            Pending Requests ({{ joinRequests.length }})
          </button>
          <button @click="activeTab = 'blocked'" :class="[
            'whitespace-nowrap py-3 px-1 border-b-2 font-medium text-sm',
            activeTab === 'blocked'
              ? 'border-blue-500 text-blue-600'
              : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300',
          ]">
            Blocked Users ({{ blockedUsers.length }})
          </button>
        </nav>
      </div>
    </header>

    <!-- PENDING REQUESTS TAB CONTENT -->
    <div v-if="activeTab === 'requests'">
      <div v-if="isLoadingRequests" class="text-center py-10">Loading...</div>
      <div v-else-if="requestsError" class="bg-red-100 p-4 rounded-md text-red-700">{{ requestsError }}</div>
      <div v-else-if="joinRequests.length === 0" class="bg-white p-6 rounded-lg shadow-md text-center">
        <p class="text-gray-500">There are no pending join requests.</p>
      </div>
      <!-- ================================================================================= -->
      <!-- THIS ENTIRE 'v-else' BLOCK WAS MISSING ITS CONTENT. IT IS NOW RESTORED. -->
      <!-- ================================================================================= -->
      <div v-else class="bg-white rounded-lg shadow-md divide-y divide-gray-200">
        <div v-for="request in joinRequests" :key="request.id" class="p-4 flex items-center justify-between">
          <div class="flex items-center space-x-4">
            <img :src="request.user.picture || defaultAvatar" alt="User avatar" class="w-12 h-12 rounded-full object-cover">
            <div>
              <RouterLink :to="{ name: 'profile', params: { username: request.user.username } }" class="font-bold text-gray-800 hover:underline">
                {{ request.user.username }}
              </RouterLink>
              <p class="text-sm text-gray-500">
                Requested {{ formatTimestamp(request.created_at) }}
              </p>
            </div>
          </div>
          <div class="flex items-center space-x-2">
            <button @click="handleApprove(request.id)" :disabled="isManagingRequest" class="px-4 py-1.5 bg-green-600 text-white text-sm font-semibold rounded-full hover:bg-green-700 disabled:opacity-50 disabled:cursor-wait transition-colors">
              Approve
            </button>
            <div class="relative inline-block text-left">
              <div>
                <button @click="toggleDropdown(request.id)" :disabled="isManagingRequest" class="px-4 py-1.5 bg-red-600 text-white text-sm font-semibold rounded-full hover:bg-red-700 disabled:opacity-50 disabled:cursor-wait transition-colors flex items-center">
                  Deny
                  <svg class="w-4 h-4 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path></svg>
                </button>
              </div>
              <div v-if="openDropdowns.get(request.id)" class="origin-top-right absolute right-0 mt-2 w-48 rounded-md shadow-lg bg-white ring-1 ring-black ring-opacity-5 z-10">
                <div class="py-1" role="menu" aria-orientation="vertical">
                  <a href="#" @click.prevent="handleDeny(request.id)" class="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100" role="menuitem">
                    Deny Request
                    <p class="text-xs text-gray-500">User can request to join again later.</p>
                  </a>
                  <a href="#" @click.prevent="handleDenyAndBlock(request.id)" class="block px-4 py-2 text-sm text-red-700 hover:bg-red-50" role="menuitem">
                    Deny & Block User
                    <p class="text-xs text-red-500">User will be blocked permanently.</p>
                  </a>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- BLOCKED USERS TAB CONTENT -->
    <div v-if="activeTab === 'blocked'">
      <div v-if="isLoadingBlockedUsers" class="text-center py-10">Loading...</div>
      <div v-else-if="blockedUsersError" class="bg-red-100 p-4 rounded-md text-red-700">{{ blockedUsersError }}</div>
      <div v-else-if="blockedUsers.length === 0" class="bg-white p-6 rounded-lg shadow-md text-center">
        <p class="text-gray-500">There are no users blocked from this group.</p>
      </div>
      <div v-else class="bg-white rounded-lg shadow-md divide-y divide-gray-200">
        <div v-for="block in blockedUsers" :key="block.id" class="p-4 flex items-center justify-between">
          <div class="flex items-center space-x-4">
            <img :src="block.user.picture || defaultAvatar" alt="User avatar" class="w-12 h-12 rounded-full object-cover">
            <div>
              <RouterLink :to="{ name: 'profile', params: { username: block.user.username } }" class="font-bold text-gray-800 hover:underline">
                {{ block.user.username }}
              </RouterLink>
              <p class="text-sm text-gray-500">
                Blocked {{ formatTimestamp(block.created_at) }}
              </p>
            </div>
          </div>
          <button @click="handleUnblock(block.user.id)" class="px-4 py-1.5 bg-gray-200 text-gray-800 text-sm font-semibold rounded-full hover:bg-gray-300 transition-colors">
            Unblock
          </button>
        </div>
      </div>
    </div>
  </div>
</template>