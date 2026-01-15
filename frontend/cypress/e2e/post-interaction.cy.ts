// C:\Users\Vinay\Project\frontend\cypress\e2e\post-interaction.cy.ts

describe('Post Interaction Flow', () => {
  const testUser = {
    username: `interaction_user_${Date.now()}`,
    password: 'password123',
  };
  
  const uniquePostText = `A post for interaction testing at ${Date.now()}`;
  const uniqueCommentText = `A new comment at ${Date.now()}`;

  before(() => {
    cy.testSetup('create_user', testUser);
  });

  beforeEach(() => {
    cy.login(testUser.username, testUser.password);
    cy.visit('/');
  });

  it('should allow a user to create, comment on, like, and delete their own post', () => {
    // --- 1. CREATE POST ---
    cy.get('[data-cy="create-post-input"]').type(uniquePostText);
    cy.get('[data-cy="create-post-submit-button"]').click();
    cy.get('[data-cy="post-container"]').contains(uniquePostText).parents('[data-cy="post-container"]').as('thePost');

    // --- 2. COMMENT ON POST ---
    cy.get('@thePost').contains('button', 'Comment').click();
    cy.get('@thePost').find('[data-cy="comment-input"]').type(uniqueCommentText);
    cy.get('@thePost').find('[data-cy="comment-submit-button"]').click();
    cy.get('[data-cy="comment-container"]').contains(uniqueCommentText).should('be.visible');

    // --- 3. LIKE POST ---
    cy.get('@thePost').find('[data-cy="like-count"]').should('contain.text', '0');
    cy.get('@thePost').find('[data-cy="like-button"]').click();
    cy.get('@thePost').find('[data-cy="like-count"]').should('contain.text', '1');

    // --- 4. DELETE POST ---

    // --- THIS IS THE NEW STEP ---
    // First, find and click the three-dots options button to open the menu.
    // Let's give it a data-cy attribute for reliability.
    cy.get('@thePost').find('[data-cy="post-options-button"]').click();
    
    // Now that the menu is open, the delete button is visible and can be clicked.
    cy.get('@thePost').find('[data-cy="delete-post-button"]').click();
    
    // Assert the post is gone from the UI
    cy.contains(uniquePostText).should('not.exist');
  });
});