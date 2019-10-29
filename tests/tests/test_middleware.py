from unittest import mock

import pytest

from audit_log.middleware import AuditLoggingMiddleware

pytestmark = pytest.mark.django_db


def test_middleware():

    # Initialize the middleware
    middleware = AuditLoggingMiddleware(mock.Mock())

    request = mock.Mock()
    request.user.id = 1

    middleware(request)
