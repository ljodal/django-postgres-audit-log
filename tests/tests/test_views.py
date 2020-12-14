from typing import Type

import pytest
from django.contrib.auth.models import User  # pylint: disable=imported-auth-user
from django.test import Client

from ..models import MyAuditLoggedModel


@pytest.mark.usefixtures("db")
def test_view(django_user_model: Type[User], client: Client) -> None:
    """
    Test that audit logging a full http request works as expected.
    """

    user = django_user_model.objects.create(username="test", password="test")
    user.set_password("test")
    user.save(update_fields=["password"])
    assert client.login(username="test", password="test")

    response = client.post("/my-url/?a=1&a=2&b=3", data={"value": "bla"})
    assert response.status_code == 200

    data = response.json()

    assert "id" in data
    assert isinstance(data["id"], int)

    # Make sure the model was created as we expected
    model = MyAuditLoggedModel.objects.get(id=data["id"])
    assert model.some_text == "bla"

    # Make sure it was audit logged
    assert model.audit_logs.count() == 1

    audit_log = model.audit_logs.get()
    assert audit_log.action == "INSERT"
    assert audit_log.context_type == "http-request"
    assert audit_log.context == {
        "method": "POST",
        "query_params": {"a": ["1", "2"], "b": ["3"]},
        "path": "/my-url/",
    }
    assert audit_log.performed_by == user
