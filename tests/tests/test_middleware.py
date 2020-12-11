from unittest import mock

import pytest
from django.http import QueryDict

from audit_log.middleware import AuditLoggingMiddleware


@pytest.mark.usefixtures("db")
def test_middleware() -> None:
    """
    Test that the middleware is callable with a mock request.
    """

    # Initialize the middleware
    middleware = AuditLoggingMiddleware(mock.Mock())

    request = mock.Mock()
    request.user.id = 1
    request.method = "GET"
    request.path = "/some/path"
    request.GET = QueryDict("a=1&b=2")

    middleware(request)
