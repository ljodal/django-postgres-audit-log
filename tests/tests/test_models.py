from typing import Callable

import pytest
from django.db import connection

from ..models import (
    AuditLogEntry,
    MyAuditLoggedModel,
    MyConvertedToAuditLoggedModel,
    MyManuallyAuditLoggedModel,
    MyNoLongerAuditLoggedModel,
    MyNoLongerManuallyAuditLoggedModel,
)


@pytest.mark.usefixtures("db", "audit_logging_context")
def test_insert_is_audit_logged() -> None:
    """
    Test that the audit logging context manager works and that we can insert
    data, and that the insert is audit logged.
    """

    model = MyAuditLoggedModel.objects.create(some_text="Some text")

    assert model.audit_logs.count() == 1

    log_entry = model.audit_logs.get()
    assert log_entry.changes == {"id": model.id, "some_text": "Some text"}
    assert log_entry.log_object == model


@pytest.mark.usefixtures("db", "audit_logging_context")
def test_insert_is_audit_logged_on_converted_model() -> None:
    """
    Test that the audit logging context manager works and that we can insert
    data, and that the insert is audit logged.
    """

    model = MyConvertedToAuditLoggedModel.objects.create(some_text="Some text")

    assert model.audit_logs.count() == 1

    log_entry = model.audit_logs.get()
    assert log_entry.changes == {"id": model.id, "some_text": "Some text"}
    assert log_entry.log_object == model


@pytest.mark.usefixtures("db", "audit_logging_context")
def test_insert_is_not_audit_logged_on_removed_model() -> None:
    """
    Test that the audit logging context manager works and that we can insert
    data, and that the insert is audit logged.
    """

    assert AuditLogEntry.objects.count() == 0

    MyNoLongerAuditLoggedModel.objects.create(some_text="Some text")

    assert AuditLogEntry.objects.count() == 0


@pytest.mark.usefixtures("db", "audit_logging_context")
def test_insert_is_audit_logged_on_manual_model() -> None:
    """
    Test that the audit logging context manager works and that we can insert
    data, and that the insert is audit logged.
    """

    assert AuditLogEntry.objects.count() == 0

    MyManuallyAuditLoggedModel.objects.create(some_text="Some text")

    assert AuditLogEntry.objects.count() == 1


@pytest.mark.usefixtures("db", "audit_logging_context")
def test_insert_is_not_audit_logged_on_removed_manual_model() -> None:
    """
    Test that the audit logging context manager works and that we can insert
    data, and that the insert is audit logged.
    """

    assert AuditLogEntry.objects.count() == 0

    MyNoLongerManuallyAuditLoggedModel.objects.create(some_text="Some text")

    assert AuditLogEntry.objects.count() == 0


@pytest.mark.usefixtures("db", "audit_logging_context")
def test_single_model_update_is_audit_logged() -> None:
    """
    Test that the audit logging context manager works and that we can update
    data, and that the update is audit logged.
    """

    model = MyAuditLoggedModel.objects.create(some_text="Some text")

    model.some_text = "Updated text"
    model.save(update_fields=["some_text"])

    assert model.audit_logs.count() == 2

    log_entry = model.audit_logs.latest("id")
    assert log_entry.action == "UPDATE"
    assert log_entry.changes == {"some_text": ["Some text", "Updated text"]}
    assert log_entry.log_object == model


@pytest.mark.usefixtures("db", "audit_logging_context")
def test_bulk_update_is_audit_logged() -> None:
    """
    Test that the audit logging context manager works and that we can update
    data, and that the update is audit logged.
    """

    model = MyAuditLoggedModel.objects.create(some_text="Some text")

    MyAuditLoggedModel.objects.filter(id=model.id).update(some_text="Updated text")

    assert model.audit_logs.count() == 2

    log_entry = model.audit_logs.latest("id")
    assert log_entry.action == "UPDATE"
    assert log_entry.changes == {"some_text": ["Some text", "Updated text"]}
    assert log_entry.log_object == model


@pytest.mark.usefixtures("db", "audit_logging_context")
def test_sql_update_is_audit_logged() -> None:
    """
    Test that the audit logging context manager works and that we can update
    data, and that the update is audit logged.
    """

    model = MyAuditLoggedModel.objects.create(some_text="Some text")

    with connection.cursor() as cursor:
        cursor.execute(
            f"UPDATE {MyAuditLoggedModel._meta.db_table} SET some_text=%s WHERE id=%s",
            ["Updated text", model.id],
        )

    assert model.audit_logs.count() == 2

    log_entry = model.audit_logs.latest("id")
    assert log_entry.action == "UPDATE"
    assert log_entry.changes == {"some_text": ["Some text", "Updated text"]}
    assert log_entry.log_object == model


@pytest.mark.usefixtures("db", "audit_logging_context")
def test_delete_is_audit_logged() -> None:
    """
    Test that the audit logging context manager works and that we can delete
    data, and that the delete is audit logged.
    """

    assert AuditLogEntry.objects.count() == 0

    model = MyAuditLoggedModel.objects.create(some_text="Some text")
    model_id = model.id

    assert model.audit_logs.count() == 1

    model.delete()

    assert AuditLogEntry.objects.count() == 2

    log_entry = AuditLogEntry.objects.latest("id")
    assert log_entry.action == "DELETE"
    assert log_entry.changes == {"id": model_id, "some_text": "Some text"}
    assert log_entry.log_object is None


@pytest.mark.usefixtures("db", "audit_logging_context")
def test_bulk_delete_is_audit_logged() -> None:
    """
    Test that the audit logging context manager works and that we can delete
    data, and that the delete is audit logged.
    """

    model = MyAuditLoggedModel.objects.create(some_text="Some text")
    model_id = model.id

    MyAuditLoggedModel.objects.filter(id=model_id).delete()

    assert model.audit_logs.count() == 2

    log_entry = model.audit_logs.latest("id")
    assert log_entry.action == "DELETE"
    assert log_entry.changes == {"id": model_id, "some_text": "Some text"}
    assert log_entry.log_object is None


@pytest.mark.usefixtures("db", "audit_logging_context")
def test_sql_delete_is_audit_logged() -> None:
    """
    Test that the audit logging context manager works and that we can delete
    data, and that the delete is audit logged.
    """

    model = MyAuditLoggedModel.objects.create(some_text="Some text")
    model_id = model.id

    with connection.cursor() as cursor:
        cursor.execute(
            f"DELETE FROM {MyAuditLoggedModel._meta.db_table} WHERE id=%s",
            [model.id],
        )

    MyAuditLoggedModel.objects.filter(id=model_id).delete()

    assert model.audit_logs.count() == 2

    log_entry = model.audit_logs.latest("id")
    assert log_entry.action == "DELETE"
    assert log_entry.changes == {"id": model_id, "some_text": "Some text"}
    assert log_entry.log_object is None


@pytest.mark.usefixtures("db", "audit_logging_context")
def test_prefetch_audit_logged_object(django_assert_num_queries: Callable) -> None:
    """
    Test that the audit logging context manager works and that we can insert
    data, and that the insert is audit logged.
    """

    first_model = MyAuditLoggedModel.objects.create(some_text="Some text")
    second_model = MyAuditLoggedModel.objects.create(some_text="Some other text")

    audit_logs = AuditLogEntry.objects.order_by("id")

    # Test without prefetch, should generate 3 queries
    with django_assert_num_queries(3):
        assert len(audit_logs) == 2

        first, second = audit_logs
        assert first.log_object == first_model
        assert second.log_object == second_model

    # Update queryset to include prefetch
    audit_logs = audit_logs.prefetch_related("log_object")

    with django_assert_num_queries(2):
        assert len(audit_logs) == 2

        first, second = audit_logs
        assert first.log_object == first_model
        assert second.log_object == second_model


@pytest.mark.usefixtures("db", "audit_logging_context")
def test_prefetch_log_entries(django_assert_num_queries: Callable) -> None:
    """
    Test that the audit logging context manager works and that we can insert
    data, and that the insert is audit logged.
    """

    # Create two objects and then update both, generating 4 log entries
    MyAuditLoggedModel.objects.create(some_text="Some text")
    MyAuditLoggedModel.objects.create(some_text="Some text")
    MyAuditLoggedModel.objects.update(some_text="Some other text")

    assert AuditLogEntry.objects.count() == 4

    models = MyAuditLoggedModel.objects.order_by("id")

    # Test without prefetch, should generate 3 queries
    with django_assert_num_queries(3):
        for model in models:
            audit_logs = model.audit_logs.all()
            assert len(audit_logs) == 2

    # Update queryset to include prefetch
    audit_logs = models.prefetch_related("audit_logs")

    with django_assert_num_queries(2):
        for model in models:
            audit_logs = model.audit_logs.all()
            assert len(audit_logs) == 2
