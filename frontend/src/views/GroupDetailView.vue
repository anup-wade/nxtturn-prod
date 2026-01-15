<script setup lang="ts">
import { watch, computed, ref, onUnmounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useGroupStore } from '@/stores/group';
import { useAuthStore } from '@/stores/auth';
import { usePostsStore } from '@/stores/posts';
import { useInfiniteScroll } from '@/composables/useInfiniteScroll';
import { storeToRefs } from 'pinia';
import { useToast } from 'vue-toastification';
import CreatePostForm from '@/components/CreatePostForm.vue';
import PostItem from '@/components/PostItem.vue';
import TransferOwnershipModal from '@/components/TransferOwnershipModal.vue';
import EditGroupModal from '@/components/EditGroupModal.vue';

const route = useRoute();
const router = useRouter();
const groupStore = useGroupStore();
const authStore = useAuthStore();
const postsStore = usePostsStore();
const toast = useToast();

const isTransferModalOpen = ref(false);
const isEditModalOpen = ref(false);

const {
  currentGroup, isLoadingGroup, groupError, isJoiningLeaving,
  joinLeaveError, isLoadingGroupPosts, isDeletingGroup,
  isTransferringOwnership, isUpdatingGroup,
} = storeToRefs(groupStore);

const { isAuthenticated, currentUser } = storeToRefs(authStore);
const loadMoreGroupPostsTrigger = ref<HTMLElement | null>(null);

const groupSlug = computed(() => route.params.slug as string);

const groupPosts = computed(() => {
  const ids = groupStore.postIdsByGroupSlug[groupSlug.value] || [];
  return postsStore.getPostsByIds(ids);
});

const groupPostsNextCursor = computed(() => {
  return groupStore.nextCursorByGroupSlug[groupSlug.value];
});

const isCreator = computed(() => currentGroup.value?.membership_status === 'creator');
const isMember = computed(() => ['creator', 'member'].includes(currentGroup.value?.membership_status || ''));
const hasPendingRequest = computed(() => currentGroup.value?.membership_status === 'pending');

// THIS IS THE NEW, FIXED CODE
async function loadGroupData() {
  const slug = route.params.slug as string;
  if (slug) {
    groupStore.joinLeaveError = null;

    // First, get the group details. This is correct.
    await groupStore.fetchGroupDetails(slug);

    // NEW: Check if the user is a member OR if the group is public.
    // Only then try to get the posts. This prevents the state from being overwritten.
    const canViewPosts =
      groupStore.currentGroup?.membership_status === 'member' ||
      groupStore.currentGroup?.membership_status === 'creator' ||
      groupStore.currentGroup?.privacy_level === 'public';

    if (canViewPosts) {
      groupStore.refreshGroupPosts(slug);
    }
  }
}

watch(() => route.params.slug, (newSlug, oldSlug) => {
  if (newSlug && newSlug !== oldSlug) {
    groupStore.resetCurrentGroupState();
    loadGroupData();
  }
}, { immediate: true });

onUnmounted(() => {
  document.removeEventListener('click', closeOnClickOutside, true);
  groupStore.resetCurrentGroupState();
});

const joinButtonText = computed(() => {
  if (isJoiningLeaving.value) return 'Processing...';
  // Derive text directly from the single source of truth
  switch (currentGroup.value?.membership_status) {
    case 'pending': return 'Request Sent';
    case 'blocked': return 'Blocked';
    case 'member': case 'creator': return 'Leave Group'; // Handled by menu, but good for consistency
    default:
      return currentGroup.value?.privacy_level === 'private' ? 'Request to Join' : 'Join Group';
  }
});

const joinButtonClass = computed(() => {
  // Derive class directly from the single source of truth
  switch (currentGroup.value?.membership_status) {
    case 'pending': return 'bg-yellow-500 text-white cursor-not-allowed';
    case 'blocked': return 'bg-red-600 text-white cursor-not-allowed';
    case 'member': case 'creator': return 'bg-gray-200 text-gray-800 hover-bg-gray-300';
    default: return 'bg-blue-600 text-white hover:bg-blue-700';
  }
});

const isJoinButtonDisabled = computed(() => {
  if (isJoiningLeaving.value) return true;
  // Disable if pending or blocked
  return ['pending', 'blocked'].includes(currentGroup.value?.membership_status || '');
});

async function handleMembershipAction() {
  if (!currentGroup.value || (isJoinButtonDisabled.value && !isMember.value)) return;

  // Case for a non-member joining
  if (!isMember.value) {
    await groupStore.joinGroup(currentGroup.value.slug);
    return;
  }

  // Case for a member leaving
  if (isCreator.value) {
    // Creator needs to transfer ownership if other members exist
    if (currentGroup.value.member_count > 1) {
      alert('As the group creator, you must transfer ownership before you can leave.');
      isTransferModalOpen.value = true;
      showOptionsMenu.value = false;
      return;
    } else {
      // THE NEW LOGIC: First alert, then confirm.
      alert('As the sole member, leaving the group will permanently delete it.');
      // Now, call the existing delete handler which has its own confirmation.
      await handleDeleteGroup();
      return;
    }
  }

  // Regular member leaving
  await groupStore.leaveGroup(currentGroup.value.slug);
}

const showOptionsMenu = ref(false);
const optionsMenuRef = ref<HTMLDivElement | null>(null);

useInfiniteScroll(loadMoreGroupPostsTrigger, groupStore.fetchNextPageOfGroupPosts, groupPostsNextCursor);

function toggleOptionsMenu() {
  showOptionsMenu.value = !showOptionsMenu.value;
}
const closeOnClickOutside = (event: MouseEvent) => {
  if (optionsMenuRef.value && !optionsMenuRef.value.contains(event.target as Node)) {
    showOptionsMenu.value = false;
  }
};
watch(showOptionsMenu, (isOpen) => {
  if (isOpen) {
    document.addEventListener('click', closeOnClickOutside, true);
  } else {
    document.removeEventListener('click', closeOnClickOutside, true);
  }
});

function handleTransferOwnership() {
  showOptionsMenu.value = false;
  isTransferModalOpen.value = true;
}

async function handleDeleteGroup() {
  if (!currentGroup.value) return;
  if (confirm(`Are you sure you want to permanently delete the group "${currentGroup.value.name}"?`)) {
    const success = await groupStore.deleteGroup(currentGroup.value.slug);
    if (success) {
      router.push({ name: 'group-list' });
    }
  }
}

function openEditModal() {
  showOptionsMenu.value = false;
  isEditModalOpen.value = true;
}

async function handleConfirmTransfer(newOwnerId: number) {
  if (!currentGroup.value) return;
  const success = await groupStore.transferOwnership(currentGroup.value.slug, newOwnerId);
  if (success) {
    isTransferModalOpen.value = false;
  }
}

async function handleUpdateGroup(data: { name: string; description?: string }) {
  if (!currentGroup.value) return;
  const success = await groupStore.updateGroupDetails(currentGroup.value.slug, data);
  if (success) {
    isEditModalOpen.value = false;
    toast.success('Group details updated successfully!');
  } else {
    toast.error(groupStore.updateGroupError || 'Failed to update group details.');
  }
}
</script>

<template>
  <div class="max-w-4xl mx-auto">
    <div v-if="isLoadingGroup && !currentGroup" class="text-center py-10 text-gray-500">
      <p>Loading group...</p>
    </div>
    <div v-else-if="groupError" class="bg-red-100 border-l-4 border-red-500 text-red-700 p-4">
      <p class="font-bold">Error</p>
      <p>{{ groupError }}</p>
    </div>
    <div v-else-if="currentGroup">
      <header class="bg-white p-6 rounded-lg shadow-md mb-8">
        <div class="flex justify-between items-start">
          <div>
            <h1 data-cy="group-name-header" class="text-3xl font-bold text-gray-900">{{ currentGroup.name }}</h1>
            <p class="text-md text-gray-500 mt-1">@{{ currentGroup.slug }}</p>
            <p class="text-gray-600 mt-2">{{ currentGroup.description }}</p>
          </div>
          <div class="flex-shrink-0 ml-4 flex space-x-2">
            <!-- Button for NON-MEMBERS ONLY -->
            <button v-if="isAuthenticated && currentGroup && !isMember" data-cy="group-membership-button"
              @click="handleMembershipAction()" :disabled="isJoinButtonDisabled" :class="[
                'px-6 py-2 rounded-full font-semibold transition-colors duration-200',
                joinButtonClass,
                isJoiningLeaving ? 'opacity-50' : ''
              ]">
              {{ joinButtonText }}
            </button>

            <!-- Admin options dropdown for the CREATOR -->
            <div v-if="isAuthenticated && isCreator" class="relative" ref="optionsMenuRef">
              <button data-cy="group-options-button" @click.stop="toggleOptionsMenu"
                class="p-2 rounded-full text-gray-500 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500">
                <svg class="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                  <path
                    d="M10 6a2 2 0 110-4 2 2 0 010 4zM10 12a2 2 0 110-4 2 2 0 010 4zM10 18a2 2 0 110-4 2 2 0 010 4z">
                  </path>
                </svg>
              </button>
              <div v-if="showOptionsMenu"
                class="origin-top-right absolute right-0 mt-2 w-56 rounded-md shadow-lg bg-white ring-1 ring-black ring-opacity-5 focus:outline-none z-10">
                <div class="py-1" role="menu" aria-orientation="vertical">
                  <a href="#" @click.prevent="openEditModal"
                    class="text-gray-700 block px-4 py-2 text-sm hover:bg-gray-100" role="menuitem">Edit Group</a>
                  <router-link :to="{ name: 'group-requests', params: { slug: currentGroup.slug } }"
                    class="text-gray-700 block px-4 py-2 text-sm hover:bg-gray-100" role="menuitem">
                    Manage Requests
                  </router-link>
                  <a href="#" @click.prevent="handleTransferOwnership"
                    class="text-gray-700 block px-4 py-2 text-sm hover:bg-gray-100" role="menuitem">Transfer
                    Ownership</a>
                  <a href="#" @click.prevent="handleMembershipAction"
                    class="text-gray-700 block px-4 py-2 text-sm hover:bg-gray-100" role="menuitem">Leave Group</a>
                  <a href="#" @click.prevent="handleDeleteGroup"
                    class="text-red-700 block px-4 py-2 text-sm hover:bg-red-50" role="menuitem">Delete Group</a>
                </div>
              </div>
            </div>

            <!-- NEW: Options dropdown for regular MEMBERS -->
            <div v-if="isAuthenticated && isMember && !isCreator" class="relative" ref="optionsMenuRef">
              <button data-cy="group-options-button" @click.stop="toggleOptionsMenu"
                class="p-2 rounded-full text-gray-500 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500">
                <svg class="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                  <path
                    d="M10 6a2 2 0 110-4 2 2 0 010 4zM10 12a2 2 0 110-4 2 2 0 010 4zM10 18a2 2 0 110-4 2 2 0 010 4z">
                  </path>
                </svg>
              </button>
              <div v-if="showOptionsMenu"
                class="origin-top-right absolute right-0 mt-2 w-56 rounded-md shadow-lg bg-white ring-1 ring-black ring-opacity-5 focus:outline-none z-10">
                <div class="py-1" role="menu" aria-orientation="vertical">
                  <a href="#" data-cy="leave-group-button" @click.prevent="handleMembershipAction"
                    class="text-gray-700 block px-4 py-2 text-sm hover:bg-gray-100" role="menuitem">Leave Group</a>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div class="mt-4 text-sm text-gray-500">
          <!-- CORRECTED CODE -->
          <span>Created by:
            <router-link v-if="currentGroup.creator && currentGroup.creator.username"
              :to="{ name: 'profile', params: { username: currentGroup.creator.username } }"
              class="font-semibold hover:underline">
              {{ currentGroup.creator.username }}
            </router-link>
          </span>
          <span class="mx-2">|</span>
          <span>{{ currentGroup.member_count }} Members</span>
        </div>
        <div v-if="joinLeaveError" class="bg-red-100 border-l-4 border-red-500 text-red-700 p-3 text-sm mt-3">
          <p>{{ joinLeaveError }}</p>
        </div>
      </header>

      <div v-if="isMember" class="mb-8">
        <CreatePostForm :group-slug="currentGroup.slug" />
      </div>

      <div v-else-if="isAuthenticated && !isMember"
        class="bg-white p-6 rounded-lg shadow-md mb-8 text-center text-gray-500">
        <p v-if="currentGroup.privacy_level === 'private'">You must be a member to view and create posts in this private
          group.</p>
        <p v-else>You must join this group to create posts.</p>
        <p v-if="hasPendingRequest" class="mt-4 text-yellow-600">Your request to join is pending approval.</p>
      </div>

      <div v-else-if="!isAuthenticated" class="bg-white p-6 rounded-lg shadow-md mb-8 text-center text-gray-500">
        <p>Please log in to join this group and create posts.</p>
      </div>

      <main class="mt-8">
        <h2 class="text-2xl font-semibold text-gray-800 mb-4">Group Feed</h2>
        <div v-if="groupPosts.length > 0" class="space-y-4">
          <PostItem v-for="post in groupPosts" :key="post.id" :post="post" :hide-group-context="true" />
        </div>
        <div v-else-if="!isLoadingGroupPosts && groupPosts.length === 0"
          class="bg-white p-6 rounded-lg shadow-md text-center text-gray-500">
          <p v-if="!isMember && currentGroup.privacy_level === 'private'">Content is hidden for non-members.</p>
          <p v-else>No posts in this group yet. Be the first to create one!</p>
        </div>
        <div v-if="groupPostsNextCursor" ref="loadMoreGroupPostsTrigger" class="h-10"></div>
        <div v-if="isLoadingGroupPosts && groupPosts.length > 0" class="text-center p-4 text-gray-500">
          Loading more posts...
        </div>
      </main>
    </div>

    <TransferOwnershipModal v-if="currentGroup && currentUser" :is-open="isTransferModalOpen"
      :members="currentGroup.members" :creator-id="currentUser.id" :is-submitting="isTransferringOwnership"
      @close="isTransferModalOpen = false" @submit="handleConfirmTransfer" />

    <EditGroupModal v-if="currentGroup" :is-open="isEditModalOpen" :group="currentGroup"
      :is-submitting="isUpdatingGroup" @close="isEditModalOpen = false" @submit="handleUpdateGroup" />
  </div>
</template>