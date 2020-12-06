from __future__ import annotations

from typing import Any, Mapping, Tuple, Type, cast

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from django.db import models
from django.http import HttpRequest

from . import fields


class BaseContext(models.Model):
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
        choices=settings.AUDIT_LOG_CONTEXT_TYPE_CHOICES,
    )
    context = models.JSONField()

    class Meta:
        abstract = True

    @classmethod
    def create_from_request(cls, request: HttpRequest) -> BaseContext:
        """
        Create audit logging context from the given HTTP request object.
        """

        return cast(
            BaseContext,
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
        kwargs: Mapping[str, Any],
    ) -> BaseContext:
        """
        Insert audit logging context data when a management command is run.
        """

        return cast(
            BaseContext,
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


class BaseLogEntry(models.Model):
    """
    Base class for audit log entries
    """

    # We use a generic foreign key fron Django's contenttypes framework to
    # identify the object that was changed.
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField(null=True)

    log_object = GenericForeignKey("content_type", "object_id")

    # Track the user that performed the action.
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )

    # Context for the change, like if it was an HTTP request, a managment
    # command, or a celery task.
    context_type = models.CharField(
        max_length=128,
        choices=settings.AUDIT_LOG_CONTEXT_TYPE_CHOICES,
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
    Base class for audit logged model instances. This doesn't add any fields,
    but it adds a relation back to the audit log entries for this model, to
    allow easy access.

    When the custom database engine is enabled this will also pick up any
    subclasses of this and automatically add the audit logging triggers to the
    database.
    """

    audit_logs = fields.AuditLogsField()

    class Meta:
        abstract = True
