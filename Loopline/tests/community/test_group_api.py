# C:\Users\Vinay\Project\Loopline\tests\community\test_group_api.py
# --- FULLY CORRECTED VERSION ---
import pytest
from rest_framework import status
from community.models import Group, GroupJoinRequest, GroupBlock, Notification

from tests.conftest import user_factory, api_client_factory, api_client, join_request_scenario

pytestmark = pytest.mark.django_db

def test_unauthenticated_user_cannot_create_group(api_client):
    response = api_client.post('/api/groups/', {'name': 'Fail Group'})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_authenticated_user_can_create_group(user_factory, api_client_factory):
    user = user_factory()
    client = api_client_factory(user=user)
    response = client.post('/api/groups/', {'name': 'Test Group', 'privacy_level': 'public'})
    assert response.status_code == status.HTTP_201_CREATED
    assert Group.objects.filter(name='Test Group', creator=user).exists()

def test_user_can_list_groups(user_factory, api_client_factory):
    user = user_factory()
    Group.objects.create(creator=user, name="Group 1")
    client = api_client_factory(user=user)
    response = client.get('/api/groups/')
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()['results']) == 1

def test_user_can_search_groups_by_name(user_factory, api_client_factory):
    user = user_factory()
    Group.objects.create(creator=user, name="Python Devs")
    Group.objects.create(creator=user, name="Django Fans")
    client = api_client_factory(user=user)
    response = client.get('/api/groups/?search=Python')
    assert len(response.json()['results']) == 1

def test_user_can_retrieve_group_details(user_factory, api_client_factory):
    user = user_factory()
    group = Group.objects.create(creator=user, name="Retrieve Me")
    client = api_client_factory(user=user)
    response = client.get(f'/api/groups/{group.slug}/')
    assert response.status_code == status.HTTP_200_OK
    assert response.json()['name'] == "Retrieve Me"

def test_non_member_sees_limited_private_group_details(user_factory, api_client_factory):
    creator, member, non_member = user_factory(), user_factory(), user_factory()
    group = Group.objects.create(creator=creator, name="Secret", privacy_level='private')
    group.members.add(creator, member)
    client = api_client_factory(user=non_member)
    response = client.get(f'/api/groups/{group.slug}/')
    assert response.status_code == status.HTTP_200_OK
    assert response.json()['members'] == []

def test_member_can_see_full_private_group_details(user_factory, api_client_factory):
    creator, member = user_factory(), user_factory()
    group = Group.objects.create(creator=creator, name="Secret", privacy_level='private')
    group.members.add(creator, member)
    client = api_client_factory(user=member)
    response = client.get(f'/api/groups/{group.slug}/')
    assert len(response.json()['members']) == 2

def test_creator_can_update_group(user_factory, api_client_factory):
    creator = user_factory()
    group = Group.objects.create(creator=creator, name="Old Name")
    client = api_client_factory(user=creator)
    response = client.patch(f'/api/groups/{group.slug}/', {'name': 'New Name'})
    assert response.status_code == status.HTTP_200_OK
    group.refresh_from_db()
    assert group.name == "New Name"

def test_non_creator_cannot_update_group(user_factory, api_client_factory):
    creator, other_user = user_factory(), user_factory()
    group = Group.objects.create(creator=creator, name="Old Name")
    client = api_client_factory(user=other_user)
    response = client.patch(f'/api/groups/{group.slug}/', {'name': 'New Name'})
    assert response.status_code == status.HTTP_403_FORBIDDEN

def test_creator_can_delete_group(user_factory, api_client_factory):
    creator = user_factory()
    group = Group.objects.create(creator=creator, name="Delete Me")
    client = api_client_factory(user=creator)
    response = client.delete(f'/api/groups/{group.slug}/')
    assert response.status_code == status.HTTP_204_NO_CONTENT

def test_non_creator_cannot_delete_group(user_factory, api_client_factory):
    creator, other_user = user_factory(), user_factory()
    group = Group.objects.create(creator=creator, name="Delete Me")
    client = api_client_factory(user=other_user)
    response = client.delete(f'/api/groups/{group.slug}/')
    assert response.status_code == status.HTTP_403_FORBIDDEN

def test_user_must_request_to_join_private_group(user_factory, api_client_factory):
    creator, requester = user_factory(), user_factory()
    group = Group.objects.create(creator=creator, name="Private Group", privacy_level='private')
    client = api_client_factory(user=requester)
    response = client.post(f"/api/groups/{group.slug}/membership/")
    assert response.status_code == status.HTTP_201_CREATED
    assert not group.members.filter(id=requester.id).exists()
    assert GroupJoinRequest.objects.filter(group=group, user=requester).exists()

def test_group_creator_can_list_pending_requests(join_request_scenario, api_client_factory):
    scenario = join_request_scenario
    client = api_client_factory(user=scenario['creator'])
    response = client.get(f"/api/groups/{scenario['group'].slug}/requests/")
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()['results']) == 1

def test_non_creator_cannot_list_pending_requests(join_request_scenario, api_client_factory, user_factory):
    random_user = user_factory()
    client = api_client_factory(user=random_user)
    response = client.get(f"/api/groups/{join_request_scenario['group'].slug}/requests/")
    assert response.status_code == status.HTTP_403_FORBIDDEN

def test_group_creator_can_approve_join_request(join_request_scenario, api_client_factory):
    scenario = join_request_scenario
    client = api_client_factory(user=scenario['creator'])
    response = client.patch(f"/api/groups/{scenario['group'].slug}/requests/{scenario['request'].id}/", {"action": "approve"})
    assert response.status_code == status.HTTP_200_OK
    assert scenario['group'].members.filter(id=scenario['requester'].id).exists()

def test_group_creator_can_deny_join_request(join_request_scenario, api_client_factory):
    scenario = join_request_scenario
    client = api_client_factory(user=scenario['creator'])
    response = client.patch(f"/api/groups/{scenario['group'].slug}/requests/{scenario['request'].id}/", {"action": "deny"})
    assert response.status_code == status.HTTP_200_OK
    assert not GroupJoinRequest.objects.filter(id=scenario['request'].id).exists()

def test_creator_can_transfer_ownership(user_factory, api_client_factory):
    creator, new_owner = user_factory(), user_factory()
    group = Group.objects.create(creator=creator)
    group.members.add(creator, new_owner)
    client = api_client_factory(user=creator)
    response = client.post(f'/api/groups/{group.slug}/transfer-ownership/', {'new_owner_id': new_owner.id})
    assert response.status_code == status.HTTP_200_OK
    group.refresh_from_db()
    assert group.creator == new_owner

def test_non_creator_cannot_transfer_ownership(user_factory, api_client_factory):
    creator, member, new_owner = user_factory(), user_factory(), user_factory()
    group = Group.objects.create(creator=creator)
    group.members.add(creator, member, new_owner)
    client = api_client_factory(user=member)
    response = client.post(f'/api/groups/{group.slug}/transfer-ownership/', {'new_owner_id': new_owner.id})
    assert response.status_code == status.HTTP_403_FORBIDDEN

def test_creator_cannot_transfer_to_non_member(user_factory, api_client_factory):
    creator, non_member = user_factory(), user_factory()
    group = Group.objects.create(creator=creator)
    client = api_client_factory(user=creator)
    response = client.post(f'/api/groups/{group.slug}/transfer-ownership/', {'new_owner_id': non_member.id})
    assert response.status_code == status.HTTP_400_BAD_REQUEST

def test_creator_cannot_transfer_ownership_to_self(user_factory, api_client_factory):
    creator = user_factory()
    group = Group.objects.create(creator=creator)
    client = api_client_factory(user=creator)
    response = client.post(f'/api/groups/{group.slug}/transfer-ownership/', {'new_owner_id': creator.id})
    assert response.status_code == status.HTTP_400_BAD_REQUEST

def test_blocked_user_cannot_request_to_join_private_group(user_factory, api_client_factory):
    creator, blocked_user = user_factory(), user_factory()
    group = Group.objects.create(creator=creator, privacy_level='private')
    GroupBlock.objects.create(group=group, user=blocked_user, blocked_by=creator)
    client = api_client_factory(user=blocked_user)
    response = client.post(f"/api/groups/{group.slug}/membership/")
    assert response.status_code == status.HTTP_403_FORBIDDEN

def test_creator_can_deny_and_block_request(join_request_scenario, api_client_factory):
    scenario = join_request_scenario
    client = api_client_factory(user=scenario['creator'])
    response = client.patch(f"/api/groups/{scenario['group'].slug}/requests/{scenario['request'].id}/", {"action": "deny_and_block"})
    assert response.status_code == status.HTTP_200_OK
    assert GroupBlock.objects.filter(group=scenario['group'], user=scenario['requester']).exists()

def test_former_member_can_re_request_to_join_private_group(user_factory, api_client_factory):
    creator, former_member = user_factory(), user_factory()
    group = Group.objects.create(creator=creator, privacy_level='private')
    group.members.add(creator, former_member)
    group.members.remove(former_member)
    client = api_client_factory(user=former_member)
    response = client.post(f'/api/groups/{group.slug}/membership/')
    assert response.status_code == status.HTTP_201_CREATED
    assert GroupJoinRequest.objects.filter(group=group, user=former_member, status='pending').exists()

def test_creator_can_list_blocked_users(user_factory, api_client_factory):
    creator, blocked = user_factory(), user_factory()
    group = Group.objects.create(creator=creator)
    GroupBlock.objects.create(group=group, user=blocked, blocked_by=creator)
    client = api_client_factory(user=creator)
    response = client.get(f'/api/groups/{group.slug}/blocks/')
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()['results']) == 1

def test_non_creator_cannot_list_blocked_users(user_factory, api_client_factory):
    creator, other_user = user_factory(), user_factory()
    group = Group.objects.create(creator=creator)
    client = api_client_factory(user=other_user)
    response = client.get(f'/api/groups/{group.slug}/blocks/')
    assert response.status_code == status.HTTP_403_FORBIDDEN

def test_creator_can_unblock_user(user_factory, api_client_factory):
    creator, blocked = user_factory(), user_factory()
    group = Group.objects.create(creator=creator)
    GroupBlock.objects.create(group=group, user=blocked, blocked_by=creator)
    client = api_client_factory(user=creator)
    response = client.delete(f'/api/groups/{group.slug}/blocks/{blocked.id}/')
    assert response.status_code == status.HTTP_204_NO_CONTENT

def test_non_creator_cannot_unblock_user(user_factory, api_client_factory):
    creator, blocked, other_user = user_factory(), user_factory(), user_factory()
    group = Group.objects.create(creator=creator)
    GroupBlock.objects.create(group=group, user=blocked, blocked_by=creator)
    client = api_client_factory(user=other_user)
    response = client.delete(f'/api/groups/{group.slug}/blocks/{blocked.id}/')
    assert response.status_code == status.HTTP_403_FORBIDDEN

def test_unblocking_non_blocked_user_returns_404(user_factory, api_client_factory):
    creator, not_blocked = user_factory(), user_factory()
    group = Group.objects.create(creator=creator)
    client = api_client_factory(user=creator)
    response = client.delete(f'/api/groups/{group.slug}/blocks/{not_blocked.id}/')
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_join_request_to_private_group_creates_notification_for_owner(user_factory, api_client_factory): # <-- MISSING TEST
    creator, requester = user_factory(), user_factory()
    group = Group.objects.create(creator=creator, privacy_level='private')
    client = api_client_factory(user=requester)
    Notification.objects.all().delete()
    client.post(f"/api/groups/{group.slug}/membership/")
    assert Notification.objects.filter(recipient=creator, notification_type=Notification.GROUP_JOIN_REQUEST).count() == 1

def test_approving_join_request_creates_notification_for_requester(join_request_scenario, api_client_factory): # <-- MISSING TEST
    scenario = join_request_scenario
    client = api_client_factory(user=scenario['creator'])
    Notification.objects.all().delete()
    client.patch(f"/api/groups/{scenario['group'].slug}/requests/{scenario['request'].id}/", {"action": "approve"})
    assert Notification.objects.filter(recipient=scenario['requester'], notification_type=Notification.GROUP_JOIN_APPROVED).count() == 1


# --- Test Set 1: VERIFY THE BUG FIX ---

def test_blocked_user_sees_blocked_status_on_group_detail(user_factory, api_client_factory):
    """
    This is the regression test for the critical bug we just fixed.
    It ensures the API correctly reports 'blocked' status, which would have
    failed before the GroupSerializer was corrected.
    """
    creator, blocked_user = user_factory(), user_factory()
    group = Group.objects.create(creator=creator, privacy_level='private', name="Block Status Test Group")
    GroupBlock.objects.create(group=group, user=blocked_user, blocked_by=creator)
    
    # Log in as the blocked user and view the group
    client = api_client_factory(user=blocked_user)
    response = client.get(f'/api/groups/{group.slug}/')
    
    assert response.status_code == status.HTTP_200_OK
    assert response.json()['membership_status'] == 'blocked'


# --- Test Set 2: PUBLIC GROUP JOIN LOGIC ---

def test_user_can_join_public_group_directly(user_factory, api_client_factory):
    """
    Verifies that a user is added as a member immediately upon joining a public group,
    without creating a join request. This complements the existing private group tests.
    """
    creator, joiner = user_factory(), user_factory()
    group = Group.objects.create(creator=creator, name="A Public Group", privacy_level='public')
    
    client = api_client_factory(user=joiner)
    response = client.post(f"/api/groups/{group.slug}/membership/")
    
    assert response.status_code == status.HTTP_201_CREATED
    assert group.members.filter(id=joiner.id).exists()
    assert not GroupJoinRequest.objects.filter(group=group, user=joiner).exists()

# --- Test Set 3: MEMBER LEAVE LOGIC ---

def test_regular_member_can_leave_group(user_factory, api_client_factory):
    """Verifies a non-creator member can successfully leave a group."""
    creator, member = user_factory(), user_factory()
    group = Group.objects.create(creator=creator)
    group.members.add(creator, member)
    
    client = api_client_factory(user=member)
    response = client.delete(f'/api/groups/{group.slug}/membership/')
    
    assert response.status_code == status.HTTP_204_NO_CONTENT
    group.refresh_from_db()
    assert not group.members.filter(id=member.id).exists()
    assert group.members.count() == 1 # Check the count is updated

def test_creator_of_populated_group_cannot_leave_via_membership_endpoint(user_factory, api_client_factory):
    """Verifies the creator cannot use the 'leave' endpoint if other members exist."""
    creator, member = user_factory(), user_factory()
    group = Group.objects.create(creator=creator)
    group.members.add(creator, member)
    
    client = api_client_factory(user=creator)
    response = client.delete(f'/api/groups/{group.slug}/membership/')
    
    # Your GroupMembershipView correctly forbids this, expecting a transfer or delete flow.
    assert response.status_code == status.HTTP_403_FORBIDDEN
    group.refresh_from_db()
    assert group.creator == creator # Ensure creator has not changed

def test_non_member_cannot_leave_group(user_factory, api_client_factory):
    """Verifies that a user not in the group gets an error when trying to leave."""
    creator, non_member = user_factory(), user_factory()
    group = Group.objects.create(creator=creator)
    
    client = api_client_factory(user=non_member)
    response = client.delete(f'/api/groups/{group.slug}/membership/')
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST