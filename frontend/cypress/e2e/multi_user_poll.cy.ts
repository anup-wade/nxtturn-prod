// C:\Users\Vinay\Project\frontend\cypress\e2e\multi_user_poll.cy.ts

describe('Multi-User Poll Interaction & State Synchronization', () => {
  // --- Test Data Setup ---
  const userA = { username: 'userA', password: 'password123' };
  const userB = { username: 'userB', password: 'password123' };
  const userC = { username: 'userC', password: 'password123' };

  const pollData = {
    question: 'Which is the best testing approach?',
    options: ['Unit Tests', 'E2E Tests'],
  };

  before(() => {
    // --- ARRANGE ---
    // This runs ONCE before all tests. We set up our entire world state here.
    cy.testSetup('create_user', userA);
    cy.testSetup('create_user', userB);
    cy.testSetup('create_user', userC);
    cy.testSetup('create_post_with_poll', {
      username: userA.username,
      content: pollData.question,
      poll_question: pollData.question,
      poll_options: pollData.options,
    });

    // --- THE CRUCIAL FIX ---
    // User B and C must follow User A to see the post in their feeds.
    cy.testSetup('create_follow', { follower: userB.username, following: userA.username });
    cy.testSetup('create_follow', { follower: userC.username, following: userA.username });
  });

  it('accurately reflects votes, percentages, and un-votes across three user sessions', () => {
    // --- Phase 1: User A (the creator) casts the first vote ---
    cy.log('--- Phase 1: User A casts the first vote ---');
    cy.login(userA.username, userA.password);
    
    cy.intercept('GET', '/api/feed/').as('getFeedA');
    cy.visit('/');
    cy.wait('@getFeedA');

    cy.contains('[data-cy="post-container"]', pollData.question).within(() => {
      cy.contains('0 votes').should('be.visible');
      cy.contains('button', pollData.options[1]).click(); // User A votes for "E2E Tests"
      cy.contains('1 vote').should('be.visible');
      cy.contains(pollData.options[1]).parent().contains('100%').should('be.visible');
      cy.contains(pollData.options[0]).parent().contains('0%').should('be.visible');
    });

    // --- Phase 2: User B votes for the same option ---
    cy.log('--- Phase 2: User B votes for the same option ---');
    cy.login(userB.username, userB.password);

    cy.intercept('GET', '/api/feed/').as('getFeedB');
    cy.visit('/');
    cy.wait('@getFeedB');

    cy.contains('[data-cy="post-container"]', pollData.question).within(() => {
      cy.contains('1 vote').should('be.visible');
      cy.contains(pollData.options[1]).parent().contains('100%').should('be.visible');
      cy.contains('button', pollData.options[1]).click(); // User B also votes for "E2E Tests"
      cy.contains('2 votes').should('be.visible');
      cy.contains(pollData.options[1]).parent().contains('100%').should('be.visible');
    });

    // --- Phase 3: User C votes for the other option, creating a split ---
    cy.log('--- Phase 3: User C votes for the other option ---');
    cy.login(userC.username, userC.password);

    cy.intercept('GET', '/api/feed/').as('getFeedC');
    cy.visit('/');
    cy.wait('@getFeedC');

    cy.contains('[data-cy="post-container"]', pollData.question).within(() => {
      cy.contains('2 votes').should('be.visible');
      cy.contains('button', pollData.options[0]).click(); // User C votes for "Unit Tests"
      cy.contains('3 votes').should('be.visible');
      cy.contains(pollData.options[1]).parent().contains('67%').should('be.visible'); // E2E Tests: 2 votes
      cy.contains(pollData.options[0]).parent().contains('33%').should('be.visible'); // Unit Tests: 1 vote
    });

    // --- Phase 4: User B un-casts their vote, changing the result ---
    cy.log('--- Phase 4: User B un-casts their vote ---');
    cy.login(userB.username, userB.password);

    cy.intercept('GET', '/api/feed/').as('getFeedD');
    cy.visit('/');
    cy.wait('@getFeedD');

    cy.contains('[data-cy="post-container"]', pollData.question).within(() => {
      cy.contains('3 votes').should('be.visible');
      cy.contains('button', pollData.options[1]).click(); // User B clicks "E2E Tests" again to un-vote
      cy.contains('2 votes').should('be.visible');
      cy.contains(pollData.options[1]).parent().contains('50%').should('be.visible'); // E2E Tests: 1 vote
      cy.contains(pollData.options[0]).parent().contains('50%').should('be.visible'); // Unit Tests: 1 vote
    });

    // --- Phase 5: Final verification from User A's perspective ---
    cy.log("--- Phase 5: Final verification from User A's perspective ---");
    cy.login(userA.username, userA.password);

    cy.intercept('GET', '/api/feed/').as('getFeedE');
    cy.visit('/');
    cy.wait('@getFeedE');
    
    cy.contains('[data-cy="post-container"]', pollData.question).within(() => {
      cy.contains('2 votes').should('be.visible');
      cy.contains(pollData.options[1]).parent().contains('50%').should('be.visible');
      cy.contains(pollData.options[0]).parent().contains('50%').should('be.visible');
    });
  });
});