import functools

from django.db import models

from .utils import create_audit_log_model


def audit_logged():
    """
    Decorator for adding audit logging to a Django model.
    """

    def wrapper(cls):

        # Make sure that the class being decorated is a Django model
        assert issubclass(cls, models.Model)

        # Magically define an audit log model for the class
        cls.AuditLog = create_audit_log_model(for_model=cls)

        # Return the class, completely unharmed ;)
        return cls

    return wrapper
