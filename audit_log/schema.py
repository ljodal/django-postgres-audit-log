"""
This defines a custom SchemaEditor class with some extensions.
"""

from django.db.backends.postgres.schema import (
    DatabaseSchemaEditor as PostgreSQLSchemaEditor,
)

from .utils import create_temporary_table_sql, drop_temporary_table_sql


class SchemaEditor(PostgreSQLSchemaEditor):
    """
    A subclass of the normal PostgreSQL schema editor extended with
    functionality required to keep track of audit logging.
    """

    # pylint: disable=abstract-method

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
