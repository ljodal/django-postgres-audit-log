from typing import Any, Generator

import pytest

from audit_log.context_managers import audit_logging
from audit_log.utils import create_temporary_table_sql, drop_temporary_table_sql

from ..models import AuditLogContext

# pylint: disable=unused-argument,invalid-name


@pytest.fixture
def audit_logging_context(db: Any) -> Generator[AuditLogContext, None, None]:
    """
    Fixture that provides audit logging context
    """

    with audit_logging(
        create_temporary_table_sql=create_temporary_table_sql(AuditLogContext),
        drop_temporary_table_sql=drop_temporary_table_sql(AuditLogContext),
        create_context=lambda: AuditLogContext.objects.create(
            context_type="test", context={}
        ),
    ) as context:
        yield context
