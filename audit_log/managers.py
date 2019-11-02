from typing import TYPE_CHECKING, Any, Dict, List, Type, cast

from django.db import models
from django.http import HttpRequest

from .management.base import AuditLoggedCommand

if TYPE_CHECKING:
    from .models import AuditLoggingBaseContext  # pylint: disable=cyclic-import


class AuditLoggingBaseContextManager(models.Manager):
    """
    Manager for the AuditLoggingBaseContext model, with helpers to create various
    models.
    """

    def create_from_request(self, request: HttpRequest) -> "AuditLoggingBaseContext":
        """
        Create audit logging context from the given HTTP request object.
        """

        return cast(
            "AuditLoggingBaseContext",
            self.create(
                performed_by_id=getattr(request.user, "id", None),
                context_type="http_request",
                context={},
            ),
        )

    def create_from_management_command(
        self, *, cls: Type[AuditLoggedCommand], args: List[Any], kwargs: Dict[str, Any]
    ) -> "AuditLoggingBaseContext":
        """
        Insert audit logging context data when a management command is run.
        """

        return cast(
            "AuditLoggingBaseContext",
            self.create(
                request_type="management-command",
                context={
                    # Get the name of the command in the same way Django does in
                    # the call_command utility.
                    "name": cls.__module__.split(".")[-1],
                    # Include args and kwargs in the request log. This handles
                    # most common argument types like file etc. For anything not
                    # handled by default the user must provide a function that
                    # converts the value to a JSON encodeable value.
                    "args": args,
                    "kwargs": kwargs,
                },
            ),
        )
