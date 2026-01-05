// C:\Users\Vinay\Project\frontend\src\stores\auth.ts

import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import axiosInstance from '@/services/axiosInstance'
import { useFeedStore } from './feed'
import { useProfileStore } from './profile'

// --- NEW IMPORTS: Link the auth store to the real-time services ---
import { notificationService } from '@/services/notificationService'
import { useNotificationStore } from './notification'
// ------------------------------------------------------------------

// Define the shape of the User object.
export interface User {
  id: number
  username: string
  first_name: string
  last_name: string
  email: string // <--- FIX: Added this property
  date_joined: string
  picture: string | null
}

// Interface for registration data
interface RegistrationData {
  email?: string
  username?: string
  password1?: string
  password2?: string
}

// Define the store
export const useAuthStore = defineStore('auth', () => {
  // --- State ---
  const authToken = ref<string | null>(localStorage.getItem('authToken') || null)
  const currentUser = ref<User | null>(null)
  const isLoading = ref<boolean>(false)

  // --- Getters ---
  const isAuthenticated = computed(() => !!authToken.value)
  const userDisplay = computed(() => currentUser.value?.username || 'Guest')

  // --- Actions ---

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

  async function login(credentials: { username: string; password: any }) {
    isLoading.value = true
    try {
      const response = await axiosInstance.post('/auth/login/', credentials)
      if (response.data && response.data.key) {
        setToken(response.data.key)
        await fetchUserProfile()

        // --- NEW LOGIC ON SUCCESSFUL LOGIN ---
        notificationService.connect()
        const notificationStore = useNotificationStore()
        await notificationStore.fetchUnreadCount()
        // ------------------------------------

        return true
      } else {
        throw new Error('Login response did not contain an authentication key.')
      }
    } catch (error) {
      setToken(null)
      setUser(null)
      console.error('Store login action failed:', error)
      throw error
    } finally {
      isLoading.value = false
    }
  }

  async function logout() {
    // --- NEW: Cleanly disconnect WebSocket and reset stores before logging out ---
    notificationService.disconnect()
    const notificationStore = useNotificationStore()
    notificationStore.resetState()
    // -------------------------------------------------------------------------

    try {
      await axiosInstance.post('/auth/logout/')
    } catch (error: any) {
      console.error('Backend logout call failed (proceeding with client logout):', error)
    } finally {
      setToken(null)

      if (typeof window !== 'undefined') {
        window.location.href = '/login'
      }
    }
  }

  async function fetchUserProfile() {
    if (!authToken.value) return
    try {
      const response = await axiosInstance.get<User>('/auth/user/')
      if (response.data) setUser(response.data)
      else setUser(null)
    } catch (error: any) {
      console.error('Failed to fetch user profile:', error)
      if (error.response && error.response.status === 401) await logout()
      else setUser(null)
    }
  }

  async function register(registrationData: RegistrationData) {
    isLoading.value = true
    try {
      await axiosInstance.post('/auth/registration/', registrationData)
    } catch (error) {
      console.error('Backend registration failed!', error)
      throw error
    } finally {
      isLoading.value = false
    }
  }

  async function initializeAuth() {
    const tokenFromStorage = localStorage.getItem('authToken')
    if (tokenFromStorage && !authToken.value) setToken(tokenFromStorage)

    if (authToken.value && !currentUser.value) {
      await fetchUserProfile()

      // --- NEW LOGIC ON APP INITIALIZATION IF AUTHENTICATED ---
      if (currentUser.value) {
        notificationService.connect()
        const notificationStore = useNotificationStore()
        await notificationStore.fetchUnreadCount()
      }
      // --------------------------------------------------------
    }
  }

  function resetAuthState() {
    // --- NEW: Also disconnect WebSocket on multi-tab logout for a clean shutdown ---
    notificationService.disconnect()
    const notificationStore = useNotificationStore()
    notificationStore.resetState()
    // --------------------------------------------------------------------------

    authToken.value = null
    currentUser.value = null
    console.log('Client-side auth state has been reset by multi-tab sync.')
  }

  // --- Return state, getters, and actions ---
  return {
    authToken,
    currentUser,
    isAuthenticated,
    userDisplay,
    isLoading,
    setToken,
    setUser,
    login,
    logout,
    fetchUserProfile,
    register,
    initializeAuth,
    updateCurrentUserPicture,
    resetAuthState,
  }
})
