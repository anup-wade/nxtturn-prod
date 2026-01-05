// C:\Users\Vinay\Project\frontend\src\stores\moderation.ts

import { ref } from 'vue';
import { defineStore } from 'pinia';
import axiosInstance from '@/services/axiosInstance';
import type { AxiosError } from 'axios';

// Interface for the data we need to submit a report
interface ReportPayload {
  ct_id: number;
  obj_id: number;
  reason: string;
  details: string;
}

export const useModerationStore = defineStore('moderation', () => {
  // --- State ---
  const isSubmittingReport = ref(false);
  const submissionError = ref<string | null>(null);
  const submissionSuccess = ref(false);

  // --- Actions ---

  async function submitReport(payload: ReportPayload): Promise<boolean> {
    isSubmittingReport.value = true;
    submissionError.value = null;
    submissionSuccess.value = false;

    try {
      const url = `/content/${payload.ct_id}/${payload.obj_id}/report/`;
      const data = {
        reason: payload.reason,
        details: payload.details,
      };
      await axiosInstance.post(url, data);
      submissionSuccess.value = true;
      return true;

    } catch (error) {
      const axiosError = error as AxiosError<Record<string, any>>;
      
      // --- THIS IS THE NEW, ROBUST ERROR HANDLING LOGIC ---
      let errorMessage = 'An unexpected error occurred while submitting the report.';

      if (axiosError.response && axiosError.response.data) {
        const errorData = axiosError.response.data;
        
        // Handle DRF's standard 'detail' key for general errors
        if (errorData.detail) {
          const detail = errorData.detail;
          errorMessage = Array.isArray(detail) ? detail[0] : String(detail);
        } 
        // Handle DRF's validation errors (usually an object of field names)
        else if (typeof errorData === 'object' && Object.keys(errorData).length > 0) {
          errorMessage = Object.values(errorData).flat().join(' ');
        }
      }
      submissionError.value = errorMessage;
      // --- END OF CORRECTION ---

      console.error("Report submission failed:", error);
      return false;

    } finally {
      isSubmittingReport.value = false;
    }
  }

  function resetReportState() {
    isSubmittingReport.value = false;
    submissionError.value = null;
    submissionSuccess.value = false;
  }

  return {
    isSubmittingReport,
    submissionError,
    submissionSuccess,
    submitReport,
    resetReportState,
  };
});