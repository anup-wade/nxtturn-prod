// C:\Users\Vinay\Project\frontend\cypress\e2e\navigation_ux.cy.ts

describe('Navigation UX Enhancements', () => {
  let scrollTester: any
  let postAuthor: any

  beforeEach(() => {
    cy.testSetup('cleanup')

    cy.testSetup('create_user_with_posts', {
      username: 'post_author',
      num_posts: 15,
    }).then((response) => {
      postAuthor = response.body
    })

    cy.testSetup('create_user', { username_prefix: 'scroll_tester' }).then((response) => {
      scrollTester = response.body

      cy.testSetup('create_follow', {
        follower: scrollTester.username,
        following: postAuthor.username,
      }).then(() => {
        cy.login(scrollTester.username, 'Airtel@123')
      })
    })
  })

  // Helper function for pages with a SINGLE, window-based scrollbar
  const testWindowScrollToTop = (url: string, selectorToWaitFor: string, linkSelector: string) => {
    cy.visit(url)
    cy.get(selectorToWaitFor, { timeout: 10000 }).should('be.visible')
    cy.scrollTo('bottom', { duration: 500 })
    cy.window().its('scrollY').should('not.eq', 0)
    cy.get(linkSelector).click()
    cy.window().its('scrollY').should('eq', 0)
  }

  context('Desktop Viewport (1280x720)', () => {
    beforeEach(() => {
      cy.viewport(1280, 720)
    })

    it('should scroll to the top when clicking the logo link while on the home feed', () => {
      testWindowScrollToTop('/', '[data-cy="post-container"]', '[data-cy="navbar-logo-link"]')
    })

    it('should scroll to the top when clicking the sidebar home link while on the home feed', () => {
      testWindowScrollToTop('/', '[data-cy="post-container"]', '[data-cy="sidebar-home-link"]')
    })

    // --- THIS IS THE FIXED TEST ---
    it('should scroll to the top when clicking the profile link while on the profile page', () => {
      // ARRANGE: Create extra posts to ensure the right column is scrollable
      cy.testSetup('create_user_with_posts', { username: scrollTester.username, num_posts: 15 })
      cy.visit(`/profile/${scrollTester.username}`)
      cy.get('[data-cy="profile-picture-container"]', { timeout: 10000 }).should('be.visible')

      // ACT:
      // 1. Find the right column (the last of the two main columns) and scroll it down.
      cy.get('.lg\\:col-span-6').last().scrollTo('bottom', { duration: 500 })

      // 2. Assert that it has actually scrolled.
      cy.get('.lg\\:col-span-6').last().its('0.scrollTop').should('not.eq', 0)

      // 3. Click the profile link in the top navigation bar.
      cy.get('[data-cy="profile-link"]').click()

      // ASSERT:
      // 4. Assert that BOTH columns have scrolled back to the top.
      cy.get('.lg\\:col-span-6').first().its('0.scrollTop').should('eq', 0) // Left column
      cy.get('.lg\\:col-span-6').last().its('0.scrollTop').should('eq', 0) // Right column
    })
    // --- END OF FIXED TEST ---

    it('should scroll to the top when clicking the my groups link while on the groups page', () => {
      for (let i = 0; i < 10; i++) {
        cy.testSetup('create_group', {
          creator_username: scrollTester.username,
          name: `Scroll Test Group ${i}`,
        })
      }
      // Note: Re-using the window scroll helper as the groups page is a standard scrolling page.
      testWindowScrollToTop(
        '/groups',
        'h1:contains("Discover Groups")',
        '[data-cy="sidebar-groups-link"]',
      )
    })
  })

  context('Default Viewport', () => {
    it('should scroll to the top when clicking the notifications link while on the notifications page', () => {
      cy.visit('/notifications')
      cy.get('h1').contains('Your Notifications').should('be.visible')
      cy.scrollTo('bottom', { ensureScrollable: false })
      cy.get('[data-cy="navbar-notifications-link"]').click()
      cy.window().its('scrollY').should('eq', 0)
    })

    it('should scroll to the top when clicking the saved posts link while on the saved posts page', () => {
      cy.visit('/saved-posts')
      cy.get('h1').contains('Saved Posts').should('be.visible')
      cy.scrollTo('bottom', { ensureScrollable: false })
      cy.get('[data-cy="sidebar-saved-posts-link"]').click({ force: true })
      cy.window().its('scrollY').should('eq', 0)
    })
  })
})
