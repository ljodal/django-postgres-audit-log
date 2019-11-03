"""
Various helpers.
"""

import re
from functools import lru_cache
from typing import TYPE_CHECKING, Sequence, Type

from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.db import models
from django.db.backends.postgresql.base import (
    DatabaseWrapper as PostgreSQLDatabaseWrapper,
)
from django.utils.module_loading import import_string

if TYPE_CHECKING:
    from .models import AuditLogEntry  # noqa


def _column_sql(field: models.Field) -> str:
    """
    Generate the SQL required to create the given field in a CREATE TABLE
    statement.
    """

    field_type = field.get_internal_type()
    data_types = PostgreSQLDatabaseWrapper.data_types
    data_type_check_constraints = PostgreSQLDatabaseWrapper.data_type_check_constraints

    if isinstance(field, JSONField):
        column_type = "jsonb"
    elif isinstance(field, models.ForeignKey):
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
def create_temporary_table_sql(model: Type[models.Model]) -> str:
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
        if isinstance(field, models.Field)
    )

    sql = f'CREATE TEMPORARY TABLE "{model._meta.db_table}" ({definition})'

    return sql


@lru_cache(maxsize=4)
def drop_temporary_table_sql(model: Type[models.Model]) -> str:
    """
    Generate the SQL required to drop the temporary table for the given model.
    """

    # Need to use _meta, so disable protected property access checks
    # pylint: disable=protected-access

    return f"DROP TABLE {model._meta.db_table}"


def create_audit_log_model(*, for_model: Type[models.Model]) -> Type["AuditLogEntry"]:
    """
    Dynamically create a new Django model for the given model
    """

    # Need to use _meta, so disable protected property access checks
    # pylint: disable=protected-access

    class_name = f"{for_model.__name__}AuditLog"
    foreign_key: models.ForeignKey = models.ForeignKey(
        for_model, related_name="audit_logs", null=True, on_delete=models.SET_NULL
    )

    # Convert class name from CamelCase to snake_case, regex taken from
    # https://stackoverflow.com/a/12867228/1522350
    field_name = re.sub(
        r"((?<=[a-z0-9])[A-Z]|(?!^)[A-Z](?=[a-z]))", r"_\1", for_model.__name__
    ).lower()

    # Method to get the
    get_audit_logged_model = classmethod(lambda cls: for_model)

    _log_entry_base_class = import_string(settings.AUDIT_LOGGING_LOG_ENTRY_CLASS)

    return type(
        class_name,
        (_log_entry_base_class,),
        {
            "__module__": for_model.__module__,
            field_name: foreign_key,
            "get_audit_logged_model": get_audit_logged_model,
        },
    )


def create_trigger_function_sql(
    *,
    audit_log_model: Type[models.Model],
    audit_logged_model: Type[models.Model],
    context_model: Type[models.Model],
) -> str:
    """
    Generate the SQL to create the function to log the SQL.
    """

    # Need to use _meta, so disable protected property access checks
    # pylint: disable=protected-access

    # Convert class name from CamelCase to snake_case, regex taken from
    # https://stackoverflow.com/a/12867228/1522350
    field_name = re.sub(
        r"((?<=[a-z0-9])[A-Z]|(?!^)[A-Z](?=[a-z]))", r"_\1", audit_logged_model.__name__
    ).lower()
    foreign_key_column_name = audit_log_model._meta.get_field(field_name).column

    trigger_function_name = f"{ audit_logged_model._meta.db_table }_log_change"

    audit_log_table_name = audit_log_model._meta.db_table  # noqa
    context_table_name = context_model._meta.db_table  # noqa
    context_fields = ", ".join(
        field.column
        for field in context_model._meta.get_fields()  # noqa
        if isinstance(field, models.Field) and not isinstance(field, models.AutoField)
    )

    return f"""
        CREATE FUNCTION { trigger_function_name }()
        RETURNS TRIGGER AS $$
        DECLARE
            -- Id of the inserted row, used to ensure exactly one row is inserted
            entry_id int;
        BEGIN
            IF (TG_OP = 'INSERT') THEN
                INSERT INTO { audit_log_table_name } (
                    { context_fields },
                    action,
                    at,
                    changes,
                    { foreign_key_column_name }
                ) SELECT
                    { context_fields },
                    TG_OP as action,
                    now() as at,
                    to_jsonb(NEW.*) as changes,
                    NEW.id as { foreign_key_column_name }
                -- We rely on this table being created by out Django middleware
                FROM { context_table_name }
                -- We return the id into the variable to make postgresql check
                -- that exactly one row is inserted.
                RETURNING id INTO STRICT entry_id;
                RETURN NEW;
            ELSIF (TG_OP = 'UPDATE') THEN
                INSERT INTO { audit_log_table_name } (
                    { context_fields },
                    action,
                    at,
                    changes,
                    { foreign_key_column_name }
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
                    NEW.id as { foreign_key_column_name }
                -- We rely on this table being created by out Django middleware
                FROM { context_table_name }
                -- We return the id into the variable to make postgresql check
                -- that exactly one row is inserted.
                RETURNING id INTO STRICT entry_id;
                RETURN NEW;
            ELSIF (TG_OP = 'DELETE') THEN
                INSERT INTO { audit_log_table_name } (
                    { context_fields },
                    action,
                    at,
                    changes,
                    { foreign_key_column_name }
                ) SELECT
                    { context_fields },
                    TG_OP as action,
                    now() as at,
                    to_jsonb(OLD.*) as changes,
                    null as { foreign_key_column_name }
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


def drop_trigger_function_sql(*, audit_logged_model: Type[models.Model],) -> str:
    """
    Create the SQL required to drop the trigger function for the given model
    """

    return f"DROP FUNCTION { audit_logged_model._meta.db_table }_log_change"


def create_triggers_sql(*, audit_logged_model: Type[models.Model]) -> Sequence[str]:
    """
    Create the SQL requried to set up triggers for audit logging to the given
    audit log entry model.
    """

    # Need to use _meta, so disable protected property access checks
    # pylint: disable=protected-access

    # Get the model that we are audit logging
    audit_logged_table = audit_logged_model._meta.db_table  # noqa
    trigger_function_name = f"{audit_logged_table}_log_change"

    insert_trigger = f"""
    CREATE TRIGGER log_insert
        AFTER INSERT ON { audit_logged_table }
        FOR EACH ROW
        EXECUTE FUNCTION { trigger_function_name }()
    """

    update_trigger = f"""
    CREATE TRIGGER log_update
        AFTER UPDATE ON { audit_logged_table }
        FOR EACH ROW
        WHEN (OLD.* IS DISTINCT FROM NEW.*)
        EXECUTE FUNCTION { trigger_function_name }()
    """

    delete_trigger = f"""
    CREATE TRIGGER log_delete
        AFTER DELETE ON { audit_logged_table }
        FOR EACH ROW
        EXECUTE FUNCTION { trigger_function_name }()
    """

    return (insert_trigger, update_trigger, delete_trigger)


def drop_triggers_sql(*, audit_logged_model: Type[models.Model]) -> Sequence[str]:
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
