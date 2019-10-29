from typing import Callable

from django.apps import apps
from django.conf import settings
from django.db import connection, models
from django.http import HttpRequest, HttpResponse

from .utils import create_temporary_table_sql, drop_temporary_table_sql


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

        # Create the temporary table and initialize it with the request context
        sql, params = self.create_temporary_table_sql
        with connection.cursor() as cursor:
            cursor.execute(sql, params or None)

            self.context_model.objects.create(
                context_type="http_request",
                context={},
                user_id=getattr(request.user, "id", None),
            )

        try:
            return self.get_response(request)
        finally:
            # Remove the temporary table after the request has been handled
            sql, params = self.drop_temporary_table_sql
            with connection.cursor() as cursor:
                cursor.execute(sql, params or None)
