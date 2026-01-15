<script setup lang="ts">
import { shallowRef, watchEffect } from 'vue'
import type { SocialLink } from '@/types'
// ADD BriefcaseIcon to the import
import { LinkIcon, BriefcaseIcon } from '@heroicons/vue/24/solid'

const props = defineProps<{
  type: SocialLink['link_type']
}>()

const iconComponent = shallowRef<any>(LinkIcon)

watchEffect(async () => {
  if (props.type === 'linkedin') {
    const { default: comp } = await import('./brands/LinkedInIcon.vue')
    iconComponent.value = comp
  } else if (props.type === 'github') {
    const { default: comp } = await import('./brands/GitHubIcon.vue')
    iconComponent.value = comp
  } else if (props.type === 'twitter') {
    const { default: comp } = await import('./brands/TwitterIcon.vue')
    iconComponent.value = comp
  } else if (props.type === 'portfolio') {
    // --- THIS IS THE CHANGE ---
    // Use the BriefcaseIcon for portfolios
    iconComponent.value = BriefcaseIcon
  } else {
    // Fallback for any other unknown type
    iconComponent.value = LinkIcon
  }
})
</script>

<template>
  <component :is="iconComponent" class="h-6 w-6" />
</template>
