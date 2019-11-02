import pytest  # type: ignore

from audit_log.models import AuditLogEntry

from ..models import AuditLoggedModel

# pylint: disable=no-member,invalid-name


def test_has_audit_log_defined() -> None:
    """
    Test that the audit logged model has an AuditLog attribute.
    """

    assert hasattr(AuditLoggedModel, "AuditLog")
    assert issubclass(AuditLoggedModel.AuditLog, AuditLogEntry)  # type: ignore


@pytest.mark.usefixtures("db")  # type: ignore
def test_can_query_audit_log_table() -> None:
    """
    Test that querying the audit log model works.
    """

    assert AuditLoggedModel.AuditLog.objects.count() == 0  # type: ignore


@pytest.mark.usefixtures("db", "audit_logging_context")  # type: ignore
def test_insert_is_audit_logged() -> None:
    """
    Test that the audit logging context manager works and that we can insert
    data, and that the insert is audit logged.
    """

    AuditLog = AuditLoggedModel.AuditLog  # type: ignore

    model = AuditLoggedModel.objects.create(some_text="Some text")

    assert AuditLog.objects.count() == 1
    log_entry = AuditLog.objects.get()
    assert log_entry.changes == {"id": model.id, "some_text": "Some text"}
    assert log_entry.audit_logged_model == model


@pytest.mark.usefixtures("db", "audit_logging_context")  # type: ignore
def test_update_is_audit_logged() -> None:
    """
    Test that the audit logging context manager works and that we can update
    data, and that the update is audit logged.
    """

    AuditLog = AuditLoggedModel.AuditLog  # type: ignore

    model = AuditLoggedModel.objects.create(some_text="Some text")

    model.some_text = "Updated text"
    model.save(update_fields=["some_text"])

    assert AuditLog.objects.count() == 2
    log_entry = AuditLog.objects.order_by("-id").first()

    assert log_entry.action == "UPDATE"
    assert log_entry.changes == {"some_text": ["Some text", "Updated text"]}
    assert log_entry.audit_logged_model == model


@pytest.mark.usefixtures("db", "audit_logging_context")  # type: ignore
def test_delete_is_audit_logged() -> None:
    """
    Test that the audit logging context manager works and that we can delete
    data, and that the delete is audit logged.
    """

    AuditLog = AuditLoggedModel.AuditLog  # type: ignore

    model = AuditLoggedModel.objects.create(some_text="Some text")

    model.some_text = "Updated text"
    model.save(update_fields=["some_text"])

    model_id = model.id

    model.delete()

    assert AuditLog.objects.count() == 3
    log_entry = AuditLog.objects.order_by("-id").first()

    assert log_entry.action == "DELETE"
    assert log_entry.changes == {"id": model_id, "some_text": "Updated text"}
    assert log_entry.audit_logged_model is None
