<script setup lang="ts">
import { ref, watch, computed } from 'vue';
import { useRoute } from 'vue-router';
import { usePostsStore } from '@/stores/posts';
import PostItem from '@/components/PostItem.vue';
import PostItemSkeleton from '@/components/PostItemSkeleton.vue';

const route = useRoute();
const postsStore = usePostsStore();

const postId = computed(() => Number(route.params.postId));
const post = computed(() => postsStore.getPostById(postId.value));

const isLoading = ref(false);
const error = ref<string | null>(null);

watch(
  postId,
  async (newPostId) => {
    if (!newPostId || isNaN(newPostId)) return;

    // Only show the full skeleton if we have no cached version at all
    if (!post.value) {
      isLoading.value = true;
    }
    error.value = null;
    
    try {
      await postsStore.fetchPostById(newPostId);
    } catch (e: any) {
      error.value = e.response?.data?.detail || 'Post could not be loaded.';
    } finally {
      isLoading.value = false;
    }
  },
  { immediate: true }
);
</script>

<template>
  <div class="max-w-4xl mx-auto">
    <div v-if="isLoading && !post">
      <PostItemSkeleton />
    </div>

    <div v-else-if="error" class="bg-red-100 border-l-4 border-red-500 text-red-700 p-4">
      <p class="font-bold">Error loading post</p>
      <p>{{ error }}</p>
    </div>

    <div v-else-if="post">
      <PostItem :post="post" />
    </div>
    
    <div v-else class="text-center py-10 text-gray-500">
      Post not found.
    </div>
  </div>
</template>