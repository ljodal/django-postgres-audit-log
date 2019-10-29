from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.db import models


class AuditLoggingBaseContext(models.Model):
    """
    A base class for providing audit logging context.
    """

    # A reference to the user. This is marked as the primary key to stop
    # Django from creating an id field. This has no other effects, as we ignore
    # this when creating the temporary table.
    user_id = models.PositiveIntegerField(null=True, primary_key=True)

    context_type = models.CharField(
        max_length=128,
        choices=(
            ("HTTP Request", "http_request"),
            ("Management command", "management_command"),
            ("Celery task", "celery_task"),
        ),
    )
    context = JSONField()

    class Meta:
        abstract = True


class AuditLogEntry(models.Model):
    """
    Base class for audit log entries
    """

    class Meta:
        abstract = True
