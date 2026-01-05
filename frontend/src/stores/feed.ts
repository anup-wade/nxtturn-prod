// C:\Users\Vinay\Project\frontend\src\stores\feed.ts
import { ref } from 'vue'
import { defineStore } from 'pinia'
import axiosInstance from '@/services/axiosInstance'
import { useAuthStore } from './auth'
import { usePostsStore, type Post } from './posts'
import { useProfileStore } from './profile'
import { useGroupStore } from './group'

interface CursorPaginatedResponse {
  next: string | null
  previous: string | null
  results: Post[]
}
interface OffsetPaginatedResponse {
  count: number
  next: string | null
  previous: string | null
  results: Post[]
}

export const useFeedStore = defineStore('feed', () => {
  const postsStore = usePostsStore()
  const authStore = useAuthStore()
  const profileStore = useProfileStore()
  const groupStore = useGroupStore()

  // --- State (is unchanged) ---
  const mainFeedPostIds = ref<number[]>([])
  const newPostIdsFromRefresh = ref<number[]>([])
  const mainFeedNextCursor = ref<string | null>(null)
  const isLoadingMainFeed = ref(false)
  const mainFeedError = ref<string | null>(null)
  const isRefreshingMainFeed = ref(false)
  const savedPostIds = ref<number[]>([])
  const savedPostsNextPageUrl = ref<string | null>(null)
  const isLoadingSavedPosts = ref(false)
  const savedPostsError = ref<string | null>(null)
  const hasFetchedSavedPosts = ref(false)
  const searchResultPostIds = ref<number[]>([])
  const isLoadingSearchResults = ref(false)
  const searchError = ref<string | null>(null)
  const createPostError = ref<string | null>(null)
  const isCreatingPost = ref(false)

  function $reset() {
    mainFeedPostIds.value = []
    newPostIdsFromRefresh.value = []
    mainFeedNextCursor.value = null
    isLoadingMainFeed.value = false
    mainFeedError.value = null
    isRefreshingMainFeed.value = false
    savedPostIds.value = []
    savedPostsNextPageUrl.value = null
    isLoadingSavedPosts.value = false
    savedPostsError.value = null
    hasFetchedSavedPosts.value = false
    searchResultPostIds.value = []
    isLoadingSearchResults.value = false
    searchError.value = null
    createPostError.value = null
    isCreatingPost.value = false
  }

  // --- ACTIONS ---

  function handlePostDeletedSignal(postId: number) {
    console.log(`FeedStore: Received signal to delete post ID ${postId}`)
    mainFeedPostIds.value = mainFeedPostIds.value.filter((id) => id !== postId)
    newPostIdsFromRefresh.value = newPostIdsFromRefresh.value.filter((id) => id !== postId)
    savedPostIds.value = savedPostIds.value.filter((id) => id !== postId)
    searchResultPostIds.value = searchResultPostIds.value.filter((id) => id !== postId)
  }

  async function fetchFeed(url: string | null = null) {
    if (isLoadingMainFeed.value) return
    isLoadingMainFeed.value = true
    mainFeedError.value = null
    try {
      if (!authStore.isAuthenticated) throw new Error('Authentication required')
      const apiUrl = url || '/feed/'
      const response = await axiosInstance.get<CursorPaginatedResponse>(apiUrl)
      postsStore.addOrUpdatePosts(response.data.results)
      const newIds = response.data.results.map((post) => post.id)
      if (!url) mainFeedPostIds.value = newIds
      else mainFeedPostIds.value.push(...newIds)
      mainFeedNextCursor.value = response.data.next
    } catch (err: any) {
      mainFeedError.value = err.response?.data?.detail || err.message || 'Failed to fetch feed.'
    } finally {
      isLoadingMainFeed.value = false
    }
  }

  async function refreshMainFeed() {
    if (isRefreshingMainFeed.value) return
    const isInitialLoad = mainFeedPostIds.value.length === 0
    if (isInitialLoad) isLoadingMainFeed.value = true
    isRefreshingMainFeed.value = true
    mainFeedError.value = null
    try {
      if (!authStore.isAuthenticated) return
      const response = await axiosInstance.get<CursorPaginatedResponse>('/feed/')
      const freshPosts = response.data.results
      postsStore.addOrUpdatePosts(freshPosts)
      if (isInitialLoad) {
        mainFeedPostIds.value = freshPosts.map((p) => p.id)
        newPostIdsFromRefresh.value = []
      } else {
        const existingPostIds = new Set([...mainFeedPostIds.value, ...newPostIdsFromRefresh.value])
        const genuinelyNewPostIds = freshPosts
          .map((p) => p.id)
          .filter((id) => !existingPostIds.has(id))
        if (genuinelyNewPostIds.length > 0) {
          newPostIdsFromRefresh.value.unshift(...genuinelyNewPostIds)
        }
      }
      mainFeedNextCursor.value = response.data.next
    } catch (err: any) {
      if (isInitialLoad) mainFeedError.value = err.response?.data?.detail || 'Failed to load feed.'
    } finally {
      isRefreshingMainFeed.value = false
      if (isInitialLoad) isLoadingMainFeed.value = false
    }
  }

  async function fetchSavedPosts(url: string | null = null) {
    if (!url && hasFetchedSavedPosts.value) return
    if (isLoadingSavedPosts.value) return
    isLoadingSavedPosts.value = true
    savedPostsError.value = null
    try {
      if (!authStore.isAuthenticated) throw new Error('Authentication required')
      const apiUrl = url || '/posts/saved/'
      const response = await axiosInstance.get<OffsetPaginatedResponse>(apiUrl)
      postsStore.addOrUpdatePosts(response.data.results)
      const newIds = response.data.results.map((post) => post.id)
      if (!url) savedPostIds.value = newIds
      else savedPostIds.value.push(...newIds)
      savedPostsNextPageUrl.value = response.data.next
    } catch (err: any) {
      savedPostsError.value =
        err.response?.data?.detail || err.message || 'Failed to fetch saved posts.'
    } finally {
      isLoadingSavedPosts.value = false
      if (!url) hasFetchedSavedPosts.value = true
    }
  }

  async function searchPosts(query: string) {
    if (!query) {
      searchResultPostIds.value = []
      return
    }
    isLoadingSearchResults.value = true
    searchError.value = null
    try {
      const response = await axiosInstance.get<{ results: Post[] }>(`/posts/?search=${query}`)
      postsStore.addOrUpdatePosts(response.data.results)
      searchResultPostIds.value = response.data.results.map((post) => post.id)
    } catch (err: any) {
      searchError.value = err.response?.data?.detail || err.message || 'Failed to search posts.'
    } finally {
      isLoadingSearchResults.value = false
    }
  }

  async function createPost(postData: FormData): Promise<Post | null> {
    isCreatingPost.value = true
    createPostError.value = null
    try {
      const response = await axiosInstance.post<Post>('/posts/', postData)
      const newPost = { ...response.data, isLiking: false, isDeleting: false, isUpdating: false }
      postsStore.addOrUpdatePosts([newPost])
      mainFeedPostIds.value.unshift(newPost.id)
      profileStore.addPostToProfileFeed(newPost)
      groupStore.addPostToGroupFeed(newPost)
      return newPost
    } catch (err: any) {
      createPostError.value = 'An unexpected error occurred while creating the post.'
      return null
    } finally {
      isCreatingPost.value = false
    }
  }

  async function deletePost(postId: number): Promise<boolean> {
    postsStore.addOrUpdatePosts([{ id: postId, isDeleting: true } as Partial<Post>])
    try {
      await axiosInstance.delete(`/posts/${postId}/`)
      postsStore.removePost(postId)
      handlePostDeletedSignal(postId)
      return true
    } catch (err: any) {
      postsStore.addOrUpdatePosts([{ id: postId, isDeleting: false } as Partial<Post>])
      return false
    }
  }

  async function toggleLike(postId: number) {
    const post = postsStore.getPostById(postId)
    if (!post || post.isLiking) return
    const originalState = { is_liked_by_user: post.is_liked_by_user, like_count: post.like_count }
    const newLikeCount = (post.like_count ?? 0) + (post.is_liked_by_user ? -1 : 1)
    postsStore.addOrUpdatePosts([
      {
        id: postId,
        isLiking: true,
        is_liked_by_user: !post.is_liked_by_user,
        like_count: newLikeCount,
      } as Partial<Post>,
    ])
    try {
      const response = await axiosInstance.post<{ liked: boolean; like_count: number }>(
        `/content/${post.content_type_id}/${post.object_id}/like/`,
      )
      postsStore.addOrUpdatePosts([
        {
          id: postId,
          is_liked_by_user: response.data.liked,
          like_count: response.data.like_count,
        } as Partial<Post>,
      ])
    } catch (err) {
      postsStore.addOrUpdatePosts([{ id: postId, ...originalState } as Partial<Post>])
    } finally {
      postsStore.addOrUpdatePosts([{ id: postId, isLiking: false } as Partial<Post>])
    }
  }

  async function toggleSavePost(postId: number): Promise<void> {
    const post = postsStore.getPostById(postId)
    if (!post) return
    const originalIsSaved = post.is_saved
    postsStore.addOrUpdatePosts([{ id: postId, is_saved: !originalIsSaved } as Partial<Post>])
    try {
      const response = await axiosInstance.post<Post>(`/posts/${postId}/save/`)
      postsStore.addOrUpdatePosts([
        { id: postId, is_saved: response.data.is_saved } as Partial<Post>,
      ])
      if (response.data.is_saved) {
        if (!savedPostIds.value.includes(postId)) savedPostIds.value.unshift(postId)
      } else {
        savedPostIds.value = savedPostIds.value.filter((id) => id !== postId)
      }
    } catch (err) {
      postsStore.addOrUpdatePosts([{ id: postId, is_saved: originalIsSaved } as Partial<Post>])
    }
  }

  // Replace the castVote function in feed.ts with this one

  async function castVote(pollId: number, optionId: number) {
    const postsStore = usePostsStore()
    try {
      // This URL is now correct. It does NOT start with /api/.
      const url = `polls/${pollId}/options/${optionId}/vote/`

      const response = await axiosInstance.post<Post>(url, {})

      postsStore.addOrUpdatePosts([response.data])
    } catch (error) {
      console.error('Failed to cast vote:', error)
    }
  }

  async function handleNewPostSignal(postId: number) {
    try {
      const isAlreadyPresent =
        mainFeedPostIds.value.includes(postId) || newPostIdsFromRefresh.value.includes(postId)
      if (isAlreadyPresent) return
      const response = await axiosInstance.get<Post>(`/posts/${postId}/`)
      postsStore.addOrUpdatePosts([response.data])
      newPostIdsFromRefresh.value.unshift(response.data.id)
    } catch (error) {
      console.error(`FeedStore: Failed to fetch full post data for ID ${postId}.`, error)
    }
  }

  // --- UPDATED RETURN STATEMENT ---
  return {
    mainFeedPostIds,
    mainFeedNextCursor,
    isLoadingMainFeed,
    mainFeedError,
    newPostIdsFromRefresh,
    savedPostIds,
    savedPostsNextPageUrl,
    isLoadingSavedPosts,
    savedPostsError,
    hasFetchedSavedPosts,
    searchResultPostIds,
    isLoadingSearchResults,
    searchError,
    createPostError,
    isCreatingPost,
    fetchFeed,
    refreshMainFeed,
    fetchNextPageOfMainFeed: () => fetchFeed(mainFeedNextCursor.value),
    showNewPosts: () => {
      mainFeedPostIds.value.unshift(...newPostIdsFromRefresh.value)
      newPostIdsFromRefresh.value = []
    },
    fetchSavedPosts,
    fetchNextPageOfSavedPosts: () => fetchSavedPosts(savedPostsNextPageUrl.value),
    searchPosts,
    createPost,
    deletePost,
    toggleLike,
    toggleSavePost,
    castVote, // Expose the new function
    $reset,
    handleNewPostSignal,
    handlePostDeletedSignal,
  }
})
