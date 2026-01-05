describe('Profile Experience Tab', () => {
  const ownerUser = {
    username: 'expOwner',
    email: 'exp_owner@test.com',
    password: 'password123',
    first_name: 'Owner',
    last_name: 'User',
  }

  const visitorUser = {
    username: 'expVisitor',
    email: 'exp_visitor@test.com',
    password: 'password123',
    first_name: 'Visitor',
    last_name: 'User',
  }

  // Setup users once before all tests
  before(() => {
    cy.testSetup('create_user', ownerUser)
    cy.testSetup('create_user', visitorUser)
  })

  context('As the Profile Owner', () => {
    beforeEach(() => {
      // 1. Setup Intercepts
      cy.intercept('GET', `/api/profiles/${ownerUser.username}/`).as('getProfile')
      cy.intercept('POST', '/api/profile/experience/').as('createExperience')
      cy.intercept('PUT', '/api/profile/experience/*/').as('updateExperience')
      cy.intercept('DELETE', '/api/profile/experience/*/').as('deleteExperience')

      // 2. Login as Owner & Visit Profile
      cy.login(ownerUser.email, ownerUser.password)
      cy.visit(`/profile/${ownerUser.username}`)
      cy.wait('@getProfile')

      // 3. Go to Tab
      cy.contains('button', 'Experience').click()
      cy.get('[data-cy="experience-tab-content"]').should('exist')
    })

    it('Scenario 1: Form Validation (Cannot save empty data)', () => {
      cy.contains('button', 'Add Experience').click()

      // Click Save without filling anything
      cy.contains('button', 'Save').click()

      // Assert Validation Messages appear (red text)
      cy.contains('Job title is required').should('be.visible')
      cy.contains('Company name is required').should('be.visible')
      cy.contains('Start date is required').should('be.visible')

      // Close modal to clean up
      cy.contains('button', 'Cancel').click()
    })

    it('Scenario 2: Full CRUD Lifecycle (Create, Update, Delete)', () => {
      const jobData = {
        title: 'Senior Dev',
        company: `Tech Corp ${Date.now()}`,
        startYear: '2020',
      }

      // --- CREATE ---
      cy.contains('button', 'Add Experience').click()
      cy.contains('label', 'Job Title').parent().find('input').type(jobData.title)
      cy.contains('label', 'Company Name').parent().find('input').type(jobData.company)
      cy.contains('label', 'Start Date').parent().find('select').select('01')
      cy.contains('label', 'Start Date')
        .parent()
        .find('input[type="number"]')
        .type(jobData.startYear)
      cy.contains('I currently work here').click()

      cy.contains('button', 'Save').click()
      cy.wait('@createExperience').its('response.statusCode').should('eq', 201)

      // Verify UI
      cy.contains(jobData.company).parents('.bg-white').as('card')
      cy.get('@card').should('contain.text', jobData.title)
      cy.get('@card').should('contain.text', 'Present')

      // --- UPDATE ---
      cy.get('@card').find('button[title="Edit Experience"]').click()
      cy.contains('label', 'Job Title').parent().find('input').clear().type('Lead Dev')
      cy.contains('button', 'Save').click()
      cy.wait('@updateExperience').its('response.statusCode').should('eq', 200)
      cy.get('@card').should('contain.text', 'Lead Dev')

      // --- DELETE ---
      cy.get('@card').find('button[title="Delete Experience"]').click()
      cy.on('window:confirm', () => true)
      cy.wait('@deleteExperience').its('response.statusCode').should('eq', 204)
      cy.contains(jobData.company).should('not.exist')
    })

    it('Scenario 3: Sorting (Newest jobs appear first)', () => {
      // Create Old Job (2015)
      cy.contains('button', 'Add Experience').click()
      cy.contains('label', 'Job Title').parent().find('input').type('Junior Dev')
      cy.contains('label', 'Company Name').parent().find('input').type('Old Corp')
      cy.contains('label', 'Start Date').parent().find('select').select('01')
      cy.contains('label', 'Start Date').parent().find('input[type="number"]').type('2015')
      cy.contains('I currently work here').click()
      cy.contains('button', 'Save').click()
      cy.wait('@createExperience')

      // Create New Job (2023)
      cy.contains('button', 'Add Experience').click()
      cy.contains('label', 'Job Title').parent().find('input').type('CTO')
      cy.contains('label', 'Company Name').parent().find('input').type('New Corp')
      cy.contains('label', 'Start Date').parent().find('select').select('01')
      cy.contains('label', 'Start Date').parent().find('input[type="number"]').type('2023')
      cy.contains('I currently work here').click()
      cy.contains('button', 'Save').click()
      cy.wait('@createExperience')

      // Assert Order: First card should be "New Corp", Second should be "Old Corp"
      // We look for the <h3> elements which contain the Job Title
      cy.get('[data-cy="experience-tab-content"] h3').eq(0).should('contain.text', 'CTO')
      cy.get('[data-cy="experience-tab-content"] h3').eq(1).should('contain.text', 'Junior Dev')

      // Cleanup: Delete items one by one to avoid detached DOM errors
      // Delete first item
      cy.get('button[title="Delete Experience"]').first().click()
      cy.on('window:confirm', () => true)
      cy.wait('@deleteExperience')

      // Delete second item
      cy.get('button[title="Delete Experience"]').first().click()
      cy.wait('@deleteExperience')
    })
  })

  context('As a Visitor (Public View)', () => {
    beforeEach(() => {
      // 1. Login as Visitor
      cy.login(visitorUser.email, visitorUser.password)

      // 2. Visit Owner's Profile
      cy.intercept('GET', `/api/profiles/${ownerUser.username}/`).as('getOwnerProfile')
      cy.visit(`/profile/${ownerUser.username}`)
      cy.wait('@getOwnerProfile')

      // 3. Go to Tab
      cy.contains('button', 'Experience').click()
    })

    it('Scenario 4: Should NOT see Add/Edit/Delete buttons', () => {
      // 1. Should NOT see "Add Experience" button
      cy.contains('button', 'Add Experience').should('not.exist')

      // 2. Should NOT see Pencil/Trash icons on any cards (if any exist)
      cy.get('button[title="Edit Experience"]').should('not.exist')
      cy.get('button[title="Delete Experience"]').should('not.exist')
    })
  })
})
