from typing import TYPE_CHECKING

from django.db import models
from django.http import HttpRequest

if TYPE_CHECKING:
    from .models import AuditLoggingBaseContext


class AuditLoggingBaseContextManager(models.Manager):
    def create_from_request(self, request: HttpRequest) -> "AuditLoggingBaseContext":
        """
        Create audit logging context from the given HTTP request object.
        """

        return self.create(
            performed_by_id=getattr(request.user, "id", None),
            context_type="http_request",
            context={},
        )
