<script setup lang="ts">
import { ref, watch } from 'vue';
import { useModerationStore } from '@/stores/moderation';

const props = defineProps<{
  isOpen: boolean;
  target: { ct_id: number; obj_id: number; } | null;
}>();

const emit = defineEmits(['close']);

const moderationStore = useModerationStore();

const selectedReason = ref('');
const reportDetails = ref('');
const localValidationError = ref(''); // For form validation before submitting

const reasonOptions = [
  { value: 'SPAM', label: 'Spam or Misleading' },
  { value: 'HARASSMENT', label: 'Harassment or Bullying' },
  { value: 'HATE_SPEECH', label: 'Hate Speech' },
  { value: 'VIOLENCE', label: 'Violence or Graphic Content' },
  { value: 'OTHER', label: 'Other' },
];

const handleSubmit = async () => {
  localValidationError.value = '';
  if (!selectedReason.value) {
    localValidationError.value = 'Please select a reason for the report.';
    return;
  }
  if (selectedReason.value === 'OTHER' && !reportDetails.value.trim()) {
    localValidationError.value = "Details are required when selecting 'Other'.";
    return;
  }
  if (!props.target) {
    localValidationError.value = "Cannot submit report: target is missing.";
    return;
  }

  const success = await moderationStore.submitReport({
    ct_id: props.target.ct_id,
    obj_id: props.target.obj_id,
    reason: selectedReason.value,
    details: reportDetails.value,
  });

  if (success) {
    setTimeout(() => {
      handleClose();
    }, 2500);
  }
};

const handleClose = () => {
  emit('close');
  setTimeout(() => {
    moderationStore.resetReportState();
  }, 300);
};

watch(() => props.isOpen, (newVal) => {
  if (!newVal) {
    selectedReason.value = '';
    reportDetails.value = '';
    localValidationError.value = '';
  }
});
</script>

<template>
  <div v-if="isOpen" class="fixed inset-0 bg-black bg-opacity-50 z-40 flex items-center justify-center p-4" @click.self="handleClose">
    <div class="bg-white rounded-lg shadow-xl w-full max-w-md" @click.stop>
      <div class="p-6">
        <div class="flex justify-between items-center mb-4">
          <h2 class="text-xl font-bold text-gray-800">Report Content</h2>
          <button @click="handleClose" class="text-gray-400 hover:text-gray-600">×</button>
        </div>

        <div v-if="moderationStore.submissionSuccess" class="text-center p-4 bg-green-100 text-green-700 rounded-md">
          <p class="font-bold">Thank you!</p>
          <p>Your report has been submitted successfully.</p>
        </div>

        <form v-else @submit.prevent="handleSubmit" class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Reason for reporting:</label>
            <select v-model="selectedReason" class="w-full p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500">
              <option disabled value="">Please select a reason</option>
              <option v-for="option in reasonOptions" :key="option.value" :value="option.value">
                {{ option.label }}
              </option>
            </select>
          </div>

          <div v-if="selectedReason === 'OTHER'">
            <label for="report-details" class="block text-sm font-medium text-gray-700">Details:</label>
            <textarea
              id="report-details"
              v-model="reportDetails"
              rows="3"
              class="mt-1 w-full p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
              placeholder="Please provide specific details about your report."
            ></textarea>
          </div>

          <!-- THIS IS THE CORRECTED ERROR/FEEDBACK BLOCK WITH THE CLOSING TAG -->
          <div v-if="localValidationError || moderationStore.submissionError"
               class="p-3 text-sm rounded-md"
               :class="{
                 'bg-yellow-100 border-l-4 border-yellow-500 text-yellow-800': moderationStore.submissionError?.includes('already reported'),
                 'bg-red-100 border-l-4 border-red-500 text-red-700': localValidationError || !moderationStore.submissionError?.includes('already reported')
               }">
            <p class="font-bold" v-if="moderationStore.submissionError?.includes('already reported')">
              Already Reported
            </p>
            <p>{{ localValidationError || moderationStore.submissionError }}</p>
            <p v-if="moderationStore.submissionError?.includes('already reported')" class="mt-1 text-xs">
              Our moderation team has been notified. Thank you for your vigilance.
            </p>
          </div>

          <div class="pt-4 flex justify-end gap-3">
            <button type="button" @click="handleClose" class="px-4 py-2 bg-gray-200 text-gray-800 rounded-md hover:bg-gray-300">
              Cancel
            </button>
            <button type="submit" :disabled="moderationStore.isSubmittingReport" class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-blue-300">
              {{ moderationStore.isSubmittingReport ? 'Submitting...' : 'Submit Report' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>