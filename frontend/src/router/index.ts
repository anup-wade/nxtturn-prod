import { createRouter, createWebHistory } from 'vue-router'
import 'vue-router'
import { useAuthStore } from '@/stores/auth'
import CommunityLayout from '@/layouts/CommunityLayout.vue'
import ProfileLayout from '@/layouts/ProfileLayout.vue'
import ExploreLayout from '@/layouts/ExploreLayout.vue'
import axiosInstance from '@/services/axiosInstance'
import CheckEmailView from '../views/auth/CheckEmailView.vue'
import ForgotPasswordView from '../views/auth/ForgotPasswordView.vue'

declare module 'vue-router' {
  interface RouteMeta {
    requiresAuth?: boolean
    requiresGuest?: boolean
  }
}

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    // --- ROUTE GROUP 1: Uses the 3-Column Community Layout ---
    {
      path: '/',
      component: CommunityLayout,
      meta: { requiresAuth: true },
      children: [
        { path: '', name: 'feed', component: () => import('@/views/FeedView.vue') },
        {
          path: 'groups',
          name: 'group-list',
          component: () => import('@/views/GroupListAllView.vue'),
        },
        {
          path: 'groups/:slug',
          name: 'group-detail',
          component: () => import('@/views/GroupDetailView.vue'),
        },
        {
          path: 'groups/:slug/requests',
          name: 'group-requests',
          component: () => import('@/views/GroupRequestsView.vue'),
        },
        {
          path: 'saved-posts',
          name: 'saved-posts',
          component: () => import('@/views/SavedPostsView.vue'),
        },
        {
          path: 'notifications',
          name: 'notifications',
          component: () => import('@/views/NotificationsPage.vue'),
        },
        { path: 'search', name: 'search', component: () => import('@/views/SearchPage.vue') },
        {
          path: 'posts/:postId',
          name: 'single-post',
          component: () => import('@/views/SinglePostView.vue'),
        },
      ],
    },
    // --- ROUTE GROUP 2: Uses the Profile Layout ---
    {
      path: '/profile',
      component: ProfileLayout,
      meta: { requiresAuth: true },
      children: [
        { path: ':username', name: 'profile', component: () => import('@/views/ProfileView.vue') },
      ],
    },
    // --- ROUTE GROUP 3: Uses the Explore Layout ---
    {
      path: '/explore',
      component: ExploreLayout,
      meta: { requiresAuth: true },
      children: [{ path: '', name: 'explore', component: () => import('@/views/ExploreView.vue') }],
    },
    // --- ROUTE GROUP 4: Non-Layout Routes (Login/Register) ---
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/LoginView.vue'),
      meta: { requiresGuest: true },
    },
    {
      path: '/register',
      name: 'register',
      component: () => import('@/views/RegisterView.vue'),
      meta: { requiresGuest: true },
    },
    {
      path: '/auth/check-email',
      name: 'CheckEmail',
      component: CheckEmailView,
      meta: { requiresGuest: true },
    },
    {
      path: '/auth/forgot-password',
      name: 'ForgotPassword',
      component: ForgotPasswordView,
      meta: { requiresGuest: true },
    },
    // --- THIS IS THE NEW ROUTE WE ARE ADDING ---
    {
      path: '/auth/reset-password/:uid/:token',
      name: 'ResetPasswordConfirm',
      component: () => import('@/views/auth/ResetPasswordConfirmView.vue'),
      meta: { requiresGuest: true },
    },
  ],
})

// The beforeEach guard remains unchanged.
router.beforeEach(async (to, from, next) => {
  try {
    await axiosInstance.get('/health-check/', { timeout: 4000 })
  } catch (error) {
    // The interceptor will handle the offline toast.
  }

  const authStore = useAuthStore()
  await authStore.initializeAuth()
  const isAuthenticated = authStore.isAuthenticated

  if (to.meta.requiresAuth && !isAuthenticated) {
    next({ name: 'login' })
  } else if (to.meta.requiresGuest && isAuthenticated) {
    next({ name: 'feed' })
  } else {
    next()
  }
})

export default router
