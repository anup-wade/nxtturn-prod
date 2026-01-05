<!-- C:\Users\Vinay\Project\frontend\src\components\profile\tabs\ProfileAboutTab.vue -->
<!-- --- THIS IS THE COMPLETE, REPLACEMENT CONTENT --- -->

<script setup lang="ts">
import type { UserProfile } from '@/types'

// Import the new card components we are about to create
import BioCard from '@/components/profile/cards/BioCard.vue'
import LocationCard from '@/components/profile/cards/LocationCard.vue'
import QuickLinksCard from '@/components/profile/cards/QuickLinksCard.vue'

const props = defineProps<{
  profile: UserProfile
  isOwnProfile: boolean
}>()
</script>

<template>
  <!-- 
    This component no longer has a single white background. 
    Instead, it's a transparent container for the individual cards,
    each of which will have its own styling.
  -->
  <div class="space-y-6">
    <!-- Professional Bio Card -->
    <BioCard :profile="props.profile" :is-own-profile="props.isOwnProfile" />

    <!-- Location Card -->
    <LocationCard :profile="props.profile" :is-own-profile="props.isOwnProfile" />

    <!-- Quick Links Card -->
    <QuickLinksCard :profile="props.profile" :is-own-profile="props.isOwnProfile" />
  </div>
</template>
