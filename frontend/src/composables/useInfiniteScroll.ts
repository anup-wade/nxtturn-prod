// C:\Users\Vinay\Project\frontend\src\composables\useInfiniteScroll.ts
// --- REVISED AND CORRECTED VERSION ---

import { ref, watch } from 'vue';
import type { Ref } from 'vue';

/**
 * A robust, reusable composable for implementing infinite scroll.
 * @param trigger - A ref to the trigger element in the template.
 * @param fetcher - The async function to call to load more data.
 * @param nextUrl - A reactive ref to the NEXT PAGE URL string. The composable now watches this directly.
 */
export function useInfiniteScroll(
  trigger: Ref<HTMLElement | null>,
  fetcher: () => Promise<void>,
  nextUrl: Ref<string | null | undefined>
) {
  const observer = ref<IntersectionObserver | null>(null);

  watch(
    [trigger, nextUrl],
    ([triggerEl, url]) => {
      if (observer.value) {
        observer.value.disconnect();
      }

      if (triggerEl && url) {
        observer.value = new IntersectionObserver(async ([entry]) => {
          if (entry.isIntersecting) {
            observer.value?.unobserve(entry.target);
            await fetcher();
          }
        }, { rootMargin: '200px' });

        observer.value.observe(triggerEl);
      }
    },
    { immediate: true }
  );
}