# community/admin.py (Final Version with Autocomplete Fix)

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth import get_user_model
from django.utils.html import format_html
from django.urls import reverse, NoReverseMatch
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.shortcuts import redirect

# Import from allauth to customize its admin
from allauth.account.models import EmailAddress
from allauth.account.admin import EmailAddressAdmin

# --- Import your models ---
from .models import (
    UserProfile,
    Follow,
    StatusPost,
    Group,
    Comment,
    Like,
    Notification,
    Report,
)

User = get_user_model()


# --- Define the Inline Admin for UserProfile ---
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = "Profile"
    fk_name = "user"


# --- Define the Custom User Admin ---
class CustomUserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ("username", "email", "first_name", "last_name", "is_staff")
    list_select_related = ("profile",)

    # --- THIS IS A NEW, REQUIRED ADDITION ---
    # To enable autocomplete on the User model, we must tell Django
    # which fields are searchable.
    search_fields = ("username", "email", "first_name", "last_name")
    # --- END OF NEW ADDITION ---

    def get_inline_instances(self, request, obj=None):
        if not obj:
            return list()
        return super().get_inline_instances(request, obj)


# --- Unregister the default User admin and register the custom one ---
try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass
admin.site.register(User, CustomUserAdmin)


# --- FIX FOR EmailAddress Admin Display (Now with Autocomplete) ---
class CustomEmailAddressAdmin(EmailAddressAdmin):
    """
    Overrides the default EmailAddressAdmin to use a scalable autocomplete widget.
    """

    # --- THIS IS THE CHANGED LINE ---
    # We are switching from the dropdown/raw_id to the superior autocomplete widget.
    autocomplete_fields = ["user"]
    # --- END OF CHANGED LINE ---

    # We keep search_fields here for the EmailAddress list view itself.
    search_fields = ("user__username", "email")


# Unregister the default and register our custom version
try:
    admin.site.unregister(EmailAddress)
except admin.sites.NotRegistered:
    pass
admin.site.register(EmailAddress, CustomEmailAddressAdmin)
# --- END OF FIX ---


# --- Registrations for your other models ---


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "get_bio_preview", "picture_tag")
    search_fields = ("user__username", "bio", "college_name")
    list_select_related = ("user",)

    def get_bio_preview(self, obj):
        if obj.bio:
            return obj.bio[:50] + "..." if len(obj.bio) > 50 else obj.bio
        return "---"

    get_bio_preview.short_description = "Bio Preview"

    def picture_tag(self, obj):
        if obj.picture and hasattr(obj.picture, "url"):
            return format_html(
                '<img src="{}" style="max-height: 50px; max-width: 50px;" />',
                obj.picture.url,
            )
        return "No Image"

    picture_tag.short_description = "Picture"


admin.site.register(Follow)
admin.site.register(Group)
admin.site.register(Comment)
admin.site.register(Like)


@admin.register(StatusPost)
class StatusPostAdmin(admin.ModelAdmin):
    list_display = ("id", "author", "content_preview", "created_at")
    list_filter = ("created_at", "author")
    search_fields = ("content", "author__username")
    readonly_fields = ("image_tag_detail", "video_player_detail")

    def content_preview(self, obj):
        return (
            obj.content[:50] + "..."
            if obj.content and len(obj.content) > 50
            else obj.content
        )

    def image_tag_detail(self, obj):
        # Assuming you'll have a related PostMedia, this needs adjustment
        # For now, this is a placeholder
        return "Preview logic to be updated for PostMedia model"

    image_tag_detail.short_description = "Image Preview"

    def video_player_detail(self, obj):
        # Assuming you'll have a related PostMedia, this needs adjustment
        return "Preview logic to be updated for PostMedia model"

    video_player_detail.short_description = "Video Preview"


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "recipient_username_link",
        "actor_username_link",
        "verb",
        "notification_type",
        "target_link",
        "action_object_link",
        "is_read",
        "timestamp",
    )
    list_filter = (
        "is_read",
        "notification_type",
        "timestamp",
        "recipient__username",
        "actor__username",
    )
    search_fields = ("recipient__username", "actor__username", "verb")
    list_select_related = (
        "recipient",
        "actor",
        "target_content_type",
        "action_object_content_type",
    )
    date_hierarchy = "timestamp"

    readonly_fields = (
        "recipient_username_link",
        "actor_username_link",
        "verb",
        "notification_type",
        "action_object_link",
        "target_link",
        "timestamp",
    )

    def _get_admin_obj_url(self, obj_instance):
        if not obj_instance:
            return None
        obj_content_type = ContentType.objects.get_for_model(obj_instance.__class__)
        url_name = f"admin:{obj_content_type.app_label}_{obj_content_type.model}_change"
        try:
            return reverse(url_name, args=(obj_instance.pk,))
        except NoReverseMatch:
            return None

    def recipient_username_link(self, obj):
        if obj.recipient:
            url = self._get_admin_obj_url(obj.recipient)
            if url:
                return format_html('<a href="{}">{}</a>', url, obj.recipient.username)
            return obj.recipient.username
        return "N/A"

    recipient_username_link.short_description = "Recipient"

    def actor_username_link(self, obj):
        if obj.actor:
            url = self._get_admin_obj_url(obj.actor)
            if url:
                return format_html('<a href="{}">{}</a>', url, obj.actor.username)
            return obj.actor.username
        return "N/A"

    actor_username_link.short_description = "Actor"

    def action_object_link(self, obj):
        if obj.action_object:
            url = self._get_admin_obj_url(obj.action_object)
            obj_str = str(obj.action_object)[:30] + (
                "..." if len(str(obj.action_object)) > 30 else ""
            )
            if url:
                return format_html(
                    '<a href="{}">{} ({})</a>',
                    url,
                    obj_str,
                    obj.action_object_content_type.model,
                )
            return f"{obj_str} ({obj.action_object_content_type.model})"
        return "N/A"

    action_object_link.short_description = "Action Object"

    def target_link(self, obj):
        if obj.target:
            url = self._get_admin_obj_url(obj.target)
            obj_str = str(obj.target)[:30] + (
                "..." if len(str(obj.target)) > 30 else ""
            )
            if url:
                return format_html(
                    '<a href="{}">{} ({})</a>',
                    url,
                    obj_str,
                    obj.target_content_type.model,
                )
            return f"{obj_str} ({obj.target_content_type.model})"
        return "N/A"

    target_link.short_description = "Target Object"


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "reporter_link",
        "content_author_link",
        "content_object_link",
        "reason",
        "status",
        "created_at",
        "moderator",
    )
    list_filter = ("status", "reason", "created_at", "content_type")
    search_fields = ("reporter__username", "details", "moderator__username")
    list_editable = ("status",)

    actions = ["delete_reported_content", "dismiss_reports"]

    readonly_fields = (
        "reporter_link",
        "content_author_link",
        "content_type",
        "object_id",
        "content_object_link",
        "created_at",
        "moderated_at",
        "moderator",
    )

    fieldsets = (
        (
            "Report Details",
            {"fields": ("reporter_link", "reason", "details", "created_at")},
        ),
        (
            "Reported Content",
            {"fields": ("content_author_link", "content_object_link")},
        ),
        (
            "Moderation",
            {"fields": ("status", "moderator", "moderator_notes", "moderated_at")},
        ),
    )

    @admin.action(description='Delete reported content and mark as "Action Taken"')
    def delete_reported_content(self, request, queryset):
        items_deleted = 0
        for report in queryset:
            if report.content_object:
                report.content_object.delete()
                items_deleted += 1
        queryset.update(
            status="ACTION_TAKEN",
            moderator=request.user,
            moderated_at=timezone.now(),
            moderator_notes=f"Content deleted by {request.user.username} via admin action.",
        )
        self.message_user(
            request, f"{items_deleted} piece(s) of content were successfully deleted."
        )

    @admin.action(description='Mark selected reports as "Dismissed"')
    def dismiss_reports(self, request, queryset):
        updated_count = queryset.update(
            status="DISMISSED",
            moderator=request.user,
            moderated_at=timezone.now(),
            moderator_notes=f"Report dismissed by {request.user.username} via admin action.",
        )
        self.message_user(
            request, f"{updated_count} report(s) were successfully marked as dismissed."
        )

    def reporter_link(self, obj):
        url = (
            reverse("admin:community_report_changelist")
            + f"?reporter__id__exact={obj.reporter.id}"
        )
        return format_html(
            '<a href="{}">{} (See all reports)</a>', url, obj.reporter.username
        )

    reporter_link.short_description = "Reporter"

    def content_author_link(self, obj):
        if hasattr(obj.content_object, "author"):
            author = obj.content_object.author
            url = (
                reverse("admin:community_report_changelist")
                + f'?object_id__in={author.status_posts.values_list("id", flat=True)}'
            )
            return format_html(
                '<a href="{}">{} (See reports for user)</a>', url, author.username
            )
        return "N/A"

    content_author_link.short_description = "Content Author"

    def content_object_link(self, obj):
        if obj.content_object:
            content_str = str(obj.content_object)
            display_text = (
                (content_str[:75] + "...") if len(content_str) > 75 else content_str
            )
            admin_url = reverse(
                f"admin:{obj.content_type.app_label}_{obj.content_type.model}_change",
                args=[obj.object_id],
            )
            return format_html(
                '<a href="{}" target="_blank">{}</a>', admin_url, display_text
            )
        return "Content not found or has been deleted"

    content_object_link.short_description = "Reported Content"

    def response_change(self, request, obj):
        if "_delete_content_and_resolve" in request.POST:
            if obj.content_object:
                obj.content_object.delete()
                obj.status = "ACTION_TAKEN"
                obj.moderator = request.user
                obj.moderated_at = timezone.now()
                obj.moderator_notes = f"Content deleted by {request.user.username} from report detail view."
                obj.save()
                self.message_user(
                    request,
                    "The reported content has been deleted and the report marked as resolved.",
                )
            else:
                self.message_user(
                    request,
                    "Reported content was already deleted. Marked as resolved.",
                    level="warning",
                )
            return redirect("admin:community_report_changelist")

        if "_dismiss_report" in request.POST:
            obj.status = "DISMISSED"
            obj.moderator = request.user
            obj.moderated_at = timezone.now()
            obj.moderator_notes = (
                f"Report dismissed by {request.user.username} from report detail view."
            )
            obj.save()
            self.message_user(request, "The report has been dismissed.")
            return redirect("admin:community_report_changelist")

        return super().response_change(request, obj)

    def change_view(self, request, object_id, form_url="", extra_context=None):
        extra_context = extra_context or {}
        extra_context["show_custom_actions"] = True
        return super().change_view(
            request, object_id, form_url, extra_context=extra_context
        )
