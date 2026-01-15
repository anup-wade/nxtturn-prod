from rest_framework import permissions
from django.shortcuts import get_object_or_404
from .models import Group


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object (profile) to edit it.
    Assumes the model instance has a `user` attribute.
    Read permissions are allowed to any request (GET, HEAD, OPTIONS).
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner of the profile.
        # Assumes the model instance has a 'user' attribute.
        # For UserProfile, obj is the UserProfile instance, so obj.user is the owner.
        # --- UPDATED OWNERSHIP CHECK ---
        # Check common attribute names for the owner/author.
        # Add more checks here if your models use different field names.
        if hasattr(obj, "author"):
            # Check if the object's author is the requesting user
            return obj.author == request.user
        elif hasattr(obj, "user"):
            # Check if the object's user is the requesting user (e.g., for UserProfile)
            return obj.user == request.user
        # Add more elif checks here if needed for other owner field names

        # 3. --- NEW: Check 'user_profile' field (Education, Experience) ---
        elif hasattr(obj, "user_profile"):
            return obj.user_profile.user == request.user

        # If no owner attribute found or doesn't match, deny permission
        return False
        # --- END OF UPDATED CHECK ---


# In C:\Users\Vinay\Project\Loopline\community\permissions.py


# --- REPLACEMENT FOR THE IsGroupMember CLASS ---
class IsGroupMember(permissions.BasePermission):
    """
    Custom permission to only allow members of a specified group to create content within it.
    This version correctly handles a 'group' SLUG from the request.data.
    """

    message = "You must be a member of this group to perform this action."

    def has_permission(self, request, view):
        # Read operations are not handled by this permission; it's for creation (POST).
        # We assume another permission like IsAuthenticated handles GET.
        # This simplifies the logic. If it's not a POST, we don't block.
        if request.method != "POST":
            return True

        # For POST requests, the user must be authenticated.
        if not request.user or not request.user.is_authenticated:
            return False

        # --- THIS IS THE CORE FIX ---
        # 1. We now look for a 'group' SLUG in the request data.
        group_slug = request.data.get("group")

        # 2. If no group slug is provided, this is a main feed post.
        #    This permission should not block it. The view's IsAuthenticated handles it.
        if not group_slug:
            return True

        # 3. If a group slug IS provided, we look up the group by the slug.
        try:
            group = Group.objects.get(slug=group_slug)
            # Check if the requesting user is a member of this group.
            return group.members.filter(pk=request.user.pk).exists()
        except Group.DoesNotExist:
            # If the group slug is invalid, deny permission.
            return False


class IsCreatorOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow the creator of a group to edit or delete it.
    """

    message = "You must be the creator of this group to perform this action."

    def has_object_permission(self, request, view, obj):
        # Read permissions (GET, HEAD, OPTIONS) are allowed for any request.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions (DELETE, PUT, PATCH) are only allowed to the creator of the group.
        # This assumes the object 'obj' is a Group instance.
        return obj.creator == request.user


class IsGroupCreator(permissions.BasePermission):
    """
    Custom permission to only allow the creator of a group to perform an action.
    This permission checks the group based on a 'slug' from the URL kwargs.
    """

    message = "You must be the creator of this group to perform this action."

    def has_permission(self, request, view):
        # Retrieve the group slug from the URL
        group_slug = view.kwargs.get("slug")
        if not group_slug:
            return False

        # Find the group
        try:
            group = Group.objects.get(slug=group_slug)
        except Group.DoesNotExist:
            return False  # No group found, deny access.

        # Check if the authenticated user is the creator of the group
        if request.user and request.user.is_authenticated:
            return group.creator == request.user

        return False


class IsGroupMemberOrPublicReadOnly(permissions.BasePermission):
    """
    Custom permission for viewing and editing a group.
    - Allows ANYONE to view a group's basic details (GET).
    - Hides sensitive data at the serializer level.
    - Allows ONLY THE CREATOR to edit/delete any group.
    """

    def has_object_permission(self, request, view, obj):
        # 'obj' here is the Group instance.

        # === THIS IS THE CORE CHANGE ===
        # Allow ALL read-only requests (GET, HEAD, OPTIONS).
        # The serializer will be responsible for hiding sensitive data.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions (PATCH, DELETE) are still only for the creator.
        if not request.user.is_authenticated:
            return False
        return obj.creator == request.user
