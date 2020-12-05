import pytest
from audit_log.models import AuditLogEntry
from django.db import connection

from ..models import AuditLoggedModel

# pylint: disable=no-member,invalid-name


def test_has_audit_log_defined() -> None:
    """
    Test that the audit logged model has an AuditLog attribute.
    """

    assert hasattr(AuditLoggedModel, "AuditLog")
    assert issubclass(AuditLoggedModel.AuditLog, AuditLogEntry)  # type: ignore


@pytest.mark.usefixtures("db")
def test_can_query_audit_log_table() -> None:
    """
    Test that querying the audit log model works.
    """

    assert AuditLoggedModel.AuditLog.objects.count() == 0  # type: ignore


@pytest.mark.usefixtures("db", "audit_logging_context")
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


@pytest.mark.usefixtures("db", "audit_logging_context")
def test_single_model_update_is_audit_logged() -> None:
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


@pytest.mark.usefixtures("db", "audit_logging_context")
def test_bulk_update_is_audit_logged() -> None:
    """
    Test that the audit logging context manager works and that we can update
    data, and that the update is audit logged.
    """

    AuditLog = AuditLoggedModel.AuditLog  # type: ignore

    model = AuditLoggedModel.objects.create(some_text="Some text")

    AuditLoggedModel.objects.filter(id=model.id).update(some_text="Updated text")

    assert AuditLog.objects.count() == 2

    log_entry = AuditLog.objects.order_by("-id").first()
    assert log_entry.action == "UPDATE"
    assert log_entry.changes == {"some_text": ["Some text", "Updated text"]}
    assert log_entry.audit_logged_model == model


@pytest.mark.usefixtures("db", "audit_logging_context")
def test_sql_update_is_audit_logged() -> None:
    """
    Test that the audit logging context manager works and that we can update
    data, and that the update is audit logged.
    """

    AuditLog = AuditLoggedModel.AuditLog  # type: ignore

    model = AuditLoggedModel.objects.create(some_text="Some text")

    with connection.cursor() as cursor:
        cursor.execute(
            f"UPDATE {AuditLoggedModel._meta.db_table} SET some_text=%s WHERE id=%s",
            ["Updated text", model.id],
        )

    assert AuditLog.objects.count() == 2

    log_entry = AuditLog.objects.order_by("-id").first()
    assert log_entry.action == "UPDATE"
    assert log_entry.changes == {"some_text": ["Some text", "Updated text"]}
    assert log_entry.audit_logged_model == model


@pytest.mark.usefixtures("db", "audit_logging_context")
def test_delete_is_audit_logged() -> None:
    """
    Test that the audit logging context manager works and that we can delete
    data, and that the delete is audit logged.
    """

    AuditLog = AuditLoggedModel.AuditLog  # type: ignore

    model = AuditLoggedModel.objects.create(some_text="Some text")
    model_id = model.id

    model.delete()

    assert AuditLog.objects.count() == 2

    log_entry = AuditLog.objects.order_by("-id").first()
    assert log_entry.action == "DELETE"
    assert log_entry.changes == {"id": model_id, "some_text": "Some text"}
    assert log_entry.audit_logged_model is None


@pytest.mark.usefixtures("db", "audit_logging_context")
def test_bulk_delete_is_audit_logged() -> None:
    """
    Test that the audit logging context manager works and that we can delete
    data, and that the delete is audit logged.
    """

    AuditLog = AuditLoggedModel.AuditLog  # type: ignore

    model = AuditLoggedModel.objects.create(some_text="Some text")
    model_id = model.id

    AuditLoggedModel.objects.filter(id=model_id).delete()

    assert AuditLog.objects.count() == 2

    log_entry = AuditLog.objects.order_by("-id").first()
    assert log_entry.action == "DELETE"
    assert log_entry.changes == {"id": model_id, "some_text": "Some text"}
    assert log_entry.audit_logged_model is None


@pytest.mark.usefixtures("db", "audit_logging_context")
def test_sql_delete_is_audit_logged() -> None:
    """
    Test that the audit logging context manager works and that we can delete
    data, and that the delete is audit logged.
    """

    AuditLog = AuditLoggedModel.AuditLog  # type: ignore

    model = AuditLoggedModel.objects.create(some_text="Some text")
    model_id = model.id

    with connection.cursor() as cursor:
        # Django doesn't do cascading FK constraints at the DB level, so we
        # have to manually update any audit log entries first
        cursor.execute(
            (
                f"UPDATE {AuditLog._meta.db_table} "
                "SET audit_logged_model_id=null "
                "WHERE audit_logged_model_id=%s"
            ),
            [model.id],
        )

        # Then delete the model we want to delete
        cursor.execute(
            f"DELETE FROM {AuditLoggedModel._meta.db_table} WHERE id=%s",
            [model.id],
        )

    AuditLoggedModel.objects.filter(id=model_id).delete()

    assert AuditLog.objects.count() == 2

    log_entry = AuditLog.objects.order_by("-id").first()
    assert log_entry.action == "DELETE"
    assert log_entry.changes == {"id": model_id, "some_text": "Some text"}
    assert log_entry.audit_logged_model is None
