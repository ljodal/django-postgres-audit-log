from typing import Any

from audit_log.management.base import AuditLoggedCommand

from ...models import MyAuditLoggedModel


class Command(AuditLoggedCommand):
    """
    Test command to check that audit logging works as expected.
    """

    def handle(self, *args: Any, **kwargs: Any) -> None:
        """
        Write to an audit logged model, just to test
        """

        MyAuditLoggedModel.objects.create(some_text="Hello command")
