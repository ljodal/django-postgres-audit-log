from unittest import mock

import pytest  # type: ignore

from audit_log.middleware import AuditLoggingMiddleware


@pytest.mark.usefixtures("db")  # type: ignore
def test_middleware() -> None:

    # Initialize the middleware
    middleware = AuditLoggingMiddleware(mock.Mock())

    request = mock.Mock()
    request.user.id = 1

    middleware(request)
