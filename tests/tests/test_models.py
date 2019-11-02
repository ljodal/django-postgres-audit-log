import pytest  # type: ignore

from audit_log.context_managers import audit_logging
from audit_log.models import AuditLogEntry
from audit_log.utils import create_temporary_table_sql, drop_temporary_table_sql

from ..models import AuditLoggedModel, AuditLoggingContext

# pylint: disable=no-member


def test_has_audit_log_defined() -> None:

    assert hasattr(AuditLoggedModel, "AuditLog")
    assert issubclass(AuditLoggedModel.AuditLog, AuditLogEntry)  # type: ignore


@pytest.mark.usefixtures("db")  # type: ignore
def test_can_query_audit_log_table() -> None:

    assert AuditLoggedModel.AuditLog.objects.count() == 0  # type: ignore


@pytest.mark.usefixtures("db")  # type: ignore
def test_insert_is_audit_logged() -> None:

    with audit_logging(
        create_temporary_table_sql=create_temporary_table_sql(AuditLoggingContext),
        drop_temporary_table_sql=drop_temporary_table_sql(AuditLoggingContext),
        create_context=lambda: AuditLoggingContext.objects.create(
            context_type="other", context={}
        ),
    ):
        model = AuditLoggedModel.objects.create(some_text="Some text")

    assert AuditLoggedModel.AuditLog.objects.count() == 1  # type: ignore
    log_entry = AuditLoggedModel.AuditLog.objects.get()  # type: ignore
    assert log_entry.changes == {"id": model.id, "some_text": "Some text"}
