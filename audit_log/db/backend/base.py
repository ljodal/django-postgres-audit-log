from django.db.backends.postgresql.base import (
    DatabaseWrapper as PostgreSQLDatabaseWrapper,
)

from ...schema import SchemaEditor


class DatabaseWrapper(PostgreSQLDatabaseWrapper):
    SchemaEditorClass = SchemaEditor
