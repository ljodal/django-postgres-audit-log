import pytest
from django.core import management

from ..models import MyAuditLoggedModel


@pytest.mark.usefixtures("db")
def test_management_command() -> None:
    """
    Test that calling a managment command works with audit logging.
    """

    assert MyAuditLoggedModel.objects.count() == 0

    management.call_command("some_command", "--verbosity=1")

    assert MyAuditLoggedModel.objects.count() == 1
    model = MyAuditLoggedModel.objects.get()

    assert model.audit_logs.count() == 1  # type: ignore
    audit_log = model.audit_logs.get()  # type: ignore

    assert audit_log.context_type == "management-command"
    assert audit_log.context == {
        "command": "some_command",
        "args": [],
        "kwargs": {
            "force_color": False,
            "no_color": False,
            "pythonpath": None,
            "settings": None,
            "traceback": False,
            "verbosity": 1,
            "skip_checks": True,
        },
    }
