<!-- C:\Users\Vinay\Project\frontend\src\views\SearchPage.vue -->
<!-- VERSION 2: DEFINITIVE & CORRECTED -->

<script setup lang="ts">
import { ref, watch, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { debounce } from 'lodash-es';

import { useSearchStore } from '@/stores/search';
import { useFeedStore } from '@/stores/feed';
import { useGroupStore } from '@/stores/group';
import { usePostsStore } from '@/stores/posts';
import PostItem from '@/components/PostItem.vue';
import { getAvatarUrl } from '@/utils/avatars';

const route = useRoute();
const router = useRouter();
const searchStore = useSearchStore();
const feedStore = useFeedStore();
const groupStore = useGroupStore();
const postsStore = usePostsStore();

const localQuery = ref((route.query.q as string) || '');
const activeTab = ref<'users' | 'posts' | 'groups'>('users');

// User-related data
const userResults = computed(() => searchStore.userResults);
const isLoadingUsers = computed(() => searchStore.isLoadingUsers);
const userError = computed(() => searchStore.userError);

// Post-related data, now correctly using searchResultPostIds
const postResultIds = computed(() => feedStore.searchResultPostIds);
const postResults = computed(() => postsStore.getPostsByIds(postResultIds.value));
const isLoadingPosts = computed(() => feedStore.isLoadingSearchResults);
const postError = computed(() => feedStore.searchError);

// Group-related data
const groupResults = computed(() => groupStore.groupSearchResults);
const isLoadingGroups = computed(() => groupStore.isLoadingGroupSearch);
const groupError = computed(() => groupStore.groupSearchError);

const performSearch = (query: string) => {
  if (query.trim()) {
    searchStore.searchUsers(query);
    feedStore.searchPosts(query);
    groupStore.searchGroups(query);
  } else {
    searchStore.clearSearch();
    feedStore.searchResultPostIds = []; // <-- THE FIX
    groupStore.groupSearchResults = [];
  }
};

if (localQuery.value) {
  performSearch(localQuery.value);
}

watch(() => route.query.q, (newQuery) => {
  const queryStr = (newQuery as string) || '';
  if (localQuery.value !== queryStr) {
    localQuery.value = queryStr;
    performSearch(queryStr);
  }
});

const debouncedSearch = debounce((query: string) => {
  router.push({ name: 'search', query: { q: query } });
}, 500);

const handleInput = (event: Event) => {
  const query = (event.target as HTMLInputElement).value;
  debouncedSearch(query);
};
</script>

<template>
  <div class="max-w-4xl mx-auto p-4">
    <h1 class="text-3xl font-bold text-gray-800 mb-6">Search</h1>
    <div class="relative mb-6">
      <input type="text" :value="localQuery" @input="handleInput" placeholder="Search for users or content..."
        class="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-full shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
      <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24"
          stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
      </div>
    </div>
    <div class="border-b border-gray-200 mb-6">
      <nav class="-mb-px flex space-x-8" aria-label="Tabs">
        <button @click="activeTab = 'users'"
          :class="['whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm', activeTab === 'users' ? 'border-blue-500 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300']">
          Users
        </button>
        <button @click="activeTab = 'posts'"
          :class="['whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm', activeTab === 'posts' ? 'border-blue-500 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300']">
          Posts
        </button>
        <button @click="activeTab = 'groups'"
          :class="['whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm', activeTab === 'groups' ? 'border-blue-500 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300']">
          Groups
        </button>
      </nav>
    </div>
    <div>
      <div v-if="activeTab === 'users'">
        <div v-if="isLoadingUsers" class="text-center py-6 text-gray-500">Searching for users...</div>
        <div v-else-if="userError" class="bg-red-100 border-l-4 border-red-500 text-red-700 p-4">
          <p>{{ userError }}</p>
        </div>
        <ul v-else-if="userResults.length > 0" class="bg-white rounded-lg shadow-md divide-y divide-gray-200">
          <li v-for="user in userResults" :key="user.id">
            <router-link :to="{ name: 'profile', params: { username: user.username } }"
              class="flex items-center gap-4 p-4 hover:bg-gray-50 transition-colors">
              <img :src="getAvatarUrl(user.picture, user.first_name, user.last_name)" alt="avatar"
                class="w-12 h-12 rounded-full object-cover bg-gray-200 flex-shrink-0">
              <div class="flex-grow">
                <p class="font-bold text-gray-800">{{ user.first_name }} {{ user.last_name }}</p>
                <p class="text-sm text-gray-500">@{{ user.username }}</p>
              </div>
            </router-link>
          </li>
        </ul>
        <div v-else-if="localQuery" class="text-center py-6 text-gray-500">No users found for "{{ localQuery }}".</div>
      </div>
      <div v-if="activeTab === 'posts'">
        <div v-if="isLoadingPosts" class="text-center py-6 text-gray-500">Searching for posts...</div>
        <div v-else-if="postError" class="bg-red-100 border-l-4 border-red-500 text-red-700 p-4">
          <p>{{ postError }}</p>
        </div>
        <div v-else-if="postResults.length > 0" class="space-y-6">
          <PostItem v-for="post in postResults" :key="post.id" :post="post" />
        </div>
        <div v-else-if="localQuery" class="text-center py-6 text-gray-500">No posts found for "{{ localQuery }}".</div>
      </div>
      <div v-if="activeTab === 'groups'">
        <div v-if="isLoadingGroups" class="text-center py-6 text-gray-500">Searching for groups...</div>
        <div v-else-if="groupError" class="bg-red-100 border-l-4 border-red-500 text-red-700 p-4">
          <p>{{ groupError }}</p>
        </div>
        <ul v-else-if="groupResults.length > 0" class="bg-white rounded-lg shadow-md divide-y divide-gray-200">
          <li v-for="group in groupResults" :key="group.id">
            <router-link :to="{ name: 'group-detail', params: { slug: group.slug } }"
              class="block p-4 hover:bg-gray-50 transition-colors">
              <p class="font-bold text-gray-800">{{ group.name }}</p>
              <p class="text-sm text-gray-500">{{ group.slug }}</p>
              <p class="text-sm text-gray-600 mt-1 truncate">{{ group.description }}</p>
              <p class="text-xs text-gray-500 mt-2">{{ group.member_count }} members</p>
            </router-link>
          </li>
        </ul>
        <div v-else-if="localQuery" class="text-center py-6 text-gray-500">No groups found for "{{ localQuery }}".</div>
      </div>
    </div>
  </div>
</template>