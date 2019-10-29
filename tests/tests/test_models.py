from audit_log.models import AuditLogEntry

from ..models import AuditLoggedModel, NonAuditLoggedModel


def test_has_audit_log_defined():

    assert hasattr(AuditLoggedModel, "AuditLog")
    assert issubclass(AuditLoggedModel.AuditLog, AuditLogEntry)


def test_can_query_audit_log_table(db):

    assert AuditLoggedModel.AuditLog.objects.count() == 0
