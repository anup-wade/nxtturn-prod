<script setup lang="ts">
// Dummy data for visual representation
const people = [
  { id: 1, name: 'Priya Sharma', role: 'Software Engineer', avatar: 'https://i.pravatar.cc/150?u=p1' },
  { id: 2, name: 'Rohan Verma', role: 'Data Scientist', avatar: 'https://i.pravatar.cc/150?u=p2' },
  { id: 3, name: 'Anjali Mehta', role: 'UX Designer', avatar: 'https://i.pravatar.cc/150?u=p3' },
  { id: 4, name: 'Suresh Gupta', role: 'Product Manager', avatar: 'https://i.pravatar.cc/150?u=p4' },
  { id: 5, name: 'Kavita Singh', role: 'QA Engineer', avatar: 'https://i.pravatar.cc/150?u=p5' },
];
const institutes = [
  { id: 1, name: 'IIT Bombay', logo: 'https://placehold.co/40x40/E2E8F0/475569?text=IITB' },
  { id: 2, name: 'IIM Ahmedabad', logo: 'https://placehold.co/40x40/E2E8F0/475569?text=IIMA' },
  { id: 3, name: 'NIT Trichy', logo: 'https://placehold.co/40x40/E2E8F0/475569?text=NITT' },
];
</script>

<template>
  <div class="space-y-4">
    <div class="max-h-[calc(100vh-theme(spacing.24))] overflow-y-auto custom-scrollbar space-y-4 pr-2">
      
      <!-- People You May Know Card -->
      <div class="bg-white p-4 rounded-lg border border-gray-200 shadow-sm">
        <h3 class="font-bold text-gray-800 mb-4">People You May Know</h3>
        <ul class="space-y-4">
          <li v-for="person in people" :key="person.id" class="flex items-center gap-3">
            <img :src="person.avatar" alt="" class="h-10 w-10 rounded-full">
            <div class="flex-1">
              <p class="font-semibold text-gray-700 text-sm">{{ person.name }}</p>
              <p class="text-xs text-gray-500">{{ person.role }}</p>
            </div>
            <button class="text-sm font-medium text-blue-600 hover:text-blue-800">Connect</button>
          </li>
        </ul>
      </div>

      <!-- Featured Institutes Card -->
      <div class="bg-white p-4 rounded-lg border border-gray-200 shadow-sm">
        <h3 class="font-bold text-gray-800 mb-4">Featured Institutes</h3>
        <ul class="space-y-3">
           <li v-for="inst in institutes" :key="inst.id" class="flex items-center gap-3">
            <img :src="inst.logo" alt="" class="h-10 w-10 rounded-md">
            <p class="font-semibold text-gray-700 text-sm flex-1">{{ inst.name }}</p>
            <button class="text-sm font-medium text-blue-600 hover:text-blue-800">Follow</button>
          </li>
        </ul>
      </div>

      <!-- 
        THIS IS THE FIX: The Sponsored Card has been updated with a realistic
        placeholder image and more descriptive ad copy.
      -->
      <div class="bg-white p-4 rounded-lg border border-gray-200 shadow-sm">
        <div class="flex justify-between items-center mb-2">
          <h3 class="font-bold text-gray-800">Sponsored</h3>
          <span class="text-xs text-gray-400">Ad</span>
        </div>
        <img src="https://picsum.photos/seed/ad1/400/300" alt="Sponsored Ad" class="rounded-lg w-full">
        <div class="mt-3">
          <p class="font-semibold text-gray-700 text-sm">Master the Vue 3 Composition API</p>
          <p class="text-xs text-gray-500">The ultimate course for building scalable and maintainable Vue applications. Enroll now!</p>
        </div>
      </div>
      
    </div>
  </div>
</template>