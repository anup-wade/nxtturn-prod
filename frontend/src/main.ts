// src/main.ts

import './assets/main.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'

// 1. Import the Toast library and its CSS
import Toast from 'vue-toastification'
import 'vue-toastification/dist/index.css'

import App from './App.vue'
import router from './router'

const app = createApp(App)

// Use Pinia for state management
const pinia = createPinia() // Create the Pinia instance
app.use(pinia)

// --- THIS IS THE NEW CODE BLOCK ---
// Expose the Pinia instance to the window object, but ONLY when running in Cypress.
// This allows our E2E tests to programmatically reset stores for a clean state.
if (window.Cypress) {
  window.pinia = pinia
}
// --- END OF NEW CODE BLOCK ---

// Use Vue Router for navigation
app.use(router)

// 2. Tell the app to use the Toast plugin
app.use(Toast)

// Mount the app to the DOM
app.mount('#app')