<script setup lang="ts">
import { ref, watch, computed, onMounted, onUnmounted } from 'vue';
import { useRoute } from 'vue-router';
import { useProfileStore } from '@/stores/profile';
import { useAuthStore } from '@/stores/auth';
import { usePostsStore } from '@/stores/posts';
import { useInfiniteScroll } from '@/composables/useInfiniteScroll';
import { storeToRefs } from 'pinia';
import eventBus from '@/services/eventBus';

import ProfileCard from '@/components/profile/ProfileCard.vue';
import PostItem from '@/components/PostItem.vue';
import ProfileAboutTab from '@/components/profile/tabs/ProfileAboutTab.vue';
import ProfileEducationTab from '@/components/profile/tabs/ProfileEducationTab.vue';
import ProfileSkillsTab from '@/components/profile/tabs/ProfileSkillsTab.vue';
import ProfileExperienceTab from '@/components/profile/tabs/ProfileExperienceTab.vue';
import ProfileContactTab from '@/components/profile/tabs/ProfileContactTab.vue';
import ProfileResumeTab from '@/components/profile/tabs/ProfileResumeTab.vue';

const leftColumn = ref<HTMLElement | null>(null);
const rightColumn = ref<HTMLElement | null>(null);
const route = useRoute();
const profileStore = useProfileStore();
const authStore = useAuthStore();
const postsStore = usePostsStore();
const {
  currentProfile, isLoadingProfile, isLoadingPosts,
  errorProfile, errorPosts
} = storeToRefs(profileStore);
const { currentUser, isAuthenticated } = storeToRefs(authStore);
const username = computed(() => route.params.username as string || '');
const activeTab = ref('About');
const tabs = ['About', 'Education', 'Skills', 'Experience', 'Resume/CV', 'Contact'];
const userPostIds = computed(() => profileStore.postIdsByUsername[username.value] || []);
const userPostsNextPageUrl = computed(() => profileStore.nextPageUrlByUsername[username.value]);
const userPosts = computed(() => postsStore.getPostsByIds(userPostIds.value));
const isOwnProfile = computed(() => isAuthenticated.value && currentUser.value?.username === username.value);
const loadMoreTrigger = ref<HTMLElement | null>(null);

useInfiniteScroll(
  loadMoreTrigger,
  () => profileStore.fetchNextPageOfUserPosts(username.value),
  userPostsNextPageUrl
);

const loadProfileData = () => {
  if (username.value) {
    profileStore.fetchProfile(username.value);
    profileStore.refreshUserPosts(username.value);
  }
};

watch(username, () => {
  loadProfileData();
  activeTab.value = 'About';
}, { immediate: true });

function scrollToTop() {
  leftColumn.value?.scrollTo({ top: 0, behavior: 'smooth' });
  rightColumn.value?.scrollTo({ top: 0, behavior: 'smooth' });
}

onMounted(() => {
  eventBus.on('scroll-profile-to-top', scrollToTop);
});

onUnmounted(() => {
  eventBus.off('scroll-profile-to-top', scrollToTop);
});
</script>

<template>
  <div>
    <div v-if="isLoadingProfile && !currentProfile" class="text-center p-10 text-gray-500 pt-20">
      Loading profile...
    </div>

    <div v-else-if="errorProfile" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-md m-4 mt-20">
      <p>{{ errorProfile }}</p>
    </div>

    <div v-else-if="currentProfile" class="container mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 pt-20">
      <div class="grid grid-cols-12 gap-x-8 h-[calc(100vh-5rem)]">

        <!-- 
            --- THIS IS THE FIX ---
            Added data-cy="profile-left-column" to this aside element
            so Cypress can specifically target it for scrolling.
        -->
        <aside ref="leftColumn" data-cy="profile-left-column"
          class="col-span-12 lg:col-span-6 h-full overflow-y-auto space-y-6">
          <ProfileCard :profile="currentProfile" :is-own-profile="isOwnProfile" />

          <!-- Tab Section -->
          <div>
            <div class="mb-5 border-b border-gray-200">
              <nav class="-mb-px flex space-x-4 overflow-x-auto" aria-label="Tabs">
                <button v-for="tab in tabs" :key="tab" @click="activeTab = tab" :class="[
                  'whitespace-nowrap pb-3 px-1 border-b-2 font-medium text-sm',
                  activeTab === tab
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                ]">
                  {{ tab }}
                </button>
              </nav>
            </div>
            <div class="transition-all duration-300">
              <ProfileAboutTab v-if="activeTab === 'About'" :profile="currentProfile" :is-own-profile="isOwnProfile" />
              <ProfileEducationTab v-if="activeTab === 'Education'" :profile="currentProfile"
                :is-own-profile="isOwnProfile" />
              <ProfileSkillsTab v-if="activeTab === 'Skills'" :profile="currentProfile"
                :is-own-profile="isOwnProfile" />
              <ProfileExperienceTab v-if="activeTab === 'Experience'" :profile="currentProfile"
                :is-own-profile="isOwnProfile" />
              <ProfileResumeTab v-if="activeTab === 'Resume/CV'" :profile="currentProfile"
                :is-own-profile="isOwnProfile" />
              <ProfileContactTab v-if="activeTab === 'Contact'" :profile="currentProfile"
                :is-own-profile="isOwnProfile" />
            </div>
          </div>
        </aside>

        <!-- RIGHT COLUMN -->
        <div ref="rightColumn" class="col-span-12 lg:col-span-6 min-w-0 mt-6 lg:mt-0 h-full overflow-y-auto">
          <div v-if="isLoadingPosts && userPosts.length === 0" class="text-center p-10 text-gray-500">
            Loading posts...
          </div>
          <div v-else-if="errorPosts" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-md">
            {{ errorPosts }}
          </div>
          <div v-else-if="userPosts.length > 0" class="space-y-4">
            <PostItem v-for="post in userPosts" :key="post.id" :post="post" />
          </div>
          <div v-else class="bg-white rounded-lg shadow-md p-10 text-center text-gray-500">
            This user hasn't posted anything yet.
          </div>

          <div v-if="userPostsNextPageUrl" ref="loadMoreTrigger" class="h-10"></div>
          <div v-if="isLoadingPosts && userPosts.length > 0" class="text-center p-4 text-gray-500">
            Loading more posts...
          </div>
        </div>

      </div>
    </div>
  </div>
</template>