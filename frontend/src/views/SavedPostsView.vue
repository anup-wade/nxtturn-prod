<!-- C:\Users\Vinay\Project\frontend\src\views\SavedPostsView.vue -->
<!-- VERSION 2: REFACTORED FOR CENTRAL CACHE -->

<script setup lang="ts">
import { onMounted,onUnmounted, ref, computed } from 'vue';
import { useFeedStore } from '@/stores/feed';
import { usePostsStore } from '@/stores/posts'; // --- CHANGE ---
import { useInfiniteScroll } from '@/composables/useInfiniteScroll';
import PostItem from '@/components/PostItem.vue';
import eventBus from '@/services/eventBus';

const feedStore = useFeedStore();
const postsStore = usePostsStore(); // --- CHANGE ---
const loadMoreTrigger = ref<HTMLElement | null>(null);

// --- CHANGE: Resolve full post objects from the central cache using IDs ---
const savedPosts = computed(() => postsStore.getPostsByIds(feedStore.savedPostIds));

// This is the single source of truth for the next page URL
const nextSavedPostUrl = computed(() => feedStore.savedPostsNextPageUrl);

// We pass it to our composable
useInfiniteScroll(loadMoreTrigger, feedStore.fetchNextPageOfSavedPosts, nextSavedPostUrl);

onMounted(() => {
  // --- CHANGE: Use our new "fetch-if-needed" logic by checking the ID array ---
  if (!feedStore.hasFetchedSavedPosts) {
    feedStore.fetchSavedPosts();
  }
});
// --- ADD THIS BLOCK to handle scrolling ---
function scrollToTop() {
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

onMounted(() => {
  if (!feedStore.hasFetchedSavedPosts) {
    feedStore.fetchSavedPosts();
  }
  eventBus.on('scroll-saved-posts-to-top', scrollToTop); // Add listener
});

onUnmounted(() => {
  eventBus.off('scroll-saved-posts-to-top', scrollToTop); // Add cleanup
});
// --- END OF NEW BLOCK ---
</script>

<template>
  <div class="space-y-4">
    <div class="bg-white rounded-lg shadow-sm p-4 md:p-6 border border-gray-200">
      <div class="flex items-center justify-between">
        <h1 class="text-xl md:text-2xl font-bold text-gray-800">Saved Posts</h1>
      </div>
    </div>

    <!-- --- CHANGE: Use our local computed `savedPosts` for all checks and loops --- -->
    <div v-if="feedStore.isLoadingSavedPosts && savedPosts.length === 0" class="text-center text-gray-500 mt-12">
      Loading saved posts...
    </div>

    <div v-else-if="feedStore.savedPostsError" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-md">
      Error: {{ feedStore.savedPostsError }}
    </div>

    <div v-else-if="savedPosts.length === 0" class="text-center text-gray-500 mt-12 p-8 bg-white rounded-lg shadow-sm border border-gray-200">
      <p class="mb-4 text-lg">You haven't saved any posts yet.</p>
      <p>Click the bookmark icon on any post to save it for later!</p>
    </div>

    <div v-else class="space-y-4">
      <PostItem
        v-for="post in savedPosts"
        :key="post.id"
        :post="post"
      />
      
      <div v-if="nextSavedPostUrl" ref="loadMoreTrigger" class="h-10"></div>
      
      <div v-if="feedStore.isLoadingSavedPosts && savedPosts.length > 0" class="text-center p-4 text-gray-500">
          Loading more posts...
      </div>

    </div>
  </div>
</template>