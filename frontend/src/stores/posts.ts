// C:\Users\Vinay\Project\frontend\src\stores\posts.ts
import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import axiosInstance from '@/services/axiosInstance'
import type { Post } from '@/types'

export const usePostsStore = defineStore('posts', () => {
  const posts = ref<{ [id: number]: Post }>({})

  const getPostById = computed(() => {
    return (postId: number): Post | undefined => posts.value[postId]
  })

  const getPostsByIds = computed(() => {
    return (ids: number[]): Post[] => {
      return ids.map((id) => posts.value[id]).filter((post): post is Post => !!post)
    }
  })

  function addOrUpdatePosts(newPosts: Partial<Post>[]) {
    for (const post of newPosts) {
      if (post && post.id) {
        const existingPost = posts.value[post.id]
        if (existingPost) {
          posts.value[post.id] = { ...existingPost, ...post }
        } else {
          posts.value[post.id] = post as Post
        }
      }
    }
  }

  function processVoteUpdate(updatedPost: Post) {
    if (posts.value[updatedPost.id] && updatedPost.poll) {
      posts.value[updatedPost.id].poll = updatedPost.poll
    }
  }

  function removePost(postId: number) {
    console.log(`PostsStore: Deleting post data for ID ${postId} from central cache.`)
    delete posts.value[postId]
  }

  function incrementCommentCount(postId: number) {
    const post = posts.value[postId]
    if (post) {
      post.comment_count = (post.comment_count || 0) + 1
    }
  }

  function decrementCommentCount(postId: number) {
    const post = posts.value[postId]
    if (post && post.comment_count) {
      post.comment_count = Math.max(0, post.comment_count - 1)
    }
  }

  // --- NEW ACTION TO FIX THE SYNCHRONIZATION BUG ---
  function updateAuthorDetailsInPosts(authorId: number, payload: { picture: string | null }) {
    console.log(`PostsStore: Syncing picture for author ID ${authorId}`)
    for (const post of Object.values(posts.value)) {
      if (post && post.author && post.author.id === authorId) {
        post.author.picture = payload.picture
      }
    }
  }
  // --- END OF NEW ACTION ---

  async function fetchPostById(postId: number) {
    const existingPost = posts.value[postId]
    if (existingPost && typeof existingPost.comment_count !== 'undefined') {
      return existingPost
    }
    try {
      const response = await axiosInstance.get<Post>(`/posts/${postId}/`)
      addOrUpdatePosts([response.data])
      return response.data
    } catch (error) {
      console.error(`Failed to fetch post with ID ${postId}`, error)
      throw error
    }
  }

  return {
    posts,
    getPostById,
    getPostsByIds,
    addOrUpdatePosts,
    removePost,
    incrementCommentCount,
    decrementCommentCount,
    fetchPostById,
    processVoteUpdate,
    updateAuthorDetailsInPosts, // <-- Expose the new action
  }
})
