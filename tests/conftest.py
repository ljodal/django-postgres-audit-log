from typing import Any

import pytest


@pytest.fixture
def require_migrations(request: Any, django_db_use_migrations: bool) -> None:
    """
    Skip tests that we know will fail when migrations are not applied.
    """

    if not django_db_use_migrations:
        pytest.skip("This test requires migrations to run")
