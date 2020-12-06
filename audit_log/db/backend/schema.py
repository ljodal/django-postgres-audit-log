"""
This defines a custom SchemaEditor class with some extensions.
"""
from typing import Any, Type

from django.apps import apps
from django.conf import settings
from django.db.backends.postgresql.schema import (
    DatabaseSchemaEditor as PostgreSQLSchemaEditor,
)
from django.db.models import Model
from django.utils.module_loading import import_string

from ... import fields, utils


class SchemaEditor(PostgreSQLSchemaEditor):
    """
    A subclass of the normal PostgreSQL schema editor extended with
    functionality required to keep track of audit logging.
    """

    # pylint: disable=abstract-method

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        app_label, model_name = settings.AUDIT_LOG_CONTEXT_MODEL.rsplit(".", 1)
        self._context_model = apps.get_model(app_label, model_name)

        app_label, model_name = settings.AUDIT_LOG_ENTRY_MODEL.rsplit(".", 1)
        self._log_entry_model = apps.get_model(app_label, model_name)

        self._audit_logged_model = import_string("audit_log.models.AuditLoggedModel")

    def create_model(self, model: Type[Model]) -> None:

        super().create_model(model)

        if any(
            isinstance(field, fields.AuditLogsField)
            for field in model._meta.local_fields
        ):
            self.create_audit_logging_triggers(audit_logged_model=model)

    def delete_model(self, model: Type[Model]) -> None:

        if any(
            isinstance(field, fields.AuditLogsField)
            for field in model._meta.local_fields
        ):
            self.drop_audit_logging_triggers(audit_logged_model=model)

        super().create_model(model)

    def create_audit_logging_triggers(self, *, audit_logged_model: Type[Model]) -> None:
        """
        Add audit logging triggers for class
        """

        self.deferred_sql.append(
            utils.create_trigger_function_sql(
                audit_logged_model=audit_logged_model,
                context_model=self._context_model,
                log_entry_model=self._log_entry_model,
            )
        )
        self.deferred_sql.extend(
            utils.create_triggers_sql(audit_logged_model=audit_logged_model)
        )

        # Make sure the ContentType object exists for the model, as we need that
        # for the trigger.
        self.deferred_sql.append(
            utils.create_content_type(audit_logged_model=audit_logged_model)
        )

    def drop_audit_logging_triggers(self, *, audit_logged_model: Type[Model]) -> None:
        """
        Remove audit logging triggers for class
        """

        self.deferred_sql.extend(
            utils.drop_triggers_sql(audit_logged_model=audit_logged_model)
        )
        self.deferred_sql.append(
            utils.drop_trigger_function_sql(audit_logged_model=audit_logged_model)
        )
