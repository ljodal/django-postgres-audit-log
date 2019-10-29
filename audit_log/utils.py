"""
Various helpers.
"""

import re
from functools import lru_cache
from typing import Any, List, Tuple, Type

from django.contrib.postgres.fields import JSONField
from django.db import models
from django.db.backends.postgresql.base import (
    DatabaseWrapper as PostgreSQLDatabaseWrapper,
)

from .models import AuditLogEntry


def _column_sql(field: models.Field) -> Tuple[str, List[Any]]:
    """
    Generate the SQL required to create the given field in a CREATE TABLE
    statement.
    """

    field_type = field.get_internal_type()
    data_types = PostgreSQLDatabaseWrapper.data_types
    data_type_check_constraints = PostgreSQLDatabaseWrapper.data_type_check_constraints

    if isinstance(field, JSONField):
        column_type = "jsonb"
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

    return f"{field.column} {column_type}", []


@lru_cache(maxsize=4)
def create_temporary_table_sql(model: models.Model) -> Tuple[str, List[Any]]:
    """
    Get the SQL required to represent the given model in the database as a
    temporary table.

    We cache the results as this will be called for each request, but the model
    should never change (outside of tests), so we can use a very small cache.
    """

    # Need to use _meta, so disable protected property access checks
    # pylint: disable=protected-access

    columns = []
    params = []

    # For each field, generate the required SQL to add that field to the table
    for field in model._meta.get_fields():

        column_definition, column_params = _column_sql(field)
        columns.append(column_definition)
        params.extend(column_params)

    definition = ", ".join(columns)

    sql = f'CREATE TEMPORARY TABLE "{model._meta.db_table}" ({definition})'

    return sql, params


def drop_temporary_table_sql(model: models.Model) -> Tuple[str, List[Any]]:
    """
    Generate the SQL required to drop the temporary table for the given model.
    """

    # Need to use _meta, so disable protected property access checks
    # pylint: disable=protected-access

    return f"DROP TABLE {model._meta.db_table}", []


def create_audit_log_model(*, for_model: Type[models.Model]) -> Type[models.Model]:
    """
    Dynamically create a new Django model for the given model
    """

    class_name = f"{for_model.__name__}AuditLog"
    foreign_key = models.ForeignKey(
        for_model, related_name="audit_logs", on_delete=models.PROTECT
    )

    # Convert class name from CamelCase to snake_case, regex taken from
    # https://stackoverflow.com/a/12867228/1522350
    field_name = re.sub(
        r"((?<=[a-z0-9])[A-Z]|(?!^)[A-Z](?=[a-z]))", r"_\1", for_model.__name__
    )

    return type(
        class_name,
        (AuditLogEntry,),  # TODO: Dynamically get class
        {"__module__": for_model.__module__, field_name: foreign_key},
    )
