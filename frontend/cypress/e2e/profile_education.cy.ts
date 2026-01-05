// C:\Users\Vinay\Project\frontend\cypress\e2e\profile_education.cy.ts
// --- THIS IS THE FINAL, CORRECTED VERSION ---

describe('User Profile Interaction', () => {
  context('"Education" Tab CRUD', () => {
    const testUser = {
      username: 'eduTester',
      password: 'password123',
    }

    beforeEach(() => {
      cy.testSetup('create_user', testUser)
      cy.login(testUser.username, testUser.password)
      cy.visit(`/profile/${testUser.username}`)
      cy.contains('button', 'Education').click()
      cy.contains('h3', 'Education').should('be.visible')
    })

    it('allows a user to create, update, and delete an education entry', () => {
      const initialData = {
        institution: `Cypress Test University ${Date.now()}`,
        degree: 'Bachelor of Testing',
        startMonth: 'May',
        startYear: 2020,
      }

      const updatedData = {
        degree: 'Master of Automation',
        endMonth: 'April',
        endYear: 2024,
      }

      // --- CREATE ---
      cy.log('Step 1: Creating a new education entry')
      cy.contains('No education information has been added yet.').should('be.visible')
      cy.get('button[aria-label="Add new education"]').click()

      cy.get('input#institution').type(initialData.institution)
      cy.get('input#degree').type(initialData.degree)
      cy.contains('label', 'Start Date').parent().find('select').select(initialData.startMonth)
      cy.contains('label', 'Start Date')
        .parent()
        .find('input[placeholder="Year"]')
        .type(String(initialData.startYear))

      cy.intercept('POST', '/api/profile/education/').as('createEducation')
      cy.get('button[type="submit"]').contains('Save').click()
      cy.wait('@createEducation')

      cy.contains('li', initialData.institution).as('educationEntry')
      cy.get('@educationEntry').should('contain.text', initialData.degree)
      cy.get('@educationEntry').should('contain.text', `May ${initialData.startYear} - Present`)

      // --- UPDATE ---
      cy.log('Step 2: Updating the education entry')
      cy.get('@educationEntry').find('button[aria-label="Edit education"]').click()

      cy.get('input#degree').clear().type(updatedData.degree)
      cy.contains('label', 'End Date').parent().find('select').select(updatedData.endMonth)
      cy.contains('label', 'End Date')
        .parent()
        .find('input[placeholder="Year"]')
        .type(String(updatedData.endYear))

      cy.intercept('PUT', '/api/profile/education/*/').as('updateEducation')
      cy.get('button[type="submit"]').contains('Save').click()
      cy.wait('@updateEducation')

      cy.get('@educationEntry').should('contain.text', updatedData.degree)
      cy.get('@educationEntry').should('not.contain.text', initialData.degree)
      cy.get('@educationEntry').should(
        'contain.text',
        `May ${initialData.startYear} - Apr ${updatedData.endYear}`,
      )

      // --- DELETE ---
      cy.log('Step 3: Deleting the education entry')

      // --- THIS IS THE FIX ---
      // 1. Start listening for the DELETE request BEFORE you click the button.
      cy.intercept('DELETE', '/api/profile/education/*/').as('deleteEducation')

      // 2. Now, click the delete button.
      cy.get('@educationEntry').find('button[aria-label="Delete education"]').click()

      // 3. Now, wait for the request you were listening for.
      cy.wait('@deleteEducation')
      // --- END OF FIX ---

      cy.log('Asserting the deletion')
      cy.contains(initialData.institution).should('not.exist')
      cy.contains('No education information has been added yet.').should('be.visible')
    })
  })
})
