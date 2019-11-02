from typing import Type

import pytest  # type: ignore
from django.contrib.auth.models import User
from django.test import Client

from ..models import AuditLoggedModel


@pytest.mark.usefixtures("db")  # type: ignore
def test_view(django_user_model: Type[User], client: Client) -> None:
    user = django_user_model.objects.create(username="test", password="test")
    user.set_password("test")
    user.save(update_fields=["password"])
    assert client.login(username="test", password="test")

    response = client.post("/my-url/", data={"value": "bla"})
    assert response.status_code == 200

    data = response.json()

    assert "id" in data
    assert isinstance(data["id"], int)

    # Make sure the model was created as we expected
    model = AuditLoggedModel.objects.get(id=data["id"])
    assert model.some_text == "bla"

    # Make sure it was audit logged
    assert model.audit_logs.count() == 1  # type: ignore

    audit_log = model.audit_logs.get()  # type: ignore
    assert audit_log.action == "INSERT"
    assert audit_log.context_type == "http_request"
    assert audit_log.performed_by == user
