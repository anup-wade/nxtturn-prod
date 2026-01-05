// C:\Users\Vinay\Project\frontend\cypress\e2e\smoke.cy.ts

describe('Smoke Test', () => {
  it('App loads the login page correctly', () => {
    // Visit the base URL (http://192.168.31.35:5173 from our config)
    cy.visit('/');

    // Assert that the page contains an <h2> element with the text "Log in to your account"
    // IMPORTANT: If your login page uses different text, change this line to match!
    cy.contains('Sign in to your account');
  });
});

// A simple comment to trigger a change