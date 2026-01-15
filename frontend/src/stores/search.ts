// C:\Users\Vinay\Project\frontend\src\stores\search.ts

import { ref } from 'vue';
import { defineStore } from 'pinia';
import axiosInstance from '@/services/axiosInstance';
import type { User } from '@/stores/auth';

// --- Interface for API Response ---
// This store now only cares about user responses.
interface PaginatedUserResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: User[];
}

export const useSearchStore = defineStore('search', () => {
  // --- State ---
  // This store now only holds state for USER search results.
  const userResults = ref<User[]>([]);
  const isLoadingUsers = ref(false);
  const userError = ref<string | null>(null);

  // --- Actions ---

  // We rename this action to `searchUsers` and make it public.
  // This is its only job now.
  async function searchUsers(query: string) {
    if (!query.trim()) {
        clearSearch();
        return;
    }
    isLoadingUsers.value = true;
    userError.value = null;
    try {
      // Assuming your user search endpoint is /search/users/. If it's just /search/, adjust here.
      const response = await axiosInstance.get<PaginatedUserResponse>('/search/users/', {
        params: { q: query }
      });
      userResults.value = response.data.results;
    } catch (err: any) {
      userError.value = err.response?.data?.detail || 'Failed to search for users.';
      userResults.value = [];
    } finally {
      isLoadingUsers.value = false;
    }
  }

  // A simple function to clear only the state managed by this store.
  function clearSearch() {
    userResults.value = [];
    userError.value = null;
  }

  // --- Return only what this store is responsible for ---
  return {
    // User Search State & Results
    userResults,
    isLoadingUsers,
    userError,
    
    // Actions
    searchUsers, // This is now the public action to call.
    clearSearch,
  };
});