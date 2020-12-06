"""
Various helpers.
"""

from functools import lru_cache
from textwrap import dedent
from typing import List, Sequence, Type

from django.apps import apps
from django.conf import settings
from django.db.backends.postgresql.base import (
    DatabaseWrapper as PostgreSQLDatabaseWrapper,
)
from django.db.models import AutoField, Field, ForeignKey, JSONField, Model

from . import fields


def _column_sql(field: Field) -> str:
    """
    Generate the SQL required to create the given field in a CREATE TABLE
    statement.
    """

    field_type = field.get_internal_type()
    data_types = PostgreSQLDatabaseWrapper.data_types
    data_type_check_constraints = PostgreSQLDatabaseWrapper.data_type_check_constraints

    if isinstance(field, JSONField):
        column_type = "jsonb"
    elif isinstance(field, ForeignKey):
        column_type = "integer"
    else:
        column_type = data_types[field_type]

    try:
        check_constraint = data_type_check_constraints[field_type]
        check_constraint = check_constraint % {"column": field.column}
    except KeyError:
        check_constraint = None

    # Interpolate any dynamic values (like max_length)
    column_type = column_type % field.__dict__

    # Add NOT NULL if null values are not allowed
    if not field.null:
        column_type += " NOT NULL"

    if field.choices:
        # Assume that if choices is set, it's a char field and that the choices
        # are a list of strings that are valid values.
        column_type += f' CHECK ("{field.column}" IN ('
        column_type += ", ".join([f"'{choice}'" for _, choice in field.choices])
        column_type += "))"
    elif check_constraint:
        # If the column had a check constrain defined, add that
        column_type += f" CHECK ({check_constraint})"

    return f"{field.column} {column_type}"


@lru_cache(maxsize=4)
def create_temporary_table_sql(model: Type[Model]) -> str:
    """
    Get the SQL required to represent the given model in the database as a
    temporary table.

    We cache the results as this will be called for each request, but the model
    should never change (outside of tests), so we can use a very small cache.
    """

    # Need to use _meta, so disable protected property access checks
    # pylint: disable=protected-access

    # For each field, generate the required SQL to add that field to the table
    definition = ", ".join(
        _column_sql(field)
        for field in model._meta.get_fields()  # noqa
        if isinstance(field, Field)
    )

    sql = f'CREATE TEMPORARY TABLE "{model._meta.db_table}" ({definition})'

    return sql


def drop_temporary_table_sql(model: Type[Model]) -> str:
    """
    Generate the SQL required to drop the temporary table for the given model.
    """

    # Need to use _meta, so disable protected property access checks
    # pylint: disable=protected-access

    return f"DROP TABLE {model._meta.db_table}"


def create_trigger_function_sql(
    *,
    audit_logged_model: Type[Model],
    context_model: Type[Model],
    log_entry_model: Type[Model],
) -> str:
    """
    Generate the SQL to create the function to log the SQL.
    """

    trigger_function_name = f"{ audit_logged_model._meta.db_table }_log_change"

    context_table_name = context_model._meta.db_table  # noqa
    context_fields = ", ".join(
        field.column
        for field in context_model._meta.get_fields()  # noqa
        if isinstance(field, Field) and not isinstance(field, AutoField)
    )

    log_entry_table_name = log_entry_model._meta.db_table

    return dedent(
        f"""
        CREATE FUNCTION { trigger_function_name }()
        RETURNS TRIGGER AS $$
        DECLARE
            -- Id of the inserted row, used to ensure exactly one row is inserted
            entry_id int;
            content_type_id int;
        BEGIN
            SELECT id INTO STRICT content_type_id
                FROM django_content_type WHERE
                app_label = '{ audit_logged_model._meta.app_label }'
                AND model = '{ audit_logged_model._meta.model_name }';

            IF (TG_OP = 'INSERT') THEN
                INSERT INTO { log_entry_table_name } (
                    { context_fields },
                    action,
                    at,
                    changes,
                    content_type_id,
                    object_id
                ) SELECT
                    { context_fields },
                    TG_OP as action,
                    now() as at,
                    to_jsonb(NEW.*) as changes,
                    content_type_id,
                    NEW.id as object_id
                -- We rely on this table being created by out Django middleware
                FROM { context_table_name }
                -- We return the id into the variable to make postgresql check
                -- that exactly one row is inserted.
                RETURNING id INTO STRICT entry_id;
                RETURN NEW;
            ELSIF (TG_OP = 'UPDATE') THEN
                INSERT INTO { log_entry_table_name } (
                    { context_fields },
                    action,
                    at,
                    changes,
                    content_type_id,
                    object_id
                ) SELECT
                    { context_fields },
                    TG_OP as action,
                    now() as at,
                    (
                        SELECT
                            -- Aggregate back to a single jsonb object, with
                            -- column name as key and the two values in an array.
                            jsonb_object_agg(
                                COALESCE(old_row.key, new_row.key),
                                ARRAY[old_row.value, new_row.value]
                            )
                        FROM
                            -- Select key value pairs from the old and the new
                            -- row, and then join them on the key. THis gives
                            -- us rows with the same key and values from both
                            -- the old row and the new row.
                            jsonb_each(to_jsonb(OLD.*)) old_row
                            FULL OUTER JOIN
                            jsonb_each(to_jsonb(NEW.*)) new_row
                            ON old_row.key = new_row.key
                        WHERE
                            -- Only select rows that have actually changed
                            old_row.* IS DISTINCT FROM new_row.*
                    ) as changes,
                    content_type_id,
                    NEW.id as object_id
                -- We rely on this table being created by out Django middleware
                FROM { context_table_name }
                -- We return the id into the variable to make postgresql check
                -- that exactly one row is inserted.
                RETURNING id INTO STRICT entry_id;
                RETURN NEW;
            ELSIF (TG_OP = 'DELETE') THEN
                INSERT INTO { log_entry_table_name } (
                    { context_fields },
                    action,
                    at,
                    changes,
                    content_type_id,
                    object_id
                ) SELECT
                    { context_fields },
                    TG_OP as action,
                    now() as at,
                    to_jsonb(OLD.*) as changes,
                    content_type_id,
                    OLD.id as object_id
                -- We rely on this table being created by out Django middleware
                FROM { context_table_name }
                -- We return the id into the variable to make postgresql check
                -- that exactly one row is inserted.
                RETURNING id INTO STRICT entry_id;
                RETURN NEW;
            END IF;
        END;
        $$ language 'plpgsql';
        """
    )


def drop_trigger_function_sql(
    *,
    audit_logged_model: Type[Model],
) -> str:
    """
    Create the SQL required to drop the trigger function for the given model
    """

    return f"DROP FUNCTION { audit_logged_model._meta.db_table }_log_change"


def create_triggers_sql(*, audit_logged_model: Type[Model]) -> Sequence[str]:
    """
    Create the SQL requried to set up triggers for audit logging to the given
    audit log entry model.
    """

    # Get the model that we are audit logging
    audit_logged_table = audit_logged_model._meta.db_table  # noqa
    trigger_function_name = f"{audit_logged_table}_log_change"

    insert_trigger = dedent(
        f"""
        CREATE TRIGGER log_insert
        AFTER INSERT ON { audit_logged_table }
        FOR EACH ROW
        EXECUTE FUNCTION { trigger_function_name }()
        """
    )

    update_trigger = dedent(
        f"""
        CREATE TRIGGER log_update
        AFTER UPDATE ON { audit_logged_table }
        FOR EACH ROW
        WHEN (OLD.* IS DISTINCT FROM NEW.*)
        EXECUTE FUNCTION { trigger_function_name }()
        """
    )

    delete_trigger = dedent(
        f"""
        CREATE TRIGGER log_delete
        AFTER DELETE ON { audit_logged_table }
        FOR EACH ROW
        EXECUTE FUNCTION { trigger_function_name }()
        """
    )

    return (insert_trigger, update_trigger, delete_trigger)


def drop_triggers_sql(*, audit_logged_model: Type[Model]) -> Sequence[str]:
    """
    Generate the SQL required to remove the audit logging triggers for the
    given audit log entry model.
    """

    # Need to use _meta, so disable protected property access checks
    # pylint: disable=protected-access

    # Get the model that we are audit logging
    audit_logged_table = audit_logged_model._meta.db_table  # noqa

    return (
        f"DROP TRIGGER log_insert ON { audit_logged_table }",
        f"DROP TRIGGER log_update ON { audit_logged_table }",
        f"DROP TRIGGER log_delete ON { audit_logged_table }",
    )


def create_content_type_sql(*, audit_logged_model: Type[Model]) -> str:
    """
    Generate the SQL required to ensure the ContentType object exists for the
    given model. We eagerly create this as it's used by the trigger and we don't
    want to create it on demand there, which is what Django usually does.
    """

    app_label = audit_logged_model._meta.app_label
    model_name = audit_logged_model._meta.model_name

    return dedent(
        f"""
        INSERT INTO django_content_type (app_label, model)
        VALUES ('{app_label}', '{model_name}')
        ON CONFLICT (app_label, model) DO NOTHING
        """
    )


def is_audit_logs_field(field: Field) -> bool:
    """
    Check if a given field is an AuditLogsField
    """

    return isinstance(field, fields.AuditLogsField)


def has_audit_logs_field(model: Type[Model]) -> bool:
    """
    Check if any of the model's fields is an AuditLogsField
    """

    return any(is_audit_logs_field(field) for field in model._meta.local_fields)


def get_context_model(_apps=None) -> Type[Model]:
    app_label, model_name = settings.AUDIT_LOG_CONTEXT_MODEL.rsplit(".", 1)
    return (_apps or apps).get_model(app_label, model_name)


def get_log_entry_model(_apps=None) -> Type[Model]:
    app_label, model_name = settings.AUDIT_LOG_ENTRY_MODEL.rsplit(".", 1)
    return (_apps or apps).get_model(app_label, model_name)


def add_audit_logging_sql(
    *,
    audit_logged_model: Type[Model],
    context_model: Type[Model],
    log_entry_model: Type[Model],
) -> List[str]:

    sql = []

    sql.append(
        create_trigger_function_sql(
            audit_logged_model=audit_logged_model,
            context_model=context_model,
            log_entry_model=log_entry_model,
        )
    )
    sql.extend(create_triggers_sql(audit_logged_model=audit_logged_model))

    # Make sure the ContentType object exists for the model, as we need that
    # for the trigger.
    sql.append(create_content_type_sql(audit_logged_model=audit_logged_model))

    return sql


def remove_audit_logging_sql(*, audit_logged_model: Type[Model]) -> List[str]:

    sql: List[str] = []
    sql.extend(drop_triggers_sql(audit_logged_model=audit_logged_model))
    sql.append(drop_trigger_function_sql(audit_logged_model=audit_logged_model))
    return sql
