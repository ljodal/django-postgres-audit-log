"""
This defines a custom SchemaEditor class with some extensions.
"""
from typing import Any, Type

from django.db.backends.postgresql.schema import (
    DatabaseSchemaEditor as PostgreSQLSchemaEditor,
)
from django.db.models import Field, Model

from ... import utils


class SchemaEditor(PostgreSQLSchemaEditor):
    """
    A subclass of the normal PostgreSQL schema editor extended with
    functionality required to keep track of audit logging.
    """

    # pylint: disable=abstract-method

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self._context_model = utils.get_context_model()
        self._log_entry_model = utils.get_log_entry_model()

    def create_model(self, model: Type[Model]) -> None:

        super().create_model(model)

        if utils.has_audit_logs_field(model):
            self.create_audit_logging_triggers(audit_logged_model=model)

    def delete_model(self, model: Type[Model]) -> None:

        if utils.has_audit_logs_field(model):
            self.drop_audit_logging_triggers(audit_logged_model=model)

        super().create_model(model)

    def add_field(self, model: Type[Model], field: Field) -> None:
        super().add_field(model, field)

        if utils.is_audit_logs_field(field):
            self.create_audit_logging_triggers(audit_logged_model=model)

    def remove_field(self, model: Type[Model], field: Field) -> None:
        super().remove_field(model, field)

        if utils.is_audit_logs_field(field):
            self.drop_audit_logging_triggers(audit_logged_model=model)

    ####################
    # Internal helpers #
    ####################

    def create_audit_logging_triggers(self, *, audit_logged_model: Type[Model]) -> None:
        """
        Add audit logging triggers for class
        """

        self.deferred_sql.extend(
            utils.add_audit_logging_sql(
                audit_logged_model=audit_logged_model,
                context_model=self._context_model,
                log_entry_model=self._log_entry_model,
            )
        )

    def drop_audit_logging_triggers(self, *, audit_logged_model: Type[Model]) -> None:
        """
        Remove audit logging triggers for class
        """

        self.deferred_sql.extend(
            utils.remove_audit_logging_sql(audit_logged_model=audit_logged_model)
        )
