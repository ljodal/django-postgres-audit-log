from django.db import models
from django.db.models.options import Options
from typing_extensions import Protocol


class AuditLogEntryModel(Protocol):
    @classmethod
    def get_trigger_name(cls) -> str:
        ...

    @classmethod
    def get_audit_logged_model(cls) -> models.Model:
        ...

    @classmethod
    def get_fk_column(cls) -> str:
        ...

    _meta: Options
