import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import axiosInstance from '@/services/axiosInstance'
import { useFeedStore } from './feed'
import { useProfileStore } from './profile'

// Real-time services
import { notificationService } from '@/services/notificationService'
import { useNotificationStore } from './notification'

// --------------------
// Types
// --------------------
export interface User {
  id: number
  username: string
  first_name: string
  last_name: string
  email: string
  date_joined: string
  picture: string | null
}

interface RegistrationData {
  email?: string
  username?: string
  password1?: string
  password2?: string
}

// --------------------
// Store
// --------------------
export const useAuthStore = defineStore('auth', () => {
  // State
  const authToken = ref<string | null>(localStorage.getItem('authToken'))
  const currentUser = ref<User | null>(null)
  const isLoading = ref<boolean>(false)

  // Getters
  const isAuthenticated = computed(() => !!authToken.value)
  const userDisplay = computed(() => currentUser.value?.username || 'Guest')

  // --------------------
  // Helpers
  // --------------------
  function setToken(token: string | null) {
    authToken.value = token

    if (token) {
      localStorage.setItem('authToken', token)
      axiosInstance.defaults.headers.common['Authorization'] = `Token ${token}`
    } else {
      localStorage.removeItem('authToken')
      delete axiosInstance.defaults.headers.common['Authorization']
      currentUser.value = null
    }
  }

  function setUser(user: User | null) {
    currentUser.value = user
  }

  function updateCurrentUserPicture(newPictureUrl: string | null) {
    if (currentUser.value) {
      currentUser.value.picture = newPictureUrl
    }
  }

  // --------------------
  // Actions
  // --------------------
  async function login(credentials: { username: string; password: string }) {
    isLoading.value = true
    try {
      const response = await axiosInstance.post('/auth/login/', credentials)

      if (!response.data?.key) {
        throw new Error('Login response missing auth token')
      }

      setToken(response.data.key)
      await fetchUserProfile()

      // Start WebSocket + notifications
      notificationService.connect()
      const notificationStore = useNotificationStore()
      await notificationStore.fetchUnreadCount()

      return true
    } catch (error) {
      setToken(null)
      setUser(null)
      console.error('Login failed:', error)
      throw error
    } finally {
      isLoading.value = false
    }
  }

  async function logout() {
    // Disconnect realtime services
    notificationService.disconnect()
    useNotificationStore().resetState()

    try {
      await axiosInstance.post('/auth/logout/')
    } catch (error) {
      console.warn('Backend logout failed, continuing client logout:', error)
    } finally {
      setToken(null)
      currentUser.value = null
      window.location.href = '/login'
    }
  }

  async function fetchUserProfile() {
    if (!authToken.value) return

    try {
      const response = await axiosInstance.get<User>('/auth/user/')
      setUser(response.data)
    } catch (error: any) {
      console.error('Failed to fetch user profile:', error)

      if (error.response?.status === 401) {
        await logout()
      } else {
        setUser(null)
      }
    }
  }

  async function register(registrationData: RegistrationData) {
    isLoading.value = true
    try {
      // IMPORTANT:
      // This becomes /api/auth/registration/ automatically
      await axiosInstance.post('/auth/registration/', registrationData)
    } catch (error) {
      console.error('Backend registration failed!', error)
      throw error
    } finally {
      isLoading.value = false
    }
  }

  async function initializeAuth() {
    const storedToken = localStorage.getItem('authToken')

    if (storedToken && !authToken.value) {
      setToken(storedToken)
    }

    if (authToken.value && !currentUser.value) {
      await fetchUserProfile()

      if (currentUser.value) {
        notificationService.connect()
        await useNotificationStore().fetchUnreadCount()
      }
    }
  }

  function resetAuthState() {
    notificationService.disconnect()
    useNotificationStore().resetState()
    authToken.value = null
    currentUser.value = null
    console.log('Auth state reset')
  }

  // --------------------
  // Expose
  // --------------------
  return {
    authToken,
    currentUser,
    isAuthenticated,
    userDisplay,
    isLoading,
    login,
    logout,
    register,
    fetchUserProfile,
    initializeAuth,
    setToken,
    setUser,
    updateCurrentUserPicture,
    resetAuthState,
  }
})

