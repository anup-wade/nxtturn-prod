<!-- C:\Users\Vinay\Project\frontend\src\components\common\BaseModal.vue -->
<!-- --- THIS IS THE DEFINITIVE, CORRECTED CONTENT --- -->

<script setup lang="ts">
import { XMarkIcon } from '@heroicons/vue/24/solid'

const props = defineProps<{
  show: boolean
  title: string
}>()

const emit = defineEmits(['close'])

function closeModal() {
  emit('close')
}
</script>

<template>
  <teleport to="body">
    <!-- The backdrop transition is unchanged -->
    <transition
      enter-active-class="transition ease-out duration-200"
      enter-from-class="opacity-0"
      enter-to-class="opacity-100"
      leave-active-class="transition ease-in duration-150"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <!-- The backdrop div is now simpler -->
      <div v-if="show" class="fixed inset-0 z-40 bg-black bg-opacity-60 backdrop-blur-sm"></div>
    </transition>

    <!-- The main modal transition is unchanged -->
    <transition
      enter-active-class="transition ease-out duration-300"
      enter-from-class="opacity-0 translate-y-4 sm:translate-y-0 sm:scale-95"
      enter-to-class="opacity-100 translate-y-0 sm:scale-100"
      leave-active-class="transition ease-in duration-200"
      leave-from-class="opacity-100 translate-y-0 sm:scale-100"
      leave-to-class="opacity-0 translate-y-4 sm:translate-y-0 sm:scale-95"
    >
      <!-- @click handler is on the main container for "click outside" -->
      <div
        v-if="show"
        class="fixed inset-0 z-50 flex items-center justify-center p-4"
        @click="closeModal"
      >
        <!-- The modal panel is now a flex container with max-height -->
        <div
          class="relative flex flex-col w-full max-w-lg bg-white rounded-lg shadow-xl max-h-[90vh]"
          @click.stop
        >
          <!-- Modal Header (flex-shrink-0 keeps it from shrinking) -->
          <div class="flex items-center justify-between p-4 border-b flex-shrink-0">
            <h3 class="text-lg font-semibold text-gray-800">{{ title }}</h3>
            <button
              @click="closeModal"
              class="p-1 rounded-full text-gray-400 hover:bg-gray-100 hover:text-gray-600 transition-colors"
              aria-label="Close modal"
            >
              <XMarkIcon class="w-6 h-6" />
            </button>
          </div>

          <!-- Modal Body now has overflow-y-auto to enable scrolling -->
          <div class="p-6 overflow-y-auto">
            <slot></slot>
          </div>

          <!-- Modal Footer (flex-shrink-0 keeps it from shrinking) -->
          <div v-if="$slots.footer" class="p-4 bg-gray-50 border-t rounded-b-lg flex-shrink-0">
            <slot name="footer"></slot>
          </div>
        </div>
      </div>
    </transition>
  </teleport>
</template>
