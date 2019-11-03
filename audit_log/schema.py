"""
This defines a custom SchemaEditor class with some extensions.
"""
from typing import TYPE_CHECKING, Any, Type

from django.apps import apps
from django.conf import settings
from django.db import models
from django.db.backends.postgresql.schema import (
    DatabaseSchemaEditor as PostgreSQLSchemaEditor,
)
from django.utils.module_loading import import_string

from .utils import (
    create_trigger_function_sql,
    create_triggers_sql,
    drop_trigger_function_sql,
    drop_triggers_sql,
)

if TYPE_CHECKING:
    from .models import AuditLogEntry  # noqa


class SchemaEditor(PostgreSQLSchemaEditor):
    """
    A subclass of the normal PostgreSQL schema editor extended with
    functionality required to keep track of audit logging.
    """

    # pylint: disable=abstract-method

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        # Dynamically get the context model from settings
        app_label, model_name = settings.AUDIT_LOGGING_CONTEXT_MODEL.rsplit(".", 1)
        self._context_model = apps.get_model(app_label=app_label, model_name=model_name)
        self._log_entry_base_class: Type["AuditLogEntry"] = import_string(
            settings.AUDIT_LOGGING_LOG_ENTRY_CLASS
        )

    def create_model(self, model: Type[models.Model]) -> None:

        super().create_model(model)

        if issubclass(model, self._log_entry_base_class):
            self.create_audit_logging_triggers(
                audit_log_model=model,
                audit_logged_model=model.get_audit_logged_model(),
            )

    def delete_model(self, model: Type[models.Model]) -> None:

        if issubclass(model, self._log_entry_base_class):
            self.drop_audit_logging_triggers(
                audit_log_model=model,
                audit_logged_model=model.get_audit_logged_model(),
            )

        super().create_model(model)

    def create_audit_logging_triggers(
        self,
        *,
        audit_log_model: Type[models.Model],
        audit_logged_model: Type[models.Model]
    ) -> None:
        """
        Add audit logging triggers for class
        """

        self.deferred_sql.append(
            create_trigger_function_sql(
                audit_log_model=audit_log_model,
                audit_logged_model=audit_logged_model,
                context_model=self._context_model,
            )
        )
        self.deferred_sql.extend(
            create_triggers_sql(audit_logged_model=audit_logged_model)
        )

    def drop_audit_logging_triggers(
        self,
        *,
        audit_log_model: Type[models.Model],
        audit_logged_model: Type[models.Model]
    ) -> None:
        """
        Remove audit logging triggers for class
        """

        self.deferred_sql.extend(
            drop_triggers_sql(audit_logged_model=audit_logged_model)
        )
        self.deferred_sql.append(
            drop_trigger_function_sql(audit_logged_model=audit_logged_model,)
        )
