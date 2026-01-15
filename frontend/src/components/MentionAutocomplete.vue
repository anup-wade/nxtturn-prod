<script setup lang="ts">
import { ref, watch } from 'vue';
import { debounce } from 'lodash-es';
import axiosInstance from '@/services/axiosInstance';
import { getAvatarUrl } from '@/utils/avatars';
import type { User } from '@/stores/auth';

const props = defineProps<{
  modelValue: string;
  placeholder?: string;
  rows?: number;
}>();

const emit = defineEmits(['update:modelValue']);

defineExpose({ blur: () => textareaRef.value?.blur(), focus: () => textareaRef.value?.focus() });

const textareaRef = ref<HTMLTextAreaElement | null>(null);
const showDropdown = ref(false);
const isLoading = ref(false);
const searchResults = ref<User[]>([]);
const activeIndex = ref(-1);

const handleInput = (event: Event) => {
  const target = event.target as HTMLTextAreaElement;
  emit('update:modelValue', target.value);
  checkForMention(target.value, target.selectionStart);
};

const searchUsers = debounce(async (query: string) => {
  if (query.length < 1) {
    searchResults.value = [];
    return;
  }
  isLoading.value = true;
  try {
    const response = await axiosInstance.get('/search/users/', {
      params: { q: query, page_size: 5 }
    });
    searchResults.value = response.data.results;
  } catch (error) {
    console.error("Failed to search for users:", error);
    searchResults.value = [];
  } finally {
    isLoading.value = false;
  }
}, 300);

const checkForMention = (text: string, cursorPosition: number) => {
  const textBeforeCursor = text.slice(0, cursorPosition);
  const mentionMatch = textBeforeCursor.match(/@([\w.-]*)$/);

  if (mentionMatch) {
    showDropdown.value = true;
    activeIndex.value = -1;
    searchUsers(mentionMatch[1]); 
  } else {
    showDropdown.value = false;
  }
};

const selectUser = (user: User) => {
  if (!textareaRef.value) return;

  const currentText = props.modelValue;
  const cursorPosition = textareaRef.value.selectionStart;
  const textBeforeCursor = currentText.slice(0, cursorPosition);
  const mentionStartIndex = textBeforeCursor.lastIndexOf('@');

  if (mentionStartIndex !== -1) {
    const textBeforeMention = currentText.slice(0, mentionStartIndex);
    const textAfterCursor = currentText.slice(cursorPosition);
    const newText = `${textBeforeMention}@${user.username} ${textAfterCursor}`;
    emit('update:modelValue', newText);
    const newCursorPosition = (textBeforeMention + `@${user.username} `).length;
    setTimeout(() => {
        if(textareaRef.value) {
            textareaRef.value.focus();
            textareaRef.value.selectionStart = textareaRef.value.selectionEnd = newCursorPosition;
        }
    }, 0);
  }
  
  showDropdown.value = false;
};

const handleKeydown = (event: KeyboardEvent) => {
  if (!showDropdown.value || searchResults.value.length === 0) return;

  if (event.key === 'ArrowDown') {
    event.preventDefault();
    activeIndex.value = (activeIndex.value + 1) % searchResults.value.length;
  } else if (event.key === 'ArrowUp') {
    event.preventDefault();
    activeIndex.value = (activeIndex.value - 1 + searchResults.value.length) % searchResults.value.length;
  } else if (event.key === 'Enter' || event.key === 'Tab') {
    if (activeIndex.value !== -1) {
      event.preventDefault();
      selectUser(searchResults.value[activeIndex.value]);
    }
  } else if (event.key === 'Escape') {
    event.preventDefault();
    showDropdown.value = false;
  }
};

// === THIS IS THE FIX for the deprecation warning ===
watch(showDropdown, (isOpen) => {
    const listener = (e: MouseEvent) => {
      // Use the 'e' parameter that is passed into the function, not the global 'event'.
      const rootEl = (e.target as HTMLElement).closest('.relative');
      if (!rootEl || !rootEl.contains(e.target as Node)) {
        showDropdown.value = false;
      }
    };
    if (isOpen) {
        document.addEventListener('click', listener, true);
    } else {
        document.removeEventListener('click', listener, true);
    }
});
// === END OF FIX ===
</script>

<template>
  <div class="relative w-full">
    <textarea
      ref="textareaRef"
      :value="modelValue"
      @input="handleInput"
      @keydown="handleKeydown"
      :placeholder="placeholder"
      :rows="rows || 3"
      class="w-full p-3 text-base text-gray-800 bg-gray-100 border-transparent rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all"
    ></textarea>
    
    <div
      v-if="showDropdown"
      class="absolute top-full mt-1 w-full rounded-md shadow-lg bg-white ring-1 ring-black ring-opacity-5 z-20"
    >
      <ul class="max-h-60 overflow-auto py-1 text-base">
        <li v-if="isLoading" class="px-4 py-2 text-sm text-gray-500">Searching...</li>
        <li v-else-if="searchResults.length === 0" class="px-4 py-2 text-sm text-gray-500">No users found.</li>
        <li
          v-for="(user, index) in searchResults"
          :key="user.id"
          @click="selectUser(user)"
          class="flex items-center gap-3 px-4 py-2 text-sm cursor-pointer"
          :class="{ 'bg-blue-100': index === activeIndex }"
        >
          <img 
            :src="getAvatarUrl(user.picture, user.first_name, user.last_name)" 
            alt="user avatar" 
            class="w-8 h-8 rounded-full object-cover"
          >
          <span class="font-medium text-gray-900">{{ user.username }}</span>
          <span class="text-gray-500">{{ user.first_name }} {{ user.last_name }}</span>
        </li>
      </ul>
    </div>
  </div>
</template>