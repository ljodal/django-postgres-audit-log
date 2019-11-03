from typing import Any, Dict, List, Optional, Tuple, Type, Union

from django.conf import settings
from django.db import models
from django.db.migrations.operations import CreateModel
from django.utils.module_loading import import_string

from ...schema import SchemaEditor


class CreateAuditLogModel(CreateModel):
    def __init__(
        self,
        name: str,
        fields: List[Tuple[str, models.Field]],
        *,
        options: Optional[Dict[str, Any]] = None,
        bases: Optional[List[Union[str, Type[models.Model]]]] = None,
        managers: Optional[List[Tuple[str, models.Manager]]] = None,
        audit_log_for: str,
    ) -> None:
        super().__init__(name, fields, options=options, bases=bases, managers=managers)

        self.audit_log_for = audit_log_for

    def database_forwards(
        self,
        app_label: str,
        schema_editor: SchemaEditor,
        from_state: Any,
        to_state: Any,
    ) -> None:
        super().database_forwards(app_label, schema_editor, from_state, to_state)

        schema_editor.create_audit_logging_triggers(
            audit_log_model=to_state.apps.get_model(app_label, self.name),
            audit_logged_model=to_state.apps.get_model(
                *self.audit_log_for.rsplit(".", 1)
            ),
        )

    def database_backwards(
        self,
        app_label: str,
        schema_editor: SchemaEditor,
        from_state: Any,
        to_state: Any,
    ) -> None:

        schema_editor.drop_audit_logging_triggers(
            audit_log_model=from_state.apps.get_model(app_label, self.name),
            audit_logged_model=from_state.apps.get_model(
                *self.audit_log_for.rsplit(".", 1)
            ),
        )

        super().database_backwards(app_label, schema_editor, from_state, to_state)
