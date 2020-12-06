from audit_log.models import AuditLoggedModel, BaseContext, BaseLogEntry
from django.db import models


class AuditLogContext(BaseContext):
    """
    Class for storing audit logging context information
    """

    class Meta:
        managed = False


class AuditLogEntry(BaseLogEntry):
    """
    An audit log entry
    """


class MyNonAuditLoggedModel(models.Model):
    """
    A model that is not audit logged
    """

    some_text = models.TextField()


class MyAuditLoggedModel(AuditLoggedModel):
    """
    A model that is audit logged.
    """

    some_text = models.TextField()
