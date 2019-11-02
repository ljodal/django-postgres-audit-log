from django.db.backends.postgresql.base import (
    DatabaseWrapper as PostgreSQLDatabaseWrapper,
)

from ...schema import SchemaEditor


class DatabaseWrapper(PostgreSQLDatabaseWrapper):
    """
    A subclass of the PostgreSQL databasw wrapper with an extended schema editor.
    """

    SchemaEditorClass = SchemaEditor
