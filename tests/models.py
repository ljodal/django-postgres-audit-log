from django.db import models

from audit_log import AuditLoggingBaseContext, audit_logged


class AuditLoggingContext(AuditLoggingBaseContext):
    """
    Class for storing audit logging context information
    """

    class Meta:
        managed = False


class NonAuditLoggedModel(models.Model):
    """
    A model that is not audit logged
    """

    some_text = models.TextField()


@audit_logged()
class AuditLoggedModel(models.Model):
    """
    A model that is audit logged.
    """

    some_text = models.TextField()