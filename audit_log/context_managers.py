from contextlib import contextmanager
from typing import Callable, Generator, TypeVar

from django.db import connection

from . import models

ContextModel = TypeVar("ContextModel", bound=models.AuditLoggingBaseContext)


@contextmanager
def audit_logging(
    *,
    create_temporary_table_sql: str,
    drop_temporary_table_sql: str,
    create_context: Callable[[], ContextModel],
) -> Generator[ContextModel, None, None]:
    """
    Context manager to enable audit logging, and cleaning up afterwards.
    """

    with connection.cursor() as cursor:
        cursor.execute(create_temporary_table_sql)

    context = create_context()

    try:
        yield context
    finally:
        with connection.cursor() as cursor:
            cursor.execute(drop_temporary_table_sql)
