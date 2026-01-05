// C:\Users\Vinay\Project\frontend\cypress\e2e\connections.cy.ts

describe('Icon-Based Connection and Follow System', () => {
  const apiBaseUrl = Cypress.env('VITE_API_BASE_URL')

  beforeEach(() => {
    cy.testSetup('create_two_users', {
      userA: { username: 'userA', password: 'password123' },
      userB: { username: 'userB', password: 'password123' },
    })
  })

  it('handles the full follow, connect, accept, and disconnect lifecycle via the new icon UI', () => {
    // === PART 1: User A follows and then sends a connection request to User B ===
    cy.login('userA', 'password123')

    cy.intercept('GET', `${apiBaseUrl}/api/profiles/userB/`).as('getProfileB')
    cy.visit('/profile/userB')
    cy.wait('@getProfileB')

    // ASSERT 1: Initial state
    cy.get('[data-cy="connect-button"]').should('be.visible').and('contain', 'Connect')
    cy.get('[data-cy="follow-toggle-button"]').should('be.visible').and('contain', 'Follow')
    cy.get('[data-cy="message-button"]').should('be.visible')

    // ACTION 1: User A clicks "Follow"
    cy.intercept('POST', `${apiBaseUrl}/api/users/userB/follow/`).as('followUser')
    cy.intercept('GET', `${apiBaseUrl}/api/profiles/userB/`).as('getProfileB_AfterFollow')
    cy.get('[data-cy="follow-toggle-button"]').click()
    cy.wait(['@followUser', '@getProfileB_AfterFollow'])

    // ASSERT 2: Follow state is updated
    cy.get('[data-cy="follow-toggle-button"]').should('be.visible').and('contain', 'Following')
    cy.get('[data-cy="connect-button"]').should('be.visible')

    // ACTION 2: User A clicks "Connect"
    cy.intercept('POST', `${apiBaseUrl}/api/connections/requests/`).as('sendRequest')
    cy.intercept('GET', `${apiBaseUrl}/api/profiles/userB/`).as('getProfileB_AfterConnect')
    cy.get('[data-cy="connect-button"]').click()
    cy.wait(['@sendRequest', '@getProfileB_AfterConnect'])

    // ASSERT 3: Button state changes to "Pending"
    cy.get('[data-cy="pending-button"]').should('be.visible')
    cy.get('[data-cy="follow-toggle-button"]').should('be.visible').and('contain', 'Following')
    cy.logout()

    // === PART 2: User B accepts the request ===
    cy.login('userB', 'password123')

    cy.intercept('GET', `${apiBaseUrl}/api/profiles/userA/`).as('getProfileA')
    cy.visit('/profile/userA')
    cy.wait('@getProfileA')

    // ASSERT 4: User B sees "Accept" icon
    cy.get('[data-cy="accept-request-button"]').should('be.visible').and('contain', 'Accept')

    // ACTION 3: User B clicks "Accept"
    cy.intercept('POST', `${apiBaseUrl}/api/users/userA/accept-request/`).as('acceptRequest')
    cy.intercept('GET', `${apiBaseUrl}/api/profiles/userA/`).as('getProfileA_AfterAccept')
    cy.get('[data-cy="accept-request-button"]').click()
    cy.wait(['@acceptRequest', '@getProfileA_AfterAccept'])

    // ASSERT 5: Final connected state is visible
    cy.get('[data-cy="connected-button"]').should('be.visible')
    cy.get('[data-cy="follow-toggle-button"]').should('not.exist')
    cy.get('[data-cy="message-button"]').should('be.visible')

    // === PART 3: User B disconnects from User A ===
    // ACTION 4: User B clicks the "Connected" icon
    cy.get('[data-cy="connected-button"]').click()

    // ASSERT 6: The "Disconnect" button is visible
    cy.get('[data-cy="disconnect-button"]').should('be.visible')

    // ACTION 5: User B clicks "Disconnect"
    cy.intercept('DELETE', `${apiBaseUrl}/api/users/userA/follow/`).as('disconnectUser')
    cy.intercept('GET', `${apiBaseUrl}/api/profiles/userA/`).as('getProfileA_AfterDisconnect')
    cy.get('[data-cy="disconnect-button"]').click()
    cy.wait(['@disconnectUser', '@getProfileA_AfterDisconnect'])

    // --- THIS IS THE FIX ---
    // Before the final check, scroll the left column to the top
    // to ensure the action icons are physically visible in the viewport.
    cy.get('[data-cy="profile-left-column"]').scrollTo('top')

    // ASSERT 7: State reverts to default
    cy.get('[data-cy="connect-button"]').should('be.visible')
    cy.get('[data-cy="follow-toggle-button"]').should('be.visible').and('contain', 'Follow')
  })
})
