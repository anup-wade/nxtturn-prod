<script setup lang="ts">
import { getAvatarUrl } from '@/utils/avatars';
import { computed, ref, watch } from 'vue';
import { format } from 'date-fns';
import type { Comment } from '@/stores/comment';
import { useAuthStore } from '@/stores/auth';
import { useCommentStore } from '@/stores/comment';
import MentionAutocomplete from './MentionAutocomplete.vue';

// Using compiler macros, so defineProps doesn't need to be imported
const props = defineProps<{
  comment: Comment;
  parentPostType: string;
  parentObjectId: number;
  parentPostActualId: number;
  currentDepth?: number;
}>();

// --- 1. DEFINE THE EMIT ---
const emit = defineEmits<{
  (e: 'report-content', payload: { content_type: string, content_type_id: number, object_id: number }): void
}>();

const MAX_REPLY_DEPTH = 1;
const effectiveDepth = computed(() => props.currentDepth ?? 0);

const authStore = useAuthStore();
const commentStore = useCommentStore();

const isEditing = ref(false);
const editableContent = ref('');
const showReplyForm = ref(false);
const replyContent = ref('');
const isSubmittingReply = ref(false);
const replyError = ref<string | null>(null);

const isCommentAuthor = computed(() => authStore.currentUser?.id === props.comment.author.id);
const canReplyToThisComment = computed(() => effectiveDepth.value < MAX_REPLY_DEPTH);
const directReplies = computed(() => {
  const postKey = `${props.parentPostType}_${props.parentObjectId}`;
  return (commentStore.commentsByPost[postKey] || []).filter(reply => reply.parent === props.comment.id);
});

// --- 2. CREATE THE HANDLER METHOD ---
function handleReportClick() {
  if (typeof props.comment.comment_content_type_id !== 'number') return;

  emit('report-content', {
    content_type: 'comment', // Hardcoded as this component is always a comment
    content_type_id: props.comment.comment_content_type_id,
    object_id: props.comment.id
  });
}

// --- All other existing functions remain the same ---
function linkifyContent(text: string): string {
  if (!text) return '';
  const urlRegex = /(\b(https?|ftp|file):\/\/[-A-Z0-9+&@#\/%?=~_|!:,.;]*[-A-Z0-9+&@#\/%=~_|])|(\bwww\.[-A-Z0-9+&@#\/%?=~_|!:,.;]*[-A-Z0-9+&@#\/%=~_|])/ig;
  const mentionRegex = /@(\w+)/g;
  let linkedText = text.replace(urlRegex, url => `<a href="${url.startsWith('www.') ? 'http://' + url : url}" target="_blank" rel="noopener noreferrer" class="text-blue-500 hover:underline">${url}</a>`);
  linkedText = linkedText.replace(mentionRegex, (match, username) => {
    const profileUrl = `/profile/${username}`;
    return `<a href="${profileUrl}" class="font-semibold text-blue-600 hover:underline">${match}</a>`;
  });
  return linkedText;
}

function toggleEditMode(edit: boolean) {
  isEditing.value = edit;
  if (edit) {
    showReplyForm.value = false;
    editableContent.value = props.comment.content;
  }
}

function toggleReplyForm() {
  if (!showReplyForm.value && !canReplyToThisComment.value) {
    return alert(`Replies are limited to ${MAX_REPLY_DEPTH} level(s).`);
  }
  showReplyForm.value = !showReplyForm.value;
  if (showReplyForm.value) {
    isEditing.value = false;
    replyContent.value = '';
    replyError.value = null;
  }
}

async function saveEdit() {
  if (!editableContent.value.trim() || editableContent.value.trim() === props.comment.content) {
    return toggleEditMode(false);
  }
  await commentStore.editComment(props.comment.id, editableContent.value, props.parentPostType, props.parentObjectId);
  toggleEditMode(false);
}

async function deleteComment() {
  if (window.confirm('Are you sure you want to delete this comment?')) {
    await commentStore.deleteComment(props.comment.id, props.parentPostType, props.parentObjectId, props.parentPostActualId);
  }
}

async function submitReply() {
  if (!replyContent.value.trim()) {
    return replyError.value = "Reply cannot be empty.";
  }
  isSubmittingReply.value = true;
  replyError.value = null;
  try {
    await commentStore.createComment(props.parentPostType, props.parentObjectId, replyContent.value, props.parentPostActualId, props.comment.id);
    toggleReplyForm();
  } catch (error: any) {
    replyError.value = error.message || "Failed to submit reply.";
  } finally {
    isSubmittingReply.value = false;
  }
}

async function handleToggleCommentLike() {
  if (!authStore.isAuthenticated) return alert("Please log in to like comments.");
  if (typeof props.comment.comment_content_type_id !== 'number') return;
  await commentStore.toggleLikeOnComment(props.comment.id, props.comment.comment_content_type_id, props.parentPostType, props.parentObjectId);
}
</script>

<template>
  <div class="flex items-start gap-3 py-3 border-b border-gray-200 last:border-b-0">
    <img :src="getAvatarUrl(comment.author.picture, comment.author.first_name, comment.author.last_name)"
      alt="comment author avatar" class="w-8 h-8 rounded-full object-cover flex-shrink-0 bg-gray-200">
    <div class="flex-grow">
      <div class="bg-gray-100 rounded-lg p-3">
        <div class="flex items-baseline justify-between">
          <span class="font-bold text-sm text-gray-800">{{ props.comment.author.username }}</span>
          <span v-if="!isEditing" class="text-xs text-gray-500">{{ format(new Date(props.comment.created_at), 'MMM d')
            }}</span>
        </div>
        <div v-if="!isEditing" class="text-sm text-gray-700 mt-1 whitespace-pre-wrap"
          v-html="linkifyContent(props.comment.content)"></div>
        <form v-else @submit.prevent="saveEdit" class="mt-1">
          <MentionAutocomplete v-model="editableContent" placeholder="Edit your comment..." :rows="2" class="text-sm" />
          <div class="flex justify-end gap-2 mt-2">
            <button @click="toggleEditMode(false)" type="button"
              class="text-xs font-semibold text-gray-600 px-3 py-1 rounded-full hover:bg-gray-200">Cancel</button>
            <button type="submit"
              class="text-xs font-semibold text-white bg-blue-500 px-3 py-1 rounded-full hover:bg-blue-600">Save</button>
          </div>
        </form>
      </div>
      <!-- 3. ADD THE REPORT BUTTON TO THE TEMPLATE -->
      <div v-if="!isEditing" class="flex items-center gap-4 mt-1 px-3 text-xs font-semibold text-gray-500">
        <button @click="handleToggleCommentLike" class="hover:underline"
          :class="{ 'text-blue-600 font-bold': props.comment.is_liked_by_user }">Like ({{ props.comment.like_count ?? 0
          }})</button>
        <button v-if="canReplyToThisComment" @click="toggleReplyForm" class="hover:underline">Reply</button>
        <button v-if="isCommentAuthor" @click="toggleEditMode(true)" class="hover:underline">Edit</button>
        <button v-if="isCommentAuthor" @click="deleteComment" class="hover:underline text-red-500">Delete</button>
        <!-- This is the new button -->
        <button v-if="authStore.isAuthenticated && !isCommentAuthor" @click="handleReportClick"
          class="hover:underline">Report</button>
      </div>
      <!-- END OF ADDITION -->
      <div v-if="showReplyForm" class="mt-2">
        <form @submit.prevent="submitReply">
          <MentionAutocomplete v-model="replyContent" placeholder="Write a reply... Mention with @" :rows="2"
            class="text-sm" />
          <div v-if="replyError" class="text-red-600 text-xs mt-1">{{ replyError }}</div>
          <div class="flex justify-end gap-2 mt-2">
            <button @click="toggleReplyForm" type="button"
              class="text-xs font-semibold text-gray-600 px-3 py-1 rounded-full hover:bg-gray-200">Cancel</button>
            <button type="submit" :disabled="isSubmittingReply"
              class="text-xs font-semibold text-white bg-blue-500 px-3 py-1 rounded-full hover:bg-blue-600 disabled:bg-blue-300">{{
                isSubmittingReply ? 'Replying...' : 'Reply' }}</button>
          </div>
        </form>
      </div>
      <div v-if="directReplies.length > 0" class="mt-3 pl-3 border-l-2 border-gray-200">
        <!-- The re-emit logic will be added to PostItem, which renders this component -->
        <CommentItem v-for="reply in directReplies" :key="reply.id" :comment="reply"
          :parentPostType="props.parentPostType" :parentObjectId="props.parentObjectId"
          :parentPostActualId="props.parentPostActualId" :currentDepth="effectiveDepth + 1"
          @report-content="emit('report-content', $event)" />
      </div>
    </div>
  </div>
</template>