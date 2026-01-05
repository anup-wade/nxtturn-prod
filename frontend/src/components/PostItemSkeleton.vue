<!-- C:\Users\Vinay\Project\frontend\src\components\PostItemSkeleton.vue -->
<template>
  <article class="bg-white rounded-2xl shadow-sm border border-gray-100 p-4 animate-pulse">
    <!-- Skeleton Header -->
    <div class="flex items-start justify-between">
      <!-- Left side: Avatar and text lines -->
      <div class="flex items-start">
        <div class="w-11 h-11 rounded-full bg-gray-200 mr-4"></div>
        <div>
          <div class="h-4 bg-gray-200 rounded w-24 mb-2"></div>
          <div class="h-3 bg-gray-200 rounded w-16"></div>
        </div>
      </div>
      <!-- Right side: Options menu button -->
      <div class="h-6 w-6 rounded-full bg-gray-200"></div>
    </div>

    <!-- Skeleton Body -->
    <div class="mt-4 space-y-3">
      <div class="h-4 bg-gray-200 rounded"></div>
      <div class="h-4 bg-gray-200 rounded w-5/6"></div>
      <div class="h-4 bg-gray-200 rounded w-1/2"></div>
    </div>
  </article>
</template>