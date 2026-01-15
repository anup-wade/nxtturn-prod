// C:\Users\Vinay\Project\frontend\cypress\e2e\state.cy.ts
// REFACTORED AND COMPLETE

describe('Application State Management', () => {
  it('should purge all store data on logout to prevent stale state', () => {
    const userWithPosts = { username: `user_with_posts_${Date.now()}`, password: 'password123' }
    const userWithEmptyFeed = { username: `empty_feed_user_${Date.now()}`, password: 'password123' }
    cy.testSetup('create_user', userWithPosts)
    cy.testSetup('create_user', userWithEmptyFeed)
    cy.testSetup('create_post', {
      username: userWithPosts.username,
      content: 'This post exists to test the cache.',
    })

    // Part 1: Login as the user who HAS posts
    cy.login(userWithPosts.username, userWithPosts.password)
    cy.get('[data-cy="post-container"]').should('exist')

    // Part 2: Logout programmatically
    cy.logout()
    cy.visit('/') // Visit a page to confirm logout
    cy.url().should('include', '/login')

    // Part 3: Login as the user with an EMPTY feed and verify state was cleared
    cy.login(userWithEmptyFeed.username, userWithEmptyFeed.password)

    // The final, definitive assertion: the first user's post should NOT be present
    cy.get('[data-cy="post-container"]').should('not.exist')
    cy.get('[data-cy="empty-feed-message"]').should('be.visible')
  })

  it('should reflect a new post on the main feed and profile page instantly', () => {
    const testUser = { username: `reactive_${Date.now()}`, password: 'password123' }
    cy.testSetup('create_user', testUser)
    cy.login(testUser.username, testUser.password)
    cy.visit('/')

    const postText = `My reactive post at ${Date.now()}`
    cy.intercept('GET', '**/api/feed/').as('getFeed')
    cy.wait('@getFeed')
    cy.get('[data-cy="create-post-input"]').type(postText)
    cy.get('[data-cy="create-post-submit-button"]').click()
    cy.get('[data-cy="post-container"]').contains(postText).should('be.visible')
    cy.get('[data-cy="profile-link"]').click()
    cy.get('[data-cy="post-container"]').contains(postText).should('be.visible')
  })

  it('should display only the correct posts on the main feed', () => {
    const mainUser = { username: `main_${Date.now()}`, password: 'password123' }
    const followedUser = { username: `followed_${Date.now()}`, password: 'password123' }
    const otherUser = { username: `other_${Date.now()}`, password: 'password123' }
    cy.testSetup('create_user', mainUser)
    cy.testSetup('create_user', followedUser)
    cy.testSetup('create_user', otherUser)

    const ownPostText = `My own post!`
    const followedPostText = `Post from followed user.`
    const otherPostText = `Post from other user that should be hidden.`

    cy.testSetup('create_post', { username: mainUser.username, content: ownPostText })
    cy.testSetup('create_post', { username: followedUser.username, content: followedPostText })
    cy.testSetup('create_post', { username: otherUser.username, content: otherPostText })

    cy.login(mainUser.username, mainUser.password)
    cy.testSetup('create_follow', {
      follower: mainUser.username,
      following: followedUser.username,
    })

    cy.visit('/')
    cy.intercept('GET', '**/api/feed/').as('getFeed')
    cy.wait('@getFeed')

    cy.get('[data-cy="post-container"]').contains(ownPostText).should('be.visible')
    cy.get('[data-cy="post-container"]').contains(followedPostText).should('be.visible')
    cy.contains(otherPostText).should('not.exist')
  })
})
