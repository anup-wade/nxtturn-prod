// C:\Users\Vinay\Project\frontend\cypress\support\commands.ts

/// <reference types="cypress" />

/**
 * Custom command to programmatically log in a user.
 * This is the most robust way to handle authentication in E2E tests.
 * It bypasses the UI for speed and reliability.
 */
Cypress.Commands.add('login', (username, password) => {
  cy.log(`Logging in as ${username}`)
  const apiBaseUrl = Cypress.env('VITE_API_BASE_URL')

  // Intercept the API call that fetches the user's profile data after login.
  // We will wait for this call to complete to ensure the app's state is fully initialized.
  cy.intercept('GET', `${apiBaseUrl}/api/auth/user/`).as('getUserProfile')

  // Step 1: Programmatically get the auth token from the backend.
  cy.request({
    method: 'POST',
    url: `${apiBaseUrl}/api/auth/login/`,
    body: { username, password },
  }).then(({ body }) => {
    // Step 2: Set the token in localStorage, which the frontend will use.
    window.localStorage.setItem('authToken', body.key)
  })

  // Step 3: Visit the homepage. This action will trigger the frontend
  // to read the token and make the '/api/auth/user/' call we intercepted.
  cy.visit('/')

  // Step 4: CRITICAL SYNCHRONIZATION POINT.
  // Wait for the '@getUserProfile' API call to finish successfully.
  // This guarantees that the Pinia authStore is fully populated before
  // the test continues, preventing all race condition errors.
  cy.wait('@getUserProfile').its('response.statusCode').should('eq', 200)

  cy.log(`Login successful and user profile data is fully loaded for ${username}.`)
})

/**
 * Custom command for all backend test setup and seeding operations.
 */
Cypress.Commands.add('testSetup', (action, data) => {
  const apiBaseUrl = Cypress.env('VITE_API_BASE_URL')
  cy.request({
    method: 'POST',
    url: `${apiBaseUrl}/api/test/setup/`,
    body: { action, data },
  })
})

/**
 * Custom command to clear the auth token from localStorage.
 */
Cypress.Commands.add('logout', () => {
  window.localStorage.removeItem('authToken')
})

// --- TypeScript Type Definitions for Custom Commands ---
declare global {
  namespace Cypress {
    interface Chainable {
      /**
       * Logs a user in programmatically and waits for the app to be ready.
       * @param username The username for login.
       * @param password The password for login.
       */
      login(username: string, password: string): Chainable<void>

      /**
       * Sends a setup command to the backend's test utility endpoint.
       * @param action The name of the action to perform (e.g., 'create_user').
       * @param data The payload for the action.
       */
      testSetup(action: string, data?: any): Chainable<Cypress.Response<any>>

      /**
       * Clears the authentication token from local storage.
       */
      logout(): Chainable<void>
    }
  }
}

export {}
