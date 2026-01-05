// C:\Users\Vinay\Project\frontend\cypress\e2e\multi-tab.cy.ts
// REFACTORED AND COMPLETE

describe('Multi-Tab Synchronization', () => {
  it('should log out the user and redirect if the auth token is removed', () => {
    const testUser = {
      username: `multitab_user_${Date.now()}`,
      password: 'password123',
    }
    cy.testSetup('create_user', testUser)

    cy.login(testUser.username, testUser.password)
    cy.visit('/')

    // Assert we are logged in by checking for an element that is always visible when authenticated.
    cy.get('[data-cy="profile-menu-button"]').should('be.visible')
    cy.url().should('not.include', '/login')

    cy.log('Simulating logout from another tab by clearing the token.')
    cy.clearLocalStorage('authToken')

    cy.reload()

    cy.url().should('include', '/login')
    cy.contains('Sign in to your account').should('be.visible')
  })
})
