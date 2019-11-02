from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.db import models

from .managers import AuditLoggingBaseContextManager


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
    context = JSONField()

    objects = AuditLoggingBaseContextManager()

    class Meta:
        abstract = True


class AuditLogEntry(models.Model):
    """
    Base class for audit log entries
    """

    # Track the user that performed the action.
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )

    # Context for the change, like if it was an HTTP request, a managment
    # command, or a celery task.
    context_type = models.CharField(
        max_length=128, choices=settings.AUDIT_LOGGING_CONTEXT_TYPE_CHOICES,
    )
    context = JSONField()

    # The action that was performed.
    action = models.CharField(
        max_length=6,
        choices=(("Insert", "INSERT"), ("Update", "UPDATE"), ("Delete", "DELETE")),
    )

    # The time the action was made
    at = models.DateTimeField()

    # The changes that were made.
    changes = JSONField()

    class Meta:
        abstract = True
