from django.db import models
from django.db.models.options import Options
from typing_extensions import Protocol


class AuditLogEntryModel(Protocol):
    """
    Protocol definition for the dynamic audit log entry class created when
    decorating a class with @audit_logged
    """

    @classmethod
    def get_trigger_name(cls) -> str:
        """
        Get the name of the trigger used to update this table.
        """
        ...

    @classmethod
    def get_audit_logged_model(cls) -> models.Model:
        """
        Get the model that this table is an audit log table for.
        """

        ...

    @classmethod
    def get_fk_column(cls) -> str:
        """
        Get the name of the foreign key column to the audit logged model.
        """

        ...

    _meta: Options
