"""
This defines a custom SchemaEditor class with some extensions.
"""

from django.apps import apps
from django.conf import settings
from django.db.backends.postgresql.schema import (
    DatabaseSchemaEditor as PostgreSQLSchemaEditor,
)
from django.utils.module_loading import import_string

from .utils import (
    create_temporary_table_sql,
    create_trigger_function_sql,
    create_triggers_sql,
    drop_temporary_table_sql,
)


class SchemaEditor(PostgreSQLSchemaEditor):
    """
    A subclass of the normal PostgreSQL schema editor extended with
    functionality required to keep track of audit logging.
    """

    # pylint: disable=abstract-method

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Dynamically get the context model from settings
        app_label, model_name = settings.AUDIT_LOGGING_CONTEXT_MODEL.rsplit(".", 1)
        self._context_model = apps.get_model(app_label=app_label, model_name=model_name)
        self._log_entry_base_class = import_string(
            settings.AUDIT_LOGGING_LOG_ENTRY_CLASS
        )

    def create_temporary_model(self, model):
        """
        Create a temporary table for the given model.
        """

        table_sql, params = create_temporary_table_sql(model)
        self.connection.execute(table_sql, params or None)

    def delete_temporary_model(self, model):
        """
        Drop a temporary table for the given model.
        """

        table_sql, params = drop_temporary_table_sql(model)
        self.connection.execute(table_sql, params or None)

    def create_model(self, model):

        super().create_model(model)

        if issubclass(model, self._log_entry_base_class):
            self._create_audit_logging_triggers(model)

    def _create_audit_logging_triggers(self, model):
        """
        Add audit logging triggers for class
        """

        self.deferred_sql.append(
            create_trigger_function_sql(
                entry_model=model, context_model=self._context_model
            )
        )
        self.deferred_sql.extend(create_triggers_sql(entry_model=model))
