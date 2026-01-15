<script setup lang="ts">
import { onMounted, onUnmounted, watch, ref, computed } from 'vue';
import { useRouter, RouterLink, useRoute } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import { useNotificationStore } from '@/stores/notification';
import { storeToRefs } from 'pinia';
import { debounce } from 'lodash-es';
import { getAvatarUrl } from '@/utils/avatars';
import type { User } from '@/stores/auth';
import { useSearchStore } from '@/stores/search';
import { useFeedStore } from '@/stores/feed';
import { useGroupStore } from '@/stores/group';
import { usePostsStore } from '@/stores/posts';
import type { Post } from '@/types';
import eventBus from '@/services/eventBus';

// --- Icon Imports for new dropdown ---
import {
  Cog6ToothIcon,
  QuestionMarkCircleIcon,
  EyeIcon,
  ChatBubbleLeftRightIcon,
  MoonIcon,
  ArrowLeftOnRectangleIcon,
  ChevronDownIcon,
} from '@heroicons/vue/24/outline';


const authStore = useAuthStore();
const notificationStore = useNotificationStore();
const searchStore = useSearchStore();
const feedStore = useFeedStore();
const groupStore = useGroupStore();
const postsStore = usePostsStore();
const router = useRouter();
const route = useRoute();

const { unreadCount } = storeToRefs(notificationStore);
const { currentUser } = storeToRefs(authStore);
const { userResults, isLoadingUsers } = storeToRefs(searchStore);

const { isLoadingSearchResults: isLoadingPosts } = storeToRefs(feedStore);
const postResultIds = computed(() => feedStore.searchResultPostIds);
const postResults = computed(() => postsStore.getPostsByIds(postResultIds.value));

const { groupSearchResults: groupResults, isLoadingGroupSearch } = storeToRefs(groupStore);

const searchQuery = ref('');
const showSearchDropdown = ref(false);
const searchContainerRef = ref<HTMLDivElement | null>(null);

// --- State for the new Profile Dropdown ---
const isProfileMenuOpen = ref(false);
const profileMenuRef = ref<HTMLDivElement | null>(null);


const hasAnyResults = computed(() => userResults.value.length > 0 || postResults.value.length > 0 || groupResults.value.length > 0);
const isSearching = computed(() => isLoadingUsers.value || isLoadingPosts.value || isLoadingGroupSearch.value);

function handleLogoClick(event: MouseEvent) {
  if (route.path === '/') {
    event.preventDefault();
    eventBus.emit('scroll-to-top');
  }
}

// --- Modified to be used within the dropdown AND on the avatar link ---
function handleProfileClick(event: MouseEvent) {
  // Only scrolls to top if on your own profile page
  if (route.name === 'profile' && route.params.username === currentUser.value?.username) {
    event.preventDefault();
    eventBus.emit('scroll-profile-to-top');
  }
  isProfileMenuOpen.value = false; // Always close menu on navigation
}

function handleNotificationsClick(event: MouseEvent) {
  if (route.name === 'notifications') {
    event.preventDefault();
    eventBus.emit('scroll-notifications-to-top');
  }
}

const handleFullSearchSubmit = () => {
  if (searchQuery.value.trim()) {
    showSearchDropdown.value = false;
    router.push({ name: 'search', query: { q: searchQuery.value.trim() } });
  }
};

const debouncedSearch = debounce(async (query: string) => {
  if (query.length < 1) {
    searchStore.clearSearch();
    feedStore.searchResultPostIds = [];
    groupStore.groupSearchResults = [];
    return;
  }
  await Promise.all([
    searchStore.searchUsers(query),
    feedStore.searchPosts(query),
    groupStore.searchGroups(query)
  ]);
}, 300);

const handleSearchInput = () => {
  if (searchQuery.value.trim()) {
    showSearchDropdown.value = true;
    debouncedSearch(searchQuery.value);
  } else {
    showSearchDropdown.value = false;
    searchStore.clearSearch();
    feedStore.searchResultPostIds = [];
    groupStore.groupSearchResults = [];
  }
};

const selectUserAndNavigate = (user: User) => {
  showSearchDropdown.value = false;
  searchQuery.value = '';
  router.push({ name: 'profile', params: { username: user.username } });
};

const selectPostAndNavigate = (post: Post) => {
  showSearchDropdown.value = false;
  searchQuery.value = '';
  router.push({ name: 'single-post', params: { postId: post.id } });
};

const closeSearchDropdownOnClickOutside = (event: MouseEvent) => {
  if (searchContainerRef.value && !searchContainerRef.value.contains(event.target as Node)) {
    showSearchDropdown.value = false;
  }
};

// --- NEW FUNCTION: Close Profile Menu on Click Outside ---
const closeProfileMenuOnClickOutside = (event: MouseEvent) => {
  if (profileMenuRef.value && !profileMenuRef.value.contains(event.target as Node)) {
    isProfileMenuOpen.value = false;
  }
};

watch(showSearchDropdown, (isOpen) => {
  if (isOpen) document.addEventListener('click', closeSearchDropdownOnClickOutside);
  else document.removeEventListener('click', closeSearchDropdownOnClickOutside);
});

// --- NEW WATCHER for Profile Menu ---
watch(isProfileMenuOpen, (isOpen) => {
  if (isOpen) document.addEventListener('click', closeProfileMenuOnClickOutside);
  else document.removeEventListener('click', closeProfileMenuOnClickOutside);
});


onUnmounted(() => {
  document.removeEventListener('click', closeSearchDropdownOnClickOutside);
  document.removeEventListener('click', closeProfileMenuOnClickOutside); // Cleanup
});


onMounted(() => {
  authStore.initializeAuth();
});

const handleLogout = async () => {
  await authStore.logout();
};
</script>

<template>
  <header class="bg-white shadow-sm flex-shrink-0 z-40 fixed top-0 left-0 w-full">
    <nav class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
      <div class="flex items-center justify-between h-16">
        <div class="flex-shrink-0">
          <RouterLink to="/" @click="handleLogoClick" data-cy="navbar-logo-link"
            class="text-2xl font-bold tracking-tight">
            <span class="bg-gradient-to-r from-blue-600 to-purple-500 bg-clip-text text-transparent">NxtTurn</span>
          </RouterLink>
        </div>
        <div class="flex-grow flex justify-center px-4" ref="searchContainerRef">
          <!-- Search form and dropdown... UNCHANGED -->
          <div class="relative w-full max-w-lg">
            <form @submit.prevent="handleFullSearchSubmit" v-if="authStore.isAuthenticated">
              <input data-cy="global-search-input" type="text" v-model="searchQuery" @input="handleSearchInput"
                @focus="handleSearchInput" placeholder="Search for users or content..."
                class="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-full bg-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white transition" />
              <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <svg class="h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </div>
            </form>
            <div v-if="showSearchDropdown && searchQuery"
              class="absolute top-full mt-2 w-full rounded-md shadow-lg bg-white ring-1 ring-black ring-opacity-5 z-50">
              <ul class="py-1 text-base overflow-y-auto">
                <li v-if="isSearching" class="px-4 py-2 text-sm text-gray-500">Searching...</li>
                <li v-else-if="!isSearching && !hasAnyResults" class="px-4 py-2 text-sm text-gray-500">No results found.
                </li>

                <template v-if="userResults.length > 0">
                  <li class="px-4 pt-2 pb-1 text-xs font-bold text-gray-500 uppercase">Users</li>
                  <li v-for="user in userResults.slice(0, 2)" :key="`user-${user.id}`">
                    <a @click.prevent="selectUserAndNavigate(user)" href="#"
                      class="flex items-center gap-3 px-4 py-2 text-sm cursor-pointer hover:bg-gray-100">
                      <img :src="getAvatarUrl(user.picture, user.first_name, user.last_name)" alt="avatar"
                        class="w-8 h-8 rounded-full object-cover">
                      <div>
                        <span class="font-medium text-gray-900">{{ user.first_name }} {{ user.last_name }}</span>
                        <p class="text-xs text-gray-500">@{{ user.username }}</p>
                      </div>
                    </a>
                  </li>
                </template>

                <template v-if="groupResults.length > 0">
                  <li class="px-4 pt-2 pb-1 text-xs font-bold text-gray-500 uppercase border-t border-gray-100 mt-1">
                    Groups</li>
                  <li v-for="group in groupResults.slice(0, 2)" :key="`group-${group.id}`">
                    <router-link :to="{ name: 'group-detail', params: { slug: group.slug } }"
                      @click="showSearchDropdown = false" class="block px-4 py-2 text-sm hover:bg-gray-100">
                      <p class="font-medium text-gray-900 truncate">{{ group.name }}</p>
                      <p class="text-xs text-gray-500 truncate">{{ group.slug }}</p>
                    </router-link>
                  </li>
                </template>

                <template v-if="postResults.length > 0">
                  <li class="px-4 pt-2 pb-1 text-xs font-bold text-gray-500 uppercase border-t border-gray-100 mt-1">
                    Posts</li>
                  <li v-for="post in postResults.slice(0, 2)" :key="`post-${post.id}`">
                    <a @click.prevent="selectPostAndNavigate(post)" href="#"
                      class="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 truncate">
                      {{ post.content || post.title }}
                    </a>
                  </li>
                </template>

                <li v-if="!isSearching && hasAnyResults" class="border-t border-gray-200">
                  <button @click="handleFullSearchSubmit"
                    class="w-full text-left px-4 py-2 text-sm font-medium text-blue-600 hover:bg-gray-100">
                    See all results for "{{ searchQuery }}"
                  </button>
                </li>
              </ul>
            </div>
          </div>
        </div>

        <!-- =========== MODIFIED AREA START =========== -->
        <div class="flex items-center gap-4 flex-shrink-0">
          <template v-if="authStore.isAuthenticated && currentUser">
            <RouterLink :to="{ name: 'explore' }" class="text-sm font-medium text-gray-600 hover:text-indigo-500"
              active-class="text-indigo-600 font-semibold">Explore</RouterLink>
            <a href="#" class="text-sm font-medium text-gray-600 hover:text-indigo-500">Jobs</a>
            <RouterLink :to="{ name: 'notifications' }" @click="handleNotificationsClick"
              data-cy="navbar-notifications-link" class="relative text-gray-600 hover:text-blue-500"
              title="Notifications">
              <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path
                  d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
              </svg>
              <span v-if="unreadCount > 0" data-cy="notification-indicator"
                class="absolute top-0 right-0 -mt-1 -mr-1 flex h-5 w-5 items-center justify-center rounded-full bg-red-500 text-xs text-white">
                {{ unreadCount > 9 ? '9+' : unreadCount }}
              </span>
            </RouterLink>

            <!-- New Profile Dropdown -->
            <div class="relative" ref="profileMenuRef">
              <!-- MODIFIED: Split into two elements -->
              <div class="flex items-center">
                <RouterLink :to="{ name: 'profile', params: { username: currentUser.username } }"
                  @click="handleProfileClick" data-cy="profile-link"
                  class="rounded-full focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2">
                  <span class="sr-only">View your profile</span>
                  <img :src="getAvatarUrl(currentUser.picture, currentUser.first_name, currentUser.last_name)"
                    alt="Your avatar" class="h-8 w-8 rounded-full object-cover" data-cy="navbar-avatar-main">
                </RouterLink>

                <button @click="isProfileMenuOpen = !isProfileMenuOpen" type="button" data-cy="profile-menu-button"
                  class="ml-1 p-1 rounded-full focus:outline-none focus:ring-2 focus:ring-blue-500">
                  <span class="sr-only">Open user menu</span>
                  <ChevronDownIcon class="h-5 w-5 text-gray-500 hover:text-gray-700" />
                </button>
              </div>

              <transition enter-active-class="transition ease-out duration-100"
                enter-from-class="transform opacity-0 scale-95" enter-to-class="transform opacity-100 scale-100"
                leave-active-class="transition ease-in duration-75" leave-from-class="transform opacity-100 scale-100"
                leave-to-class="transform opacity-0 scale-95">
                <div v-if="isProfileMenuOpen"
                  class="absolute right-0 z-10 mt-2 w-72 origin-top-right rounded-md bg-white py-1 shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none">
                  <!-- User Info Header -->
                  <div class="px-4 py-3 border-b border-gray-200">
                    <!-- Note: The profile link is now also on the avatar itself -->
                    <div class="flex items-center gap-3">
                      <img :src="getAvatarUrl(currentUser.picture, currentUser.first_name, currentUser.last_name)"
                        alt="Your avatar" class="h-10 w-10 rounded-full object-cover" data-cy="navbar-avatar-dropdown">
                      <div>
                        <p class="text-sm font-medium text-gray-800">{{ currentUser.first_name }} {{
                          currentUser.last_name }}</p>
                        <p class="text-sm text-gray-500">Premium Member</p> <!-- Placeholder -->
                      </div>
                    </div>
                  </div>
                  <!-- Menu Items -->
                  <div class="py-1">
                    <a href="#" class="flex items-center gap-3 px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">
                      <Cog6ToothIcon class="h-5 w-5 text-gray-500" />
                      <span>Settings & Privacy</span>
                    </a>
                    <a href="#" class="flex items-center gap-3 px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">
                      <QuestionMarkCircleIcon class="h-5 w-5 text-gray-500" />
                      <span>Help & Support</span>
                    </a>
                    <a href="#" class="flex items-center gap-3 px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">
                      <EyeIcon class="h-5 w-5 text-gray-500" />
                      <span>Display & Accessibility</span>
                    </a>
                    <a href="#" class="flex items-center gap-3 px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">
                      <ChatBubbleLeftRightIcon class="h-5 w-5 text-gray-500" />
                      <span>Give Feedback</span>
                    </a>
                  </div>
                  <!-- Dark Mode -->
                  <div class="py-1 border-t border-gray-200">
                    <div class="flex items-center justify-between px-4 py-2 text-sm text-gray-700">
                      <div class="flex items-center gap-3">
                        <MoonIcon class="h-5 w-5 text-gray-500" />
                        <span>Dark Mode</span>
                      </div>
                      <button type="button"
                        class="bg-gray-200 relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                        role="switch" aria-checked="false">
                        <span
                          class="pointer-events-none relative inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out translate-x-0"></span>
                      </button>
                    </div>
                  </div>
                  <!-- Logout -->
                  <div class="py-1 border-t border-gray-200">
                    <button @click="handleLogout" data-cy="logout-button"
                      class="w-full text-left flex items-center gap-3 px-4 py-2 text-sm text-red-600 hover:bg-gray-100">
                      <ArrowLeftOnRectangleIcon class="h-5 w-5" />
                      <span>Log Out</span>
                    </button>
                  </div>
                </div>
              </transition>
            </div>
          </template>
          <template v-else>
            <RouterLink to="/login" class="text-sm font-medium text-gray-600 hover:text-indigo-500">Login</RouterLink>
          </template>
        </div>
        <!-- =========== MODIFIED AREA END =========== -->
      </div>
    </nav>
  </header>
</template>