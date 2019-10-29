from typing import Any, Dict, Optional

from django.contrib.auth.models import AbstractBaseUser
from django.db import connection
from django.http import HttpRequest

from .models import AuditLoggingBaseContext


def configure_audit_logging_context(
    *,
    request_type: str,
    context: Dict[str, Any],
    user: Optional[AbstractBaseUser] = None,
    request: Optional[HttpRequest] = None,
) -> None:
    """
    Create the temporary table used to provide context when audit logging.
    """

    with connection.schema_editor() as schema_editor:
        schema_editor.create_temporary_model(AuditLoggingBaseContext)

    AuditLoggingBaseContext.objects.create()


def remove_audit_logging_context():
    """
    Remove the temporary table we created to provide audit logging context.
    """

    with connection.schema_editor() as schema_editor:
        schema_editor.delete_temporary_model(AuditLoggingBaseContext)
