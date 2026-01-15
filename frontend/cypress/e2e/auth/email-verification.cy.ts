describe('Email Verification User Flow', () => {
  beforeEach(() => {
    // Ensure a clean slate before each test
    cy.testSetup('cleanup')
  })

  it('should redirect to the "check-email" page after successful registration', () => {
    // Use dynamic values to ensure the user is always unique for each test run
    const uniqueId = Date.now()
    const username = `verifyuser_${uniqueId}`
    const email = `verify_${uniqueId}@cypresstest.com`
    const password = 'Password123!'

    // 1. Visit the registration page
    cy.visit('/register')

    // 2. Fill out the form
    cy.get('#username').type(username)
    cy.get('#email').type(email)
    cy.get('#password').type(password)
    cy.get('#password2').type(password)

    // 3. Submit the form
    cy.get('button[type="submit"]').click()

    // 4. Assert the redirection
    cy.url().should('include', '/auth/check-email')

    // 5. Assert the content of the page
    cy.contains('h2', 'Please Verify Your Email').should('be.visible')
    cy.contains('p', 'We have sent a verification link to your email address.').should('be.visible')
  })
})
