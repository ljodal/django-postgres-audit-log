from typing import TYPE_CHECKING, Callable, cast

from django.apps import apps
from django.conf import settings
from django.http import HttpRequest, HttpResponse

from .context_managers import audit_logging
from .utils import create_temporary_table_sql, drop_temporary_table_sql

if TYPE_CHECKING:
    from .models import AuditLoggingBaseContext  # noqa pylint: disable=cyclic-import


class AuditLoggingMiddleware:
    """
    A middleware that creates a temporary table and inserts context for the
    current request into that table.
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

        # Dynamically get the context model from settings
        app_label, model_name = settings.AUDIT_LOGGING_CONTEXT_MODEL.rsplit(".", 1)
        self.context_model = apps.get_model(app_label=app_label, model_name=model_name)

        # Generate the SQL required to create the temporary context table once,
        # this is faster than doing it for every request and the model
        # shouldn't change anyway.
        self.create_temporary_table_sql = create_temporary_table_sql(self.context_model)
        self.drop_temporary_table_sql = drop_temporary_table_sql(self.context_model)

    def __call__(self, request: HttpRequest) -> HttpResponse:

        with audit_logging(
            create_temporary_table_sql=self.create_temporary_table_sql,
            drop_temporary_table_sql=self.drop_temporary_table_sql,
            create_context=lambda: self.create_context(request),
        ):
            return self.get_response(request)

    def create_context(self, request: HttpRequest) -> "AuditLoggingBaseContext":
        """
        Create context from the given request
        """

        return cast(
            "AuditLoggingBaseContext",
            self.context_model.objects.create_from_request(request),
        )
