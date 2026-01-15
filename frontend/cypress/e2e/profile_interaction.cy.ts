// C:\Users\Vinay\Project\frontend\cypress\e2e\profile_interaction.cy.ts
// --- THIS IS THE FINAL, COMPLETE 6-TEST SUITE ---

describe('User Profile Interaction', () => {
  context('"About" Tab Cards', () => {
    beforeEach(() => {
      const testUser = { username: 'tester', password: 'password123' }
      cy.testSetup('create_user', testUser)
      cy.login(testUser.username, testUser.password)
      cy.visit(`/profile/${testUser.username}`)
      cy.contains('button', 'About').should('have.class', 'border-blue-500')
    })

    it('allows a user to edit and save their Bio', () => {
      const newBio = `This bio was updated by Cypress at ${new Date().toLocaleTimeString()}`

      cy.get('[data-cy="bio-card"]').as('bioCard')
      cy.get('@bioCard').should('contain.text', 'No bio available.')
      cy.get('@bioCard').find('[data-cy="edit-bio-button"]').click()

      cy.get('#bio-textarea').clear().type(newBio)
      cy.intercept('PATCH', '/api/profiles/tester/').as('updateProfile')
      cy.contains('button', 'Save Changes').click()
      cy.wait('@updateProfile')

      cy.get('@bioCard').should('contain.text', newBio)
    })

    it('allows a user to edit and save their Location and Work Preferences', () => {
      const newLocation = { city: 'Cypress', state: 'Test Runner', country: 'AutomationLand' }

      cy.get('[data-cy="location-card"]').as('locationCard')
      cy.get('@locationCard').should('contain.text', 'No location information provided.')
      cy.get('@locationCard').find('[data-cy="edit-location-button"]').click()

      cy.get('#city').clear().type(newLocation.city)
      cy.get('#state').clear().type(newLocation.state)
      cy.get('#country').clear().type(newLocation.country)
      cy.get('#work-style').select('remote')
      cy.get('#relocation').check()
      cy.intercept('PATCH', '/api/profiles/tester/').as('updateProfile')
      cy.contains('button', 'Save Changes').click()
      cy.wait('@updateProfile')

      cy.get('@locationCard').should(
        'contain.text',
        `${newLocation.city}, ${newLocation.state}, ${newLocation.country}`,
      )
      cy.get('@locationCard').should('contain.text', 'Currently working Remote')
      cy.get('@locationCard').should('contain.text', 'Open to relocation')
    })

    it('allows a user to add, edit, and delete their Quick Links', () => {
      cy.get('[data-cy="quick-links-card"]').as('linksCard')
      cy.get('@linksCard').should('contain.text', 'No links provided.')
      cy.get('@linksCard').find('[data-cy="edit-quick-links-button"]').click()

      cy.contains('button', '+ Add another link').click()

      // FIX: Add { force: true } to handle DevTools overlay
      cy.get('#link-type-0').select('github', { force: true })
      cy.get('#link-url-0').type('https://github.com/testuser')

      cy.contains('button', '+ Add another link').click()

      // FIX: Add { force: true }
      cy.get('#link-type-1').select('twitter', { force: true })
      cy.get('#link-url-1').type('https://twitter.com/testuser')

      cy.get('[data-cy="remove-link-button"]').first().click()

      cy.get('#link-url-0').clear().type('https://twitter.com/updated-profile')

      cy.intercept('PATCH', '/api/profiles/tester/').as('updateProfile')
      cy.contains('button', 'Save Changes').click()
      cy.wait('@updateProfile')

      cy.get('@linksCard').should('contain.text', 'Twitter')
      cy.get('@linksCard').should('contain.text', 'https://twitter.com/updated-profile')
      cy.get('@linksCard').should('not.contain.text', 'GitHub')
    })
  })

  context('Profile Card and Picture', () => {
    it('allows a user to edit their profile summary (Display Name and Headline)', () => {
      const testUser = { username: 'summaryEditor', password: 'password123' }
      cy.testSetup('create_user', testUser)
      cy.login(testUser.username, testUser.password)
      const newDisplayName = `Test User ${Date.now()}`
      const newHeadline = 'Cypress Test Specialist'
      cy.visit(`/profile/${testUser.username}`)
      cy.get('[data-cy="profile-card-container"]')
        .find('[aria-label="Edit profile summary"]')
        .click()
      cy.contains('h3', 'Edit Profile Summary').should('be.visible')
      cy.get('input#display_name').clear().type(newDisplayName)
      cy.get('input#headline').clear().type(newHeadline)
      cy.intercept('PATCH', `/api/profiles/${testUser.username}/`).as('updateProfile')
      cy.contains('button', 'Save Changes').click()
      cy.wait('@updateProfile')
      cy.get('h1').should('contain.text', newDisplayName)
      cy.contains('p', newHeadline).should('be.visible')
    })

    it('updates the profile picture on all components after upload', () => {
      const testUser = { username: 'picUploader', password: 'password123' }
      cy.testSetup('create_user_and_post', {
        user: testUser,
        post: { content: 'Post by pic uploader' },
      })
      cy.login(testUser.username, testUser.password)
      cy.visit(`/profile/${testUser.username}`)
      cy.get('[data-cy="profile-picture-img"]').should('not.have.attr', 'src', '*/media/*')
      cy.get('[data-cy="profile-picture-container"]').click()
      cy.intercept('PATCH', `/api/profiles/${testUser.username}/`).as('uploadPicture')
      cy.get('input#picture-upload').selectFile('cypress/fixtures/test_avatar.png', { force: true })
      cy.wait('@uploadPicture')
      const newPicturePath = '/media/profile_pics/test_avatar'
      cy.get('[data-cy="profile-picture-img"]')
        .should('have.attr', 'src')
        .and('include', newPicturePath)
      cy.get('[data-cy="navbar-avatar-main"]')
        .should('have.attr', 'src')
        .and('include', newPicturePath)
      cy.get('[data-cy="post-author-avatar"]')
        .should('have.attr', 'src')
        .and('include', newPicturePath)
    })

    it('reverts profile picture on all components after removal', () => {
      const testUser = { username: 'picRemover', password: 'password123' }
      cy.testSetup('create_user_and_post', {
        user: { ...testUser, with_picture: true },
        post: { content: 'Post by pic remover' },
      })
      cy.login(testUser.username, testUser.password)
      cy.visit(`/profile/${testUser.username}`)
      cy.get('[data-cy="profile-picture-img"]')
        .should('have.attr', 'src')
        .and('include', '/media/profile_pics/')
      cy.get('[data-cy="profile-picture-container"]').click()
      cy.intercept('PATCH', `/api/profiles/${testUser.username}/`).as('removePicture')
      cy.get('[data-cy="remove-picture-button"]').click()
      cy.wait('@removePicture')
      cy.get('[data-cy="profile-picture-img"]').should('not.have.attr', 'src', '*/media/*')
      cy.get('[data-cy="navbar-avatar-main"]').should('not.have.attr', 'src', '*/media/*')
      cy.get('[data-cy="post-author-avatar"]').should('not.have.attr', 'src', '*/media/*')
    })
  })
})
