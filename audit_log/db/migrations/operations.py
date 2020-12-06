from django.db.backends.base.schema import BaseDatabaseSchemaEditor
from django.db.migrations.operations.base import Operation
from django.db.migrations.state import ProjectState

from ... import utils


class AddAuditLogging(Operation):
    """
    Add audit logging triggers to the specified model.
    """

    def __init__(self, *, model: str) -> None:
        self.model = model

    def state_forwards(self, app_label: str, state: ProjectState) -> None:
        pass

    def database_forwards(
        self,
        app_label: str,
        schema_editor: BaseDatabaseSchemaEditor,
        from_state: ProjectState,
        to_state: ProjectState,
    ) -> None:
        model = to_state.apps.get_model(app_label, self.model)

        sql = utils.add_audit_logging_sql(
            audit_logged_model=model,
            context_model=utils.get_context_model(to_state.apps),
            log_entry_model=utils.get_log_entry_model(to_state.apps),
        )

        for query in sql:
            schema_editor.execute(query)

    def database_backwards(
        self,
        app_label: str,
        schema_editor: BaseDatabaseSchemaEditor,
        from_state: ProjectState,
        to_state: ProjectState,
    ) -> None:
        model = from_state.apps.get_model(app_label, self.model)
        sql = utils.remove_audit_logging_sql(audit_logged_model=model)

        for query in sql:
            schema_editor.execute(query)

    def describe(self) -> str:
        return f"Add audit logging to {self.model}"


class RemoveAuditLogging(Operation):
    """
    Remove audit logging triggers from the specified model.
    """

    def __init__(self, *, model: str) -> None:
        self.model = model

    def state_forwards(self, app_label: str, state: ProjectState) -> None:
        pass

    def database_forwards(
        self,
        app_label: str,
        schema_editor: BaseDatabaseSchemaEditor,
        from_state: ProjectState,
        to_state: ProjectState,
    ) -> None:
        model = to_state.apps.get_model(app_label, self.model)
        sql = utils.remove_audit_logging_sql(audit_logged_model=model)

        for query in sql:
            schema_editor.execute(query)

    def database_backwards(
        self,
        app_label: str,
        schema_editor: BaseDatabaseSchemaEditor,
        from_state: ProjectState,
        to_state: ProjectState,
    ) -> None:
        model = from_state.apps.get_model(app_label, self.model)

        sql = utils.add_audit_logging_sql(
            audit_logged_model=model,
            context_model=utils.get_context_model(from_state.apps),
            log_entry_model=utils.get_log_entry_model(from_state.apps),
        )

        for query in sql:
            schema_editor.execute(query)

    def describe(self) -> str:
        return f"Remove audit logging from {self.model}"
