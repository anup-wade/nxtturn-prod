// C:\Users\Vinay\Project\frontend\src/stores/profile.ts
import { ref } from 'vue'
import { defineStore } from 'pinia'
import axiosInstance from '@/services/axiosInstance'
import { useAuthStore } from '@/stores/auth'
import { usePostsStore } from '@/stores/posts'
import type {
  UserProfile,
  ProfileUpdatePayload,
  Post,
  PostAuthor,
  EducationEntry,
  Experience,
} from '@/types'

// --- FILE-SPECIFIC TYPES ---
interface PaginatedPostsResponse {
  count: number
  next: string | null
  previous: string | null
  results: Post[]
}

export const useProfileStore = defineStore('profile', () => {
  const authStore = useAuthStore()
  const postsStore = usePostsStore()

  const currentProfile = ref<UserProfile | null>(null)
  const postIdsByUsername = ref<{ [username: string]: number[] }>({})
  const nextPageUrlByUsername = ref<{ [username: string]: string | null }>({})
  const profilesByUsername = ref<{ [username: string]: UserProfile }>({})
  const hasFetchedPostsByUsername = ref<{ [username: string]: boolean }>({})
  const isLoadingProfile = ref(false)
  const isLoadingPosts = ref(false)
  const errorProfile = ref<string | null>(null)
  const errorPosts = ref<string | null>(null)
  const isLoadingFollow = ref(false)

  // This ref now correctly uses the type from UserProfile
  const relationshipStatus = ref<UserProfile['relationship_status']>(null)

  function handlePostDeletedSignal(postId: number) {
    for (const username in postIdsByUsername.value) {
      postIdsByUsername.value[username] = postIdsByUsername.value[username].filter(
        (id) => id !== postId,
      )
    }
  }

  async function fetchProfile(username: string) {
    isLoadingProfile.value = true
    errorProfile.value = null
    try {
      const response = await axiosInstance.get<UserProfile>(`/profiles/${username}/`)
      const profile = response.data

      profilesByUsername.value[username] = profile
      currentProfile.value = profile
      relationshipStatus.value = profile.relationship_status
    } catch (err: any) {
      errorProfile.value = err.response?.data?.detail || `Profile not found for user "${username}".`
      relationshipStatus.value = null
    } finally {
      isLoadingProfile.value = false
    }
  }

  async function fetchUserPosts(username: string, url: string | null = null) {
    if (!url && hasFetchedPostsByUsername.value[username]) return
    if (isLoadingPosts.value) return
    isLoadingPosts.value = true
    errorPosts.value = null
    const apiUrl = url || `/users/${username}/posts/`
    try {
      const response = await axiosInstance.get<PaginatedPostsResponse>(apiUrl)
      postsStore.addOrUpdatePosts(response.data.results)
      const newIds = response.data.results.map((post) => post.id)
      if (url) {
        postIdsByUsername.value[username] = [
          ...(postIdsByUsername.value[username] || []),
          ...newIds,
        ]
      } else {
        postIdsByUsername.value[username] = newIds
      }
      nextPageUrlByUsername.value[username] = response.data.next
      if (!url) hasFetchedPostsByUsername.value[username] = true
    } catch (err: any) {
      errorPosts.value = err.response?.data?.detail || 'Failed to fetch user posts.'
    } finally {
      isLoadingPosts.value = false
    }
  }

  async function refreshUserPosts(username: string) {
    const isInitialLoad = !hasFetchedPostsByUsername.value[username]
    if (isInitialLoad) isLoadingPosts.value = true
    errorPosts.value = null
    const apiUrl = `/users/${username}/posts/`
    try {
      const response = await axiosInstance.get<PaginatedPostsResponse>(apiUrl)
      const freshPosts = response.data.results
      postsStore.addOrUpdatePosts(freshPosts)
      postIdsByUsername.value[username] = freshPosts.map((p) => p.id)
      nextPageUrlByUsername.value[username] = response.data.next
      hasFetchedPostsByUsername.value[username] = true
    } catch (err: any) {
      errorPosts.value = err.response?.data?.detail || 'Failed to refresh user posts.'
    } finally {
      if (isInitialLoad) isLoadingPosts.value = false
    }
  }

  function addPostToProfileFeed(post: Post) {
    const username = post.author.username
    if (postIdsByUsername.value[username]) {
      postIdsByUsername.value[username].unshift(post.id)
    }
  }

  async function updateProfilePicture(username: string, pictureFile: File) {
    const formData = new FormData()
    formData.append('picture', pictureFile)
    try {
      const response = await axiosInstance.patch<UserProfile>(`/profiles/${username}/`, formData)
      const updatedProfile = response.data

      // --- THIS IS THE FINAL FIX ---
      // 1. Update the local profile store state
      if (currentProfile.value && currentProfile.value.user.username === username) {
        currentProfile.value.picture = updatedProfile.picture
      }
      // 2. Sync with the global authStore (for the navbar)
      if (authStore.currentUser?.username === username) {
        authStore.updateCurrentUserPicture(updatedProfile.picture)
      }
      // 3. Sync with the global postsStore (for all feed/post items)
      if (authStore.currentUser) {
        postsStore.updateAuthorDetailsInPosts(authStore.currentUser.id, {
          picture: updatedProfile.picture,
        })
      }
      // --- END OF FINAL FIX ---
    } catch (err: any) {
      throw new Error(
        err.response?.data?.picture?.join(' ') ||
          err.response?.data?.detail ||
          'Failed to update picture.',
      )
    }
  }

  async function removeProfilePicture(username: string) {
    try {
      const response = await axiosInstance.patch<UserProfile>(`/profiles/${username}/`, {
        picture: null,
      })
      const updatedProfile = response.data

      // --- THIS IS THE FINAL FIX ---
      // 1. Update the local profile store state
      if (currentProfile.value && currentProfile.value.user.username === username) {
        currentProfile.value.picture = updatedProfile.picture
      }
      // 2. Sync with the global authStore (for the navbar)
      if (authStore.currentUser?.username === username) {
        authStore.updateCurrentUserPicture(updatedProfile.picture)
      }
      // 3. Sync with the global postsStore (for all feed/post items)
      if (authStore.currentUser) {
        postsStore.updateAuthorDetailsInPosts(authStore.currentUser.id, {
          picture: updatedProfile.picture,
        })
      }
      // --- END OF FINAL FIX ---
    } catch (err: any) {
      console.error('Failed to remove profile picture:', err)
      throw new Error(
        err.response?.data?.detail || 'An unexpected error occurred while removing the picture.',
      )
    }
  }

  // --- REFACTORED ACTIONS ---

  async function followUser(usernameToFollow: string) {
    if (isLoadingFollow.value) return
    isLoadingFollow.value = true
    try {
      await axiosInstance.post(`/users/${usernameToFollow}/follow/`)
      await fetchProfile(usernameToFollow)
    } finally {
      isLoadingFollow.value = false
    }
  }

  async function unfollowUser(usernameToUnfollow: string) {
    if (isLoadingFollow.value) return
    isLoadingFollow.value = true
    try {
      await axiosInstance.delete(`/users/${usernameToUnfollow}/follow/`)
      await fetchProfile(usernameToUnfollow)
    } finally {
      isLoadingFollow.value = false
    }
  }

  async function sendConnectRequest(username: string) {
    if (!currentProfile.value) return
    try {
      const receiverId = currentProfile.value.user.id
      await axiosInstance.post('/connections/requests/', { receiver: receiverId })
      await fetchProfile(username)
    } catch (error: any) {
      console.error('Failed to send connection request:', error)
      alert(error.response?.data?.detail || 'Could not send request.')
    }
  }

  async function acceptConnectRequest(username: string) {
    try {
      await axiosInstance.post(`/users/${username}/accept-request/`)
      await fetchProfile(username)
    } catch (error: any) {
      console.error('Failed to accept connection request:', error)
      alert(error.response?.data?.detail || 'Could not accept request.')
    }
  }

  async function updateProfile(username: string, payload: ProfileUpdatePayload) {
    try {
      await axiosInstance.patch<UserProfile>(`/profiles/${username}/`, payload)
      await fetchProfile(username)
    } catch (err: any) {
      console.error('Failed to update profile:', err)
      throw new Error(
        err.response?.data?.detail || 'An unexpected error occurred while updating the profile.',
      )
    }
  }

  // --- EDUCATION ACTIONS ---

  async function addEducation(username: string, educationData: Omit<EducationEntry, 'id'>) {
    try {
      const response = await axiosInstance.post<EducationEntry>(
        `/profile/education/`, // <-- DEFINITIVE CORRECT URL
        educationData,
      )
      const newEducation = response.data
      if (currentProfile.value) {
        currentProfile.value.education.unshift(newEducation)
      }
    } catch (err: any) {
      console.error('Failed to add education:', err)
      throw new Error(err.response?.data?.detail || 'Failed to add education entry.')
    }
  }

  async function updateEducation(
    username: string,
    educationId: number,
    educationData: Omit<EducationEntry, 'id'>,
  ) {
    try {
      const response = await axiosInstance.put<EducationEntry>(
        `/profile/education/${educationId}/`, // <-- DEFINITIVE CORRECT URL
        educationData,
      )
      const updatedEducation = response.data
      if (currentProfile.value) {
        const index = currentProfile.value.education.findIndex((edu) => edu.id === educationId)
        if (index !== -1) {
          currentProfile.value.education[index] = updatedEducation
        }
      }
    } catch (err: any) {
      console.error('Failed to update education:', err)
      throw new Error(err.response?.data?.detail || 'Failed to update education entry.')
    }
  }

  async function deleteEducation(username: string, educationId: number) {
    try {
      await axiosInstance.delete(`/profile/education/${educationId}/`) // <-- DEFINITIVE CORRECT URL
      if (currentProfile.value) {
        currentProfile.value.education = currentProfile.value.education.filter(
          (edu) => edu.id !== educationId,
        )
      }
    } catch (err: any) {
      console.error('Failed to delete education:', err)
      throw new Error(err.response?.data?.detail || 'Failed to delete education entry.')
    }
  }

  // --- EXPERIENCE ACTIONS ---

  async function addExperience(username: string, experienceData: Omit<Experience, 'id'>) {
    try {
      const response = await axiosInstance.post<Experience>(`/profile/experience/`, experienceData)
      const newExperience = response.data
      if (currentProfile.value) {
        // Add to the top of the list
        currentProfile.value.experience.unshift(newExperience)
      }
    } catch (err: any) {
      console.error('Failed to add experience:', err)
      throw new Error(err.response?.data?.detail || 'Failed to add experience entry.')
    }
  }

  async function updateExperience(
    username: string,
    experienceId: number,
    experienceData: Omit<Experience, 'id'>,
  ) {
    try {
      const response = await axiosInstance.put<Experience>(
        `/profile/experience/${experienceId}/`,
        experienceData,
      )
      const updatedExperience = response.data
      if (currentProfile.value) {
        const index = currentProfile.value.experience.findIndex((exp) => exp.id === experienceId)
        if (index !== -1) {
          currentProfile.value.experience[index] = updatedExperience
        }
      }
    } catch (err: any) {
      console.error('Failed to update experience:', err)
      throw new Error(err.response?.data?.detail || 'Failed to update experience entry.')
    }
  }

  async function deleteExperience(username: string, experienceId: number) {
    try {
      await axiosInstance.delete(`/profile/experience/${experienceId}/`)
      if (currentProfile.value) {
        currentProfile.value.experience = currentProfile.value.experience.filter(
          (exp) => exp.id !== experienceId,
        )
      }
    } catch (err: any) {
      console.error('Failed to delete experience:', err)
      throw new Error(err.response?.data?.detail || 'Failed to delete experience entry.')
    }
  }

  function $reset() {
    currentProfile.value = null
    postIdsByUsername.value = {}
    nextPageUrlByUsername.value = {}
    profilesByUsername.value = {}
    hasFetchedPostsByUsername.value = {}
    isLoadingProfile.value = false
    isLoadingPosts.value = false
    errorProfile.value = null
    errorPosts.value = null
    isLoadingFollow.value = false
    relationshipStatus.value = null
  }

  return {
    currentProfile,
    postIdsByUsername,
    nextPageUrlByUsername,
    isLoadingProfile,
    isLoadingPosts,
    errorProfile,
    errorPosts,
    isLoadingFollow,
    fetchProfile,
    fetchUserPosts,
    refreshUserPosts,
    fetchNextPageOfUserPosts: (username: string) =>
      fetchUserPosts(username, nextPageUrlByUsername.value[username]),
    updateProfilePicture,
    followUser,
    unfollowUser,
    addPostToProfileFeed,
    handlePostDeletedSignal,
    updateProfile,
    removeProfilePicture,
    $reset,
    relationshipStatus,
    sendConnectRequest,
    acceptConnectRequest,
    addEducation,
    updateEducation,
    deleteEducation,
    addExperience,
    updateExperience,
    deleteExperience,
  }
})
