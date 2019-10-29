import pytest
from django.db import connection

from audit_log.utils import create_temporary_table_sql, drop_temporary_table_sql

from ..models import AuditLoggingContext

pytestmark = pytest.mark.django_db


def test_temporary_table_sql():

    table_name = AuditLoggingContext._meta.db_table

    with connection.cursor() as cursor:

        #
        # First create the temporary table
        #

        sql, args = create_temporary_table_sql(AuditLoggingContext)

        assert sql == (
            f'CREATE TEMPORARY TABLE "{table_name}" ('
            'user_id integer CHECK ("user_id" >= 0), '
            "context_type varchar(128) NOT NULL CHECK ("
            "\"context_type\" IN ('http_request', 'management_command', 'celery_task')"
            "), "
            "context jsonb NOT NULL"
            ")"
        )
        assert args == []

        # Verify that PostgeSQL can actually execute this SQL
        cursor.execute(sql, args or None)

        cursor.execute(f'SELECT COUNT(*) FROM "{table_name}"')
        num_rows, *_ = cursor.fetchone()
        assert num_rows == 0

        #
        # Then drop the table
        #

        sql, args = drop_temporary_table_sql(AuditLoggingContext)

        assert sql == f"DROP TABLE {table_name}"
        assert args == []

        # Verify that PostgeSQL can actually execute this SQL
        cursor.execute(sql, args or None)
