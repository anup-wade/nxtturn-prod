// C:\Users\Vinay\Project\frontend\cypress\e2e/group_interaction.cy.ts

describe('Group Creation and Interaction', () => {
  it('a user can create a new public group', () => {
    const testId = Date.now()
    const creatorUsername = `creator_${testId}`
    const groupName = `Public Group ${testId}`

    cy.testSetup('create_user', {
      email: `${creatorUsername}@cypresstest.com`,
      username: creatorUsername,
      password: 'password',
    }).then(() => {
      cy.login(creatorUsername, 'password')
      cy.visit('/groups')
      cy.get('[data-cy="create-group-button"]').click()
      cy.get('[data-cy="group-name-input"]').type(groupName)
      cy.get('[data-cy="group-description-input"]').type('A test description.')
      cy.get('input[value="public"]').check()
      cy.get('[data-cy="create-group-submit-button"]').click()
      cy.url().should('include', `/groups/public-group-${testId}`)
      cy.get('[data-cy="group-name-header"]').should('be.visible')
    })
  })

  it('a user can create a second group with the same name as an existing one', () => {
    const testId = Date.now()
    const creatorUsername = `creator_${testId}`
    const sharedGroupName = `Shared Name Group ${testId}`

    cy.testSetup('create_user', {
      email: `${creatorUsername}@cypresstest.com`,
      username: creatorUsername,
      password: 'password',
    }).then(() => {
      cy.login(creatorUsername, 'password')

      cy.visit('/groups')
      cy.get('[data-cy="create-group-button"]').click()
      cy.get('[data-cy="group-name-input"]').type(sharedGroupName)
      cy.get('[data-cy="group-description-input"]').type('First group.')
      cy.get('[data-cy="create-group-submit-button"]').click()
      cy.url().should('not.eq', `${Cypress.config().baseUrl}/groups`).as('firstGroupUrl')

      cy.visit('/groups')
      cy.get('[data-cy="create-group-button"]').click()
      cy.get('[data-cy="group-name-input"]').type(sharedGroupName)
      cy.get('[data-cy="group-description-input"]').type('Second group.')
      cy.get('[data-cy="create-group-submit-button"]').click()
      cy.get('[data-cy="group-name-header"]').should('be.visible')
      cy.url().as('secondGroupUrl')

      cy.get('@firstGroupUrl').then((firstUrl) => {
        cy.get('@secondGroupUrl').should('not.eq', firstUrl)
      })
    })
  })

  it('a user can join and then leave a public group', () => {
    const testId = Date.now()
    const creatorUsername = `creator_${testId}`
    const joinerUsername = `joiner_${testId}`
    const groupName = `Join-Leave Group ${testId}`
    const groupSlug = `join-leave-group-${testId}`

    cy.testSetup('create_user', {
      email: `${creatorUsername}@cypresstest.com`,
      username: creatorUsername,
      password: 'password',
    })
      .then(() =>
        cy.testSetup('create_user', {
          email: `${joinerUsername}@cypresstest.com`,
          username: joinerUsername,
          password: 'password',
        }),
      )
      .then(() => {
        cy.login(creatorUsername, 'password')
        cy.visit('/groups')
        cy.get('[data-cy="create-group-button"]').click()
        cy.get('[data-cy="group-name-input"]').type(groupName)
        cy.get('[data-cy="group-description-input"]').type('A group for testing join/leave.')
        cy.get('[data-cy="create-group-submit-button"]').click()
        cy.url().should('include', `/groups/${groupSlug}`).as('groupPageUrl')
        cy.logout()

        cy.login(joinerUsername, 'password')
        cy.intercept('GET', '**/api/auth/user/').as('getUser')
        cy.intercept('GET', `**/api/groups/${groupSlug}/`).as('getGroupDetails')
        cy.get('@groupPageUrl').then((url) => cy.visit(url as unknown as string))
        cy.wait(['@getUser', '@getGroupDetails'])

        cy.intercept('POST', `**/api/groups/${groupSlug}/membership/`).as('joinGroup')
        cy.get('[data-cy="group-membership-button"]').should('contain.text', 'Join Group').click()
        cy.wait('@joinGroup')

        cy.get('[data-cy="group-membership-button"]').should('not.exist')
        cy.get('[data-cy="group-options-button"]').should('be.visible').click()
        cy.get('[data-cy="leave-group-button"]').should('be.visible')
        cy.get('[data-cy="create-post-input"]').should('be.visible')

        cy.intercept('DELETE', `**/api/groups/${groupSlug}/membership/`).as('leaveGroup')
        cy.get('[data-cy="leave-group-button"]').click()
        cy.wait('@leaveGroup')

        cy.get('[data-cy="group-membership-button"]').should('contain.text', 'Join Group')
        cy.get('[data-cy="create-post-input"]').should('not.exist')
      })
  })

  it('a non-member can see posts in a public group', () => {
    const testId = Date.now()
    const creatorUsername = `creator_${testId}`
    const viewerUsername = `viewer_${testId}`
    const groupName = `Visibility Test Group ${testId}`
    const groupSlug = `visibility-test-group-${testId}`
    const postContent = `This is a public post that everyone should see. ID: ${testId}`

    cy.testSetup('create_user', {
      email: `${creatorUsername}@cypresstest.com`,
      username: creatorUsername,
      password: 'password',
    })
      .then(() =>
        cy.testSetup('create_user', {
          email: `${viewerUsername}@cypresstest.com`,
          username: viewerUsername,
          password: 'password',
        }),
      )
      .then(() => {
        cy.login(creatorUsername, 'password')
        cy.visit('/groups')
        cy.get('[data-cy="create-group-button"]').click()
        cy.get('[data-cy="group-name-input"]').type(groupName)
        cy.get('[data-cy="group-description-input"]').type('A group for testing visibility.')
        cy.get('[data-cy="create-group-submit-button"]').click()
        cy.url().should('include', `/groups/${groupSlug}`).as('groupPageUrl')

        cy.intercept('POST', '**/api/posts/').as('createPost')
        cy.get('[data-cy="create-post-input"]').type(postContent)
        cy.get('[data-cy="create-post-submit-button"]').click()
        cy.wait('@createPost')
        cy.logout()

        cy.login(viewerUsername, 'password')
        cy.intercept('GET', `**/api/groups/${groupSlug}/`).as('getGroupDetails')
        cy.get('@groupPageUrl').then((url) => cy.visit(url as unknown as string))
        cy.wait('@getGroupDetails')

        cy.contains(postContent).should('be.visible')
        cy.get('[data-cy="group-membership-button"]').should('contain.text', 'Join Group')
      })
  })

  it('the creator and a regular member can both post in the group', () => {
    const testId = Date.now()
    const creatorUsername = `creator_${testId}`
    const memberUsername = `member_${testId}`
    const groupName = `Posting Permissions Test Group ${testId}`
    const groupSlug = `posting-permissions-test-group-${testId}`
    const creatorPost = `This is the creator's original post. ID: ${testId}`
    const memberPost = `This is a post from a regular member. ID: ${testId}`

    cy.testSetup('create_user', {
      email: `${creatorUsername}@cypresstest.com`,
      username: creatorUsername,
      password: 'password',
    })
      .then(() =>
        cy.testSetup('create_user', {
          email: `${memberUsername}@cypresstest.com`,
          username: memberUsername,
          password: 'password',
        }),
      )
      .then(() => {
        cy.login(creatorUsername, 'password')
        cy.visit('/groups')
        cy.get('[data-cy="create-group-button"]').click()
        cy.get('[data-cy="group-name-input"]').type(groupName)
        cy.get('[data-cy="group-description-input"]').type('A group for testing posting.')
        cy.get('[data-cy="create-group-submit-button"]').click()
        cy.url().should('include', `/groups/${groupSlug}`).as('groupPageUrl')
        cy.get('[data-cy="group-name-header"]').should('be.visible')

        cy.intercept('POST', '**/api/posts/').as('createPost')
        cy.get('[data-cy="create-post-input"]').type(creatorPost)
        cy.get('[data-cy="create-post-submit-button"]').click()
        cy.wait('@createPost')
        cy.contains(creatorPost).should('be.visible')
        cy.logout()

        cy.login(memberUsername, 'password')
        cy.intercept('GET', `**/api/groups/${groupSlug}/`).as('getGroupDetails')
        cy.get('@groupPageUrl').then((url) => cy.visit(url as unknown as string))
        cy.wait('@getGroupDetails')

        cy.intercept('POST', `**/api/groups/${groupSlug}/membership/`).as('joinGroup')
        cy.get('[data-cy="group-membership-button"]').click()
        cy.wait('@joinGroup')

        cy.get('[data-cy="create-post-input"]').type(memberPost)
        cy.get('[data-cy="create-post-submit-button"]').click()
        cy.wait('@createPost')
        cy.contains(memberPost).should('be.visible')
        cy.contains(creatorPost).should('be.visible')
      })
  })

  it('a post made in a public group appears on the group, profile, and home feeds', () => {
    const testId = Date.now()
    const creatorUsername = `creator_${testId}`
    const followerUsername = `follower_${testId}`
    const groupName = `Feed Propagation Test Group ${testId}`
    const groupSlug = `feed-propagation-test-group-${testId}`
    const postContent = `This post should propagate to all feeds. ID: ${testId}`

    cy.testSetup('create_user', {
      email: `${creatorUsername}@cypresstest.com`,
      username: creatorUsername,
      password: 'password',
    })
      .then(() =>
        cy.testSetup('create_user', {
          email: `${followerUsername}@cypresstest.com`,
          username: followerUsername,
          password: 'password',
        }),
      )
      .then(() =>
        cy.testSetup('create_follow', { follower: followerUsername, following: creatorUsername }),
      )
      .then(() => {
        cy.login(creatorUsername, 'password')
        cy.visit('/groups')
        cy.get('[data-cy="create-group-button"]').click()
        cy.get('[data-cy="group-name-input"]').type(groupName)
        cy.get('[data-cy="group-description-input"]').type('A group for testing feed propagation.')
        cy.get('[data-cy="create-group-submit-button"]').click()
        cy.url().should('include', `/groups/${groupSlug}`)
        cy.get('[data-cy="group-name-header"]').should('be.visible')

        cy.intercept('POST', '**/api/posts/').as('createPost')
        cy.get('[data-cy="create-post-input"]').type(postContent)
        cy.get('[data-cy="create-post-submit-button"]').click()
        cy.wait('@createPost')

        cy.contains(postContent).should('be.visible')
        cy.visit(`/profile/${creatorUsername}`)
        cy.contains(postContent).should('be.visible')
        cy.logout()

        cy.login(followerUsername, 'password')
        cy.visit('/')
        cy.contains(postContent).should('be.visible')
      })
  })

  it('a sole creator is prompted to delete the group when trying to leave', () => {
    const testId = Date.now()
    const creatorUsername = `creator_${testId}`
    const groupName = `Solo Creator Delete Test ${testId}`
    const groupSlug = `solo-creator-delete-test-${testId}`

    cy.testSetup('create_user', {
      email: `${creatorUsername}@cypresstest.com`,
      username: creatorUsername,
      password: 'password',
    }).then(() => {
      cy.login(creatorUsername, 'password')
      cy.visit('/groups')
      cy.get('[data-cy="create-group-button"]').click()
      cy.get('[data-cy="group-name-input"]').type(groupName)
      cy.get('[data-cy="group-description-input"]').type(
        'A group for testing the final solo creator flow.',
      )
      cy.get('[data-cy="create-group-submit-button"]').click()
      cy.url().should('include', `/groups/${groupSlug}`)
      cy.get('[data-cy="group-name-header"]').should('be.visible')

      cy.on('window:alert', (alertText) =>
        expect(alertText).to.contain(
          'As the sole member, leaving the group will permanently delete it.',
        ),
      )
      cy.on('window:confirm', (confirmText) => {
        expect(confirmText).to.contain(
          `Are you sure you want to permanently delete the group "${groupName}"?`,
        )
        return true
      })

      cy.intercept('DELETE', `**/api/groups/${groupSlug}/`).as('deleteGroup')
      cy.get('[data-cy="group-options-button"]').click()
      cy.contains('a[role="menuitem"]', 'Leave Group').click()
      cy.wait('@deleteGroup')

      cy.url().should('eq', `${Cypress.config().baseUrl}/groups`)
      cy.contains(groupName).should('not.exist')
    })
  })

  it('a creator with members is prompted to transfer ownership when trying to leave', () => {
    const testId = Date.now()
    const creatorUsername = `creator_${testId}`
    const memberUsername = `member_${testId}`
    const groupName = `Transfer Owner Test Group ${testId}`
    const groupSlug = `transfer-owner-test-group-${testId}`

    cy.testSetup('create_user', {
      email: `${creatorUsername}@cypresstest.com`,
      username: creatorUsername,
      password: 'password',
    })
      .then(() =>
        cy.testSetup('create_user', {
          email: `${memberUsername}@cypresstest.com`,
          username: memberUsername,
          password: 'password',
        }),
      )
      .then(() => {
        cy.login(creatorUsername, 'password')
        cy.visit('/groups')
        cy.get('[data-cy="create-group-button"]').click()
        cy.get('[data-cy="group-name-input"]').type(groupName)
        cy.get('[data-cy="group-description-input"]').type(
          'A group for testing transfer ownership flow.',
        )
        cy.get('[data-cy="create-group-submit-button"]').click()
        cy.url().should('include', `/groups/${groupSlug}`).as('groupPageUrl')
        cy.logout()

        cy.login(memberUsername, 'password')
        cy.get('@groupPageUrl').then((url) => cy.visit(url as unknown as string))
        cy.get('[data-cy="group-membership-button"]').click()
        cy.logout()

        cy.login(creatorUsername, 'password')
        cy.get('@groupPageUrl').then((url) => cy.visit(url as unknown as string))
        cy.get('[data-cy="group-options-button"]').click()
        cy.on('window:alert', (alertText) =>
          expect(alertText).to.contain('you must transfer ownership before you can leave'),
        )
        cy.contains('a[role="menuitem"]', 'Leave Group').click()
        cy.contains('h2', 'Transfer Group Ownership').should('be.visible')
      })
  })

  it('a user can create a private group and another user can request to join', () => {
    const testId = Date.now()
    const creatorUsername = `creator_${testId}`
    const requesterUsername = `requester_${testId}`
    const groupName = `Private Test Group ${testId}`
    const groupSlug = `private-test-group-${testId}`
    const secretPost = `You should not be able to see this! ID: ${testId}`

    cy.testSetup('create_user', {
      email: `${creatorUsername}@cypresstest.com`,
      username: creatorUsername,
      password: 'password',
    })
      .then(() =>
        cy.testSetup('create_user', {
          email: `${requesterUsername}@cypresstest.com`,
          username: requesterUsername,
          password: 'password',
        }),
      )
      .then(() => {
        cy.login(creatorUsername, 'password')
        cy.visit('/groups')
        cy.get('[data-cy="create-group-button"]').click()
        cy.get('[data-cy="group-name-input"]').type(groupName)
        cy.get('[data-cy="group-description-input"]').type(
          'A private group for testing join requests.',
        )
        cy.get('input[value="private"]').check()
        cy.get('[data-cy="create-group-submit-button"]').click()
        cy.url().should('include', `/groups/${groupSlug}`).as('groupPageUrl')

        cy.get('[data-cy="create-post-input"]').type(secretPost)
        cy.get('[data-cy="create-post-submit-button"]').click()
        cy.contains(secretPost).should('be.visible')
        cy.logout()

        cy.login(requesterUsername, 'password')
        cy.intercept('GET', `**/api/groups/${groupSlug}/`).as('getGroupDetails')
        cy.get('@groupPageUrl').then((url) => cy.visit(url as unknown as string))
        cy.wait('@getGroupDetails')

        cy.contains(secretPost).should('not.exist')
        cy.contains('Content is hidden for non-members.').should('be.visible')
        cy.get('[data-cy="group-membership-button"]').should('contain.text', 'Request to Join')

        cy.intercept('POST', `**/api/groups/${groupSlug}/membership/`).as('requestJoin')
        cy.get('[data-cy="group-membership-button"]').click()
        cy.wait('@requestJoin')

        cy.get('[data-cy="group-membership-button"]')
          .should('contain.text', 'Request Sent')
          .and('be.disabled')
      })
  })

  it('a creator can approve a join request for a private group, granting access', () => {
    const testId = Date.now()
    const creatorUsername = `creator_${testId}`
    const joinerUsername = `joiner_${testId}`
    const groupName = `Approval Test Group ${testId}`
    const groupSlug = `approval-test-group-${testId}`
    const secretPost = `Secret content is now visible! ID: ${testId}`

    cy.testSetup('create_user', {
      email: `${creatorUsername}@cypresstest.com`,
      username: creatorUsername,
      password: 'password',
    })
      .then(() =>
        cy.testSetup('create_user', {
          email: `${joinerUsername}@cypresstest.com`,
          username: joinerUsername,
          password: 'password',
        }),
      )
      .then(() => {
        cy.login(creatorUsername, 'password')
        cy.visit('/groups')
        cy.get('[data-cy="create-group-button"]').click()
        cy.get('[data-cy="group-name-input"]').type(groupName)
        cy.get('[data-cy="group-description-input"]').type(
          'A private group for approving requests.',
        )
        cy.get('input[value="private"]').check()
        cy.get('[data-cy="create-group-submit-button"]').click()
        cy.url().should('include', `/groups/${groupSlug}`).as('groupPageUrl')
        cy.get('[data-cy="create-post-input"]').type(secretPost)
        cy.get('[data-cy="create-post-submit-button"]').click()
        cy.logout()

        cy.login(joinerUsername, 'password')
        cy.get('@groupPageUrl').then((url) => cy.visit(url as unknown as string))
        cy.get('[data-cy="group-membership-button"]').click()
        cy.logout()
      })
      .then(() => {
        cy.login(creatorUsername, 'password')
        cy.visit(`/groups/${groupSlug}/requests`)

        cy.intercept('PATCH', `**/api/groups/${groupSlug}/requests/**/`).as('manageRequest')
        cy.contains('div.p-4', joinerUsername).within(() => {
          cy.contains('button', 'Approve').click()
        })
        cy.wait('@manageRequest')
        cy.contains(joinerUsername).should('not.exist')
        cy.logout()

        cy.login(joinerUsername, 'password')
        cy.intercept('GET', `**/api/groups/${groupSlug}/`).as('getGroupDetails')
        cy.get('@groupPageUrl').then((url) => cy.visit(url as unknown as string))
        cy.wait('@getGroupDetails')

        cy.get('[data-cy="group-membership-button"]').should('not.exist')
        cy.get('[data-cy="group-options-button"]').should('be.visible')
        cy.contains(secretPost).should('be.visible')
      })
  })

  it('a creator can deny a join request for a private group', () => {
    const testId = Date.now()
    const creatorUsername = `creator_${testId}`
    const deniedUsername = `denied_${testId}`
    const groupName = `Denial Test Group ${testId}`
    const groupSlug = `denial-test-group-${testId}`

    cy.testSetup('create_user', {
      email: `${creatorUsername}@cypresstest.com`,
      username: creatorUsername,
      password: 'password',
    })
      .then(() =>
        cy.testSetup('create_user', {
          email: `${deniedUsername}@cypresstest.com`,
          username: deniedUsername,
          password: 'password',
        }),
      )
      .then(() => {
        cy.login(creatorUsername, 'password')
        cy.visit('/groups')
        cy.get('[data-cy="create-group-button"]').click()
        cy.get('[data-cy="group-name-input"]').type(groupName)
        cy.get('[data-cy="group-description-input"]').type('A private group for denying requests.')
        cy.get('input[value="private"]').check()
        cy.get('[data-cy="create-group-submit-button"]').click()
        cy.url().should('include', `/groups/${groupSlug}`).as('groupPageUrl')
        cy.logout()

        cy.login(deniedUsername, 'password')
        cy.get('@groupPageUrl').then((url) => cy.visit(url as unknown as string))
        cy.get('[data-cy="group-membership-button"]')
          .should('contain.text', 'Request to Join')
          .click()
        cy.get('[data-cy="group-membership-button"]').should('contain.text', 'Request Sent')
        cy.logout()
      })
      .then(() => {
        cy.login(creatorUsername, 'password')
        cy.visit(`/groups/${groupSlug}/requests`)

        cy.intercept('PATCH', `**/api/groups/${groupSlug}/requests/**/`).as('manageRequest')
        cy.contains('div.p-4', deniedUsername).within(() => {
          cy.contains('button', 'Deny').click()
        })
        cy.contains('a[role="menuitem"]', 'Deny Request').click()
        cy.wait('@manageRequest')
        cy.contains(deniedUsername).should('not.exist')
        cy.logout()

        cy.login(deniedUsername, 'password')
        cy.intercept('GET', `**/api/groups/${groupSlug}/`).as('getGroupDetails')
        cy.get('@groupPageUrl').then((url) => cy.visit(url as unknown as string))
        cy.wait('@getGroupDetails')

        cy.get('[data-cy="group-membership-button"]').should('contain.text', 'Request to Join')
      })
  })

  it('an approved member can post in a private group', () => {
    const testId = Date.now()
    const creatorUsername = `creator_${testId}`
    const joinerUsername = `joiner_${testId}`
    const groupName = `Private Posting Test Group ${testId}`
    const groupSlug = `private-posting-test-group-${testId}`
    const memberPost = `This is a post from an approved member. ID: ${testId}`

    cy.testSetup('create_user', {
      email: `${creatorUsername}@cypresstest.com`,
      username: creatorUsername,
      password: 'password',
    })
      .then(() =>
        cy.testSetup('create_user', {
          email: `${joinerUsername}@cypresstest.com`,
          username: joinerUsername,
          password: 'password',
        }),
      )
      .then(() => {
        cy.login(creatorUsername, 'password')
        cy.visit('/groups')
        cy.get('[data-cy="create-group-button"]').click()
        cy.get('[data-cy="group-name-input"]').type(groupName)
        cy.get('[data-cy="group-description-input"]').type('A group for testing private posting.')
        cy.get('input[value="private"]').check()
        cy.get('[data-cy="create-group-submit-button"]').click()
        cy.url().should('include', `/groups/${groupSlug}`).as('groupPageUrl')
        cy.logout()

        cy.login(joinerUsername, 'password')
        cy.get('@groupPageUrl').then((url) => cy.visit(url as unknown as string))
        cy.get('[data-cy="group-membership-button"]').click()
        cy.logout()

        cy.login(creatorUsername, 'password')
        cy.visit(`/groups/${groupSlug}/requests`)
        cy.intercept('PATCH', `**/api/groups/${groupSlug}/requests/**/`).as('manageRequest')
        cy.contains('div.p-4', joinerUsername).within(() => {
          cy.contains('button', 'Approve').click()
        })
        cy.wait('@manageRequest')
        cy.logout()
      })
      .then(() => {
        cy.login(joinerUsername, 'password')
        cy.get('@groupPageUrl').then((url) => cy.visit(url as unknown as string))

        cy.get('[data-cy="create-post-input"]').should('be.visible').type(memberPost)
        cy.intercept('POST', '**/api/posts/').as('createPost')
        cy.get('[data-cy="create-post-submit-button"]').click()
        cy.wait('@createPost')

        cy.contains(memberPost).should('be.visible')
      })
  })

  it("a post in a private group does not appear on a non-member follower's home feed", () => {
    const testId = Date.now()
    const creatorUsername = `creator_${testId}`
    const followerUsername = `follower_${testId}`
    const groupName = `Private Feed Test Group ${testId}`
    const groupSlug = `private-feed-test-group-${testId}`
    const privatePost = `This private post should NOT be on the home feed. ID: ${testId}`

    cy.testSetup('create_user', {
      email: `${creatorUsername}@cypresstest.com`,
      username: creatorUsername,
      password: 'password',
    })
      .then(() =>
        cy.testSetup('create_user', {
          email: `${followerUsername}@cypresstest.com`,
          username: followerUsername,
          password: 'password',
        }),
      )
      .then(() =>
        cy.testSetup('create_follow', { follower: followerUsername, following: creatorUsername }),
      )
      .then(() => {
        cy.login(creatorUsername, 'password')
        cy.visit('/groups')
        cy.get('[data-cy="create-group-button"]').click()
        cy.get('[data-cy="group-name-input"]').type(groupName)
        cy.get('[data-cy="group-description-input"]').type(
          'A group for testing private feed visibility.',
        )
        cy.get('input[value="private"]').check()
        cy.get('[data-cy="create-group-submit-button"]').click()
        cy.url().should('include', `/groups/${groupSlug}`)

        cy.get('[data-cy="create-post-input"]').type(privatePost)
        cy.get('[data-cy="create-post-submit-button"]').click()
        cy.logout()
      })
      .then(() => {
        cy.login(followerUsername, 'password')
        cy.visit('/')
        cy.contains(privatePost).should('not.exist')
      })
  })

  // THIS IS THE ONLY TEST THAT HAS BEEN MODIFIED
  it('a creator can deny and block a user, and later unblock them', () => {
    const testId = Date.now()
    const creatorUsername = `creator_${testId}`
    const blockedUsername = `blocked_${testId}`
    const groupName = `Block Test Group ${testId}`
    const groupSlug = `block-test-group-${testId}`

    // Part 1: Setup
    cy.testSetup('create_user', {
      email: `${creatorUsername}@cypresstest.com`,
      username: creatorUsername,
      password: 'password',
    })
      .then(() =>
        cy.testSetup('create_user', {
          email: `${blockedUsername}@cypresstest.com`,
          username: blockedUsername,
          password: 'password',
        }),
      )
      .then(() => {
        cy.login(creatorUsername, 'password')
        cy.visit('/groups')
        cy.get('[data-cy="create-group-button"]').click()
        cy.get('[data-cy="group-name-input"]').type(groupName)
        cy.get('[data-cy="group-description-input"]').type(
          'A group for testing the block/unblock flow.',
        )
        cy.get('input[value="private"]').check()
        cy.get('[data-cy="create-group-submit-button"]').click()
        cy.url().should('include', `/groups/${groupSlug}`).as('groupPageUrl')
        cy.logout()

        cy.login(blockedUsername, 'password')
        cy.get('@groupPageUrl').then((url) => cy.visit(url as unknown as string))
        cy.get('[data-cy="group-membership-button"]').click()
        cy.logout()
      })
      .then(() => {
        // Part 2: Creator denies and blocks the user
        cy.login(creatorUsername, 'password')
        cy.visit(`/groups/${groupSlug}/requests`)
        cy.on('window:confirm', () => true)
        cy.intercept('PATCH', `**/api/groups/${groupSlug}/requests/**/`).as('manageRequest')
        cy.contains('div.p-4', blockedUsername).within(() => cy.contains('button', 'Deny').click())
        cy.contains('a[role="menuitem"]', 'Deny & Block User').click()
        cy.wait('@manageRequest')
        cy.logout()
      })
      .then(() => {
        // Part 3: Blocked user verifies they cannot re-request
        cy.login(blockedUsername, 'password')
        cy.get('@groupPageUrl').then((url) => cy.visit(url as unknown as string))

        // THE FIX: Reload the page to force the application to correctly
        // hydrate its state with the "blocked" status from the API.
        cy.reload()

        // Now that the state is correct, this assertion will pass.
        cy.get('[data-cy="group-membership-button"]')
          .should('be.disabled')
          .and('contain.text', 'Blocked')
        cy.logout()
      })
      .then(() => {
        // Part 4: Creator unblocks the user
        cy.login(creatorUsername, 'password')
        cy.visit(`/groups/${groupSlug}/requests`)
        cy.contains('button', 'Blocked Users').click()
        cy.intercept('DELETE', `**/api/groups/${groupSlug}/blocks/**/`).as('unblockUser')
        cy.contains('div.p-4', blockedUsername).within(() =>
          cy.contains('button', 'Unblock').click(),
        )
        cy.wait('@unblockUser')
        cy.logout()
      })
      .then(() => {
        // Part 5: Unblocked user verifies they can request again
        cy.login(blockedUsername, 'password')
        cy.get('@groupPageUrl').then((url) => cy.visit(url as unknown as string))
        cy.get('[data-cy="group-membership-button"]')
          .should('not.be.disabled')
          .and('contain.text', 'Request to Join')
      })
  })
})
