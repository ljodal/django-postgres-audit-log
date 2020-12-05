from __future__ import annotations

from typing import Any, Callable, Mapping, Tuple, Type, cast

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import models
from django.http import HttpRequest


class AuditLoggingBaseContext(models.Model):
    """
    A base class for providing audit logging context.
    """

    # A reference to the user.
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL
    )

    # This is marked as the primary key to stop Django from creating an id field.
    # This has no other effects, as we ignore this when creating the temporary table
    context_type = models.CharField(
        primary_key=True,
        max_length=128,
        choices=settings.AUDIT_LOGGING_CONTEXT_TYPE_CHOICES,
    )
    context = models.JSONField()

    class Meta:
        abstract = True

    @classmethod
    def create_from_request(cls, request: HttpRequest) -> AuditLoggingBaseContext:
        """
        Create audit logging context from the given HTTP request object.
        """

        return cast(
            AuditLoggingBaseContext,
            cls.objects.create(
                performed_by_id=getattr(request.user, "id", None),
                context_type="http-request",
                context={},
            ),
        )

    @classmethod
    def create_from_management_command(
        cls,
        *,
        command_cls: Type[BaseCommand],
        args: Tuple[Any, ...],
        kwargs: Mapping[str, Any]
    ) -> AuditLoggingBaseContext:
        """
        Insert audit logging context data when a management command is run.
        """

        return cast(
            "AuditLoggingBaseContext",
            cls.objects.create(
                context_type="management-command",
                context={
                    # Get the name of the command in the same way Django does in
                    # the call_command utility.
                    "command": command_cls.__module__.split(".")[-1],
                    # Include args and kwargs in the request log. This handles
                    # most common argument types like file etc. For anything not
                    # handled by default the user must provide a function that
                    # converts the value to a JSON encodeable value.
                    "args": args,
                    "kwargs": kwargs,
                },
            ),
        )


class AuditLogEntry(models.Model):
    """
    Base class for audit log entries
    """

    # Define attributes that we are dynamically adding to subclasses
    get_audit_logged_model: Callable[[], Type[models.Model]]

    # Track the user that performed the action.
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )

    # Context for the change, like if it was an HTTP request, a managment
    # command, or a celery task.
    context_type = models.CharField(
        max_length=128,
        choices=settings.AUDIT_LOGGING_CONTEXT_TYPE_CHOICES,
    )
    context = models.JSONField()

    # The action that was performed.
    action = models.CharField(
        max_length=6,
        choices=(("Insert", "INSERT"), ("Update", "UPDATE"), ("Delete", "DELETE")),
    )

    # The time the action was made
    at = models.DateTimeField()

    # The changes that were made.
    changes = models.JSONField()

    class Meta:
        abstract = True


class AuditLoggedModel(models.Model):
    """
    Base class for audit logged model instances.
    """

    AuditLogEntry: Type[AuditLogEntry]

    class Meta:
        abstract = True
