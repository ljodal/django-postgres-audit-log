from typing import Callable, Type, TypeVar

from django.db import models

from . import utils

DjangoModel = TypeVar("DjangoModel", bound=Type[models.Model])


def audit_logged() -> Callable[[DjangoModel], DjangoModel]:
    """
    Decorator for adding audit logging to a Django model.
    """

    def wrapper(cls: DjangoModel) -> DjangoModel:

        # Magically define an audit log model for the class
        cls.AuditLog = utils.create_audit_log_model(for_model=cls)  # type: ignore

        # Return the class, completely unharmed ;)
        return cls

    return wrapper
