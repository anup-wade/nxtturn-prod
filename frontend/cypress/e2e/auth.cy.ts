// C:\Users\Vinay\Project\frontend\cypress\e2e\auth.cy.ts
// REFACTORED AND COMPLETE

describe('Authentication Flow', () => {
  const testUser = {
    username: `auth_test_user_${Date.now()}`,
    password: 'password123',
  }

  before(() => {
    cy.testSetup('create_user', testUser)
  })

  context('on a default (mobile/tablet) viewport', () => {
    beforeEach(() => {
      // Set viewport for this context block
      cy.viewport('ipad-2')
      cy.visit('/login')
    })

    it('successfully logs in and shows the main content, but hides sidebars', () => {
      // Use the robust custom command for login
      cy.login(testUser.username, testUser.password)

      // Assertions remain the same
      cy.get('[data-cy="create-post-input"]').should('be.visible')
      cy.contains('My Groups').should('not.be.visible')
    })
  })

  context('on a wide (desktop) viewport', () => {
    beforeEach(() => {
      cy.viewport('macbook-15')
      cy.visit('/login')
    })

    it('successfully logs in and displays both sidebars', () => {
      // Use the robust custom command for login
      cy.login(testUser.username, testUser.password)

      // Assertions remain the same
      cy.get('[data-cy="create-post-input"]').should('be.visible')
      cy.contains('My Groups').should('be.visible')
      cy.contains('People You May Know').should('be.visible')
    })
  })

  it('shows an informational message when an unverified user tries to log in', () => {
    const unverifiedUser = {
      username: `unverified_user_${Date.now()}`,
      email: `unverified_${Date.now()}@cypresstest.com`,
      password: 'password123',
    }
    cy.testSetup('create_unverified_user', unverifiedUser)

    cy.visit('/login')
    cy.get('#username').type(unverifiedUser.email)
    cy.get('#password').type(unverifiedUser.password)
    cy.get('button[type="submit"]').click()

    cy.get('[data-cy="login-message-box"]')
      .should('be.visible')
      .and(
        'contain.text',
        'Your account is not verified. A new verification link has been sent to your email.',
      )

    cy.get('[data-cy="login-message-box"]')
      .should('have.class', 'bg-blue-100')
      .and('have.class', 'border-blue-500')

    // Confirm login failed by checking that an element ONLY visible to logged-in users does not exist.
    cy.get('[data-cy="profile-menu-button"]').should('not.exist')
  })
})
