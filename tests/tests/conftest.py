from typing import Any, Generator

import pytest

from audit_log.context_managers import audit_logging
from audit_log.utils import create_temporary_table_sql, drop_temporary_table_sql

from ..models import AuditLoggingContext

# pylint: disable=unused-argument,invalid-name


@pytest.fixture  # type: ignore
def audit_logging_context(db: Any) -> Generator[AuditLoggingContext, None, None]:
    """
    Fixture that provides audit logging context
    """

    with audit_logging(
        create_temporary_table_sql=create_temporary_table_sql(AuditLoggingContext),
        drop_temporary_table_sql=drop_temporary_table_sql(AuditLoggingContext),
        create_context=lambda: AuditLoggingContext.objects.create(
            context_type="test", context={}
        ),
    ) as context:
        yield context
