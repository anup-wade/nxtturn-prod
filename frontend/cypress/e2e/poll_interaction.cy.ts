// C:\Users\Vinay\Project\frontend\cypress\e2e\poll_interaction.cy.ts

describe('Single-User Poll Interaction Lifecycle', () => {
  const testUser = {
    username: 'pollTester',
    password: 'password123',
  };

  const pollData = {
    question: 'Is Cypress powerful?',
    options: ['Yes', 'No'],
  };

  beforeEach(() => {
    // --- ARRANGE ---
    // Before each test, we ensure a clean slate by using our custom backend command.
    cy.testSetup('create_user', testUser);
    cy.testSetup('create_post_with_poll', {
      username: testUser.username,
      poll_question: pollData.question,
      poll_options: pollData.options,
    });

    // Log in as our test user for the upcoming actions
    cy.login(testUser.username, testUser.password);

    // Visit the main feed where the poll will be visible
    cy.visit('/');
  });

  it('allows a user to vote, change their vote, and un-cast their vote, with instant UI updates', () => {
    // --- ACT & ASSERT ---

    // Find the specific post containing our poll by its unique question text.
    // We scope all future actions within this poll to make the test stable.
    cy.contains('[data-cy="post-container"]', pollData.question).within(() => {
      
      // --- Step 1: Verify Initial State ---
      cy.log('Verifying initial state (0 votes)');
      cy.contains('0 votes').should('be.visible');

      // --- Step 2: Cast the First Vote ---
      cy.log('Casting the first vote for "Yes"');
      cy.contains('button', pollData.options[0]).click();

      // Assert UI updates instantly
      cy.contains('1 vote').should('be.visible');
      cy.contains('100%').should('be.visible');
      // Verify the 'No' option correctly shows 0%
      cy.contains(pollData.options[1]).parent().contains('0%').should('be.visible');

      // --- Step 3: Change the Vote ---
      cy.log('Changing vote to "No"');
      cy.contains('button', pollData.options[1]).click();
      
      // Assert UI updates instantly after changing vote
      cy.contains('1 vote').should('be.visible'); // Count should NOT increase
      cy.contains(pollData.options[0]).parent().contains('0%').should('be.visible');
      cy.contains(pollData.options[1]).parent().contains('100%').should('be.visible');

      // --- Step 4: Un-cast the Vote ---
      cy.log('Un-casting vote by clicking "No" again');
      cy.contains('button', pollData.options[1]).click();

      // Assert UI reverts to its original state
      cy.contains('0 votes').should('be.visible');
      // The percentages should no longer be in the DOM
      cy.contains('%').should('not.exist');
    });
  });
});