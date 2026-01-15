// C:\Users\Vinay\Project\frontend\cypress\support\e2e.ts (Final Robust Version)

// ***********************************************************
// This example support/e2e.ts is processed and
// loaded automatically before your test files.
//
// This is a great place to put global configuration and
// behavior that modifies Cypress.
//
// You can read more here:
// https://on.cypress.io/configuration
// ***********************************************************

// Import commands.js using ES2015 syntax:
import './commands'

/**
 * Reusable function to call the backend cleanup endpoint.
 * We make `failOnStatusCode: false` so a cleanup failure doesn't stop the tests.
 */
function cleanupDatabase() {
  cy.request({
    method: 'POST',
    url: `${Cypress.env('VITE_API_BASE_URL')}/api/test/setup/`,
    body: {
      action: 'cleanup',
    },
    failOnStatusCode: false,
  }).then((response) => {
    if (response.status === 200) {
      cy.log('✅ Backend cleanup successful:', response.body)
    } else {
      // Log a warning instead of failing the test run
      cy.log('⚠️ Backend cleanup may have failed.', {
        status: response.status,
        body: response.body,
      })
    }
  })
}

/**
 * Global Before Hook
 * -----------------
 * This runs ONCE before any tests start.
 * Its primary job is to guarantee a clean slate by cleaning up data from any
 * previous runs that might have failed or been cancelled.
 */
before(() => {
  cy.log('--- E2E Test Suite Starting: Cleaning up any previous test data... ---')
  cleanupDatabase()
})

/**
 * Global After Hook
 * -----------------
 * This runs ONCE after all tests have finished.
 * Its job is to be a good citizen and clean up the data from the run that
 * just completed, leaving the database clean for the next developer.
 */
after(() => {
  cy.log('--- E2E Test Suite Finished: Performing courtesy cleanup... ---')
  cleanupDatabase()
})
