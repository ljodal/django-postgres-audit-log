from typing import TYPE_CHECKING, Any, Type, cast

from django.apps import apps
from django.conf import settings
from django.core.management.base import BaseCommand

from ..context_managers import audit_logging
from ..utils import create_temporary_table_sql, drop_temporary_table_sql

if TYPE_CHECKING:
    from ..models import AuditLoggingBaseContext  # noqa pylint: disable=cyclic-import


class AuditLoggedCommand(BaseCommand):
    """
    This sub-class of Django's `BaseCommand` overrides `execute` to add audit
    logging to the command.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:

        super().__init__(*args, **kwargs)

        # Dynamically get the context model from settings
        app_label, model_name = settings.AUDIT_LOGGING_CONTEXT_MODEL.rsplit(".", 1)
        self.context_model: Type["AuditLoggingBaseContext"] = apps.get_model(
            app_label=app_label, model_name=model_name
        )

    def execute(self, *args: Any, **kwargs: Any) -> Any:

        with audit_logging(
            create_temporary_table_sql=create_temporary_table_sql(self.context_model),
            drop_temporary_table_sql=drop_temporary_table_sql(self.context_model),
            create_context=lambda: self.create_context(*args, **kwargs),
        ):
            # Continue as normal
            return super().execute(*args, **kwargs)

    def handle(self, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError(
            "Subclasses of AuditLoggedCommand must provide a handle() method"
        )

    def create_context(self, *args: Any, **kwargs: Any) -> "AuditLoggingBaseContext":
        """
        Create the context needed for audit logging changes made by this command.
        """

        return cast(
            "AuditLoggingBaseContext",
            self.context_model.objects.create_from_management_command(
                cls=self.__class__, args=args, kwargs=kwargs
            ),
        )
