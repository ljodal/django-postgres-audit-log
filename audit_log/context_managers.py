from contextlib import contextmanager
from typing import Any, Callable, Dict, Type

from django.db import connection, models


@contextmanager
def audit_logging(
    *,
    create_temporary_table_sql: str,
    drop_temporary_table_sql: str,
    create_context: Callable[[], Any],
):
    with connection.cursor() as cursor:
        cursor.execute(create_temporary_table_sql)

    create_context()

    try:
        yield
    finally:
        with connection.cursor() as cursor:
            cursor.execute(drop_temporary_table_sql)
