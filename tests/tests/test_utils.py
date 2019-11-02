import pytest  # type: ignore
from django.conf import settings
from django.db import connection

from audit_log.utils import create_temporary_table_sql, drop_temporary_table_sql

from ..models import AuditLoggingContext


@pytest.mark.usefixtures("db")  # type: ignore
def test_temporary_table_sql() -> None:
    """
    Test that we can successfully generate the SQL we need to create the
    temporary audit logging table, and then execute that SQL to make sure it
    actually works.
    """

    table_name = AuditLoggingContext._meta.db_table

    with connection.cursor() as cursor:

        #
        # First create the temporary table
        #

        sql = create_temporary_table_sql(AuditLoggingContext)

        context_types = ", ".join(
            f"'{ t }'" for _, t in settings.AUDIT_LOGGING_CONTEXT_TYPE_CHOICES
        )

        assert sql == (
            f'CREATE TEMPORARY TABLE "{table_name}" ('
            "performed_by_id integer, "
            "context_type varchar(128) NOT NULL CHECK ("
            f'"context_type" IN ({ context_types })'
            "), "
            "context jsonb NOT NULL"
            ")"
        )

        # Verify that PostgeSQL can actually execute this SQL
        cursor.execute(sql)

        cursor.execute(f'SELECT COUNT(*) FROM "{table_name}"')
        num_rows, *_ = cursor.fetchone()
        assert num_rows == 0

        #
        # Then drop the table
        #

        sql = drop_temporary_table_sql(AuditLoggingContext)

        assert sql == f"DROP TABLE {table_name}"

        # Verify that PostgeSQL can actually execute this SQL
        cursor.execute(sql)
