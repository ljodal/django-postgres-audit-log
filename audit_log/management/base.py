from typing import Any

from django.apps import apps
from django.conf import settings
from django.core.management.base import BaseCommand

from ..context_managers import audit_logging
from ..utils import create_temporary_table_sql, drop_temporary_table_sql


class AuditLoggedCommand(BaseCommand):
    """
    This sub-class of Django's `BaseCommand` overrides `execute` to add audit
    logging to the command.
    """

    def execute(self, *args: Any, **kwargs: Any) -> Any:

        # Dynamically get the context model from settings
        app_label, model_name = settings.AUDIT_LOGGING_CONTEXT_MODEL.rsplit(".", 1)
        context_model = apps.get_model(app_label=app_label, model_name=model_name)

        with audit_logging(
            create_temporary_table_sql=create_temporary_table_sql(context_model),
            drop_temporary_table_sql=drop_temporary_table_sql(context_model),
            create_context=lambda: context_model.objects.create_from_management_command(
                cls=self.__class__, args=args, kwargs=kwargs
            ),
        ):
            # Continue as normal
            return super().execute(*args, **kwargs)

    def handle(self, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError(
            "Subclasses of AuditLoggedCommand must provide a handle() method"
        )
