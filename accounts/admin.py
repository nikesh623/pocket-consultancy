
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "role",
        "approval_status",
        "is_active",
        "is_staff",
    )

    list_filter = (
        "role",
        "approval_status",
        "is_active",
        "is_staff",
    )

    search_fields = (
        "username",
        "email",
        "first_name",
        "last_name",
    )

    fieldsets = UserAdmin.fieldsets + (
        (
            "Pocket Consultancy",
            {
                "fields": (
                    "role",
                    "approval_status",
                )
            },
        ),
    )  # type: ignore

    add_fieldsets = UserAdmin.add_fieldsets + (
        (
            "Additional information",
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "first_name",
                    "last_name",
                    "role",
                    "approval_status",
                ),
            },
        ),
    )

    actions = (
        "approve_accounts",
        "reject_accounts",
    )

    @admin.action(description="Approve selected accounts")
    def approve_accounts(self, request, queryset):
        updated = queryset.filter(
            is_superuser=False,
        ).update(
            approval_status=User.ApprovalStatus.APPROVED,
            is_active=True,
        )

        self.message_user(
            request,
            f"{updated} account(s) approved.",
        )

    @admin.action(description="Reject selected accounts")
    def reject_accounts(self, request, queryset):
        updated = queryset.filter(
            is_superuser=False,
        ).update(
            approval_status=User.ApprovalStatus.REJECTED,
            is_active=False,
        )

        self.message_user(
            request,
            f"{updated} account(s) rejected.",
        )

    def save_model(self, request, obj, form, change):
        # Keep the authentication flag consistent with approval status.
        if not obj.is_superuser:
            obj.is_active = (
                obj.approval_status
                == User.ApprovalStatus.APPROVED
            )

        super().save_model(request, obj, form, change)
