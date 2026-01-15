<script setup lang="ts">
import { onMounted, onUnmounted, ref, computed } from 'vue';
import { useFeedStore } from '@/stores/feed';
import { usePostsStore } from '@/stores/posts';
import { useInfiniteScroll } from '@/composables/useInfiniteScroll';
import CreatePostForm from '@/components/CreatePostForm.vue';
import PostItem from '@/components/PostItem.vue';
import eventBus from '@/services/eventBus';
import { ArrowUpIcon } from '@heroicons/vue/24/solid';
import PostItemSkeleton from '@/components/PostItemSkeleton.vue';

const feedStore = useFeedStore();
const postsStore = usePostsStore();

const createPostFormKey = ref(0);
const loadMoreTrigger = ref<HTMLElement | null>(null);

const mainFeedPosts = computed(() => {
  return postsStore.getPostsByIds(feedStore.mainFeedPostIds);
});

const nextFeedPageUrl = computed(() => feedStore.mainFeedNextCursor);
useInfiniteScroll(loadMoreTrigger, feedStore.fetchNextPageOfMainFeed, nextFeedPageUrl);

function forceFormReset() {
  createPostFormKey.value++;
}

function scrollToTop() {
  window.scrollTo({
    top: 0,
    behavior: 'smooth'
  });
}

function handleShowNewPosts() {
  feedStore.showNewPosts();
  scrollToTop();
}

onMounted(() => {
  eventBus.on('reset-feed-form', forceFormReset);
  eventBus.on('scroll-to-top', scrollToTop);
  
  feedStore.refreshMainFeed();
});

onUnmounted(() => {
  eventBus.off('reset-feed-form', forceFormReset);
  eventBus.off('scroll-to-top', scrollToTop);
});
</script>

<template>
  <div class="max-w-4xl mx-auto">
    <div class="space-y-6">
      <CreatePostForm :key="createPostFormKey" />
      <div 
        :class="['sticky top-16 z-10 flex justify-center py-2', feedStore.newPostIdsFromRefresh.length === 0 ? 'hidden' : '']">
        <button 
          @click="handleShowNewPosts" 
          class="flex items-center gap-2 bg-blue-500 text-white font-semibold px-4 py-2 rounded-full shadow-lg hover:bg-blue-600 transition">
          <ArrowUpIcon class="w-5 h-5" />
          Show {{ feedStore.newPostIdsFromRefresh.length }} new post(s)
        </button>
      </div>
      <div v-if="feedStore.isLoadingMainFeed && mainFeedPosts.length === 0" class="space-y-4">
        <PostItemSkeleton v-for="n in 3" :key="n" />
      </div>
      <div v-if="feedStore.mainFeedError"
        class="bg-red-100 border border-red-300 text-red-700 px-4 py-3 rounded-md text-center p-8" role="alert">
        Error loading feed: {{ feedStore.mainFeedError }}
      </div>
      <div v-if="mainFeedPosts.length > 0" class="space-y-4">
        <!-- THIS IS THE LINE THAT HAS BEEN FIXED -->
        <PostItem v-for="post in mainFeedPosts" :key="post.id" :post="post" />
      </div>
      <div v-if="!feedStore.isLoadingMainFeed && mainFeedPosts.length === 0 && !feedStore.mainFeedError"
        class="text-center p-8 text-gray-500" data-cy="empty-feed-message">
        Your feed is empty. Follow some users or create a post!
      </div>
      <div v-if="feedStore.mainFeedNextCursor" ref="loadMoreTrigger" class="h-10"></div>
      <div v-if="feedStore.isLoadingMainFeed && mainFeedPosts.length > 0"
        class="text-center p-4 text-gray-500">
        Loading more posts...
      </div>
    </div>
  </div>
</template>