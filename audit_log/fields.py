from typing import Any, Dict, List, Optional, Tuple, Type

from django.conf import settings
from django.contrib.contenttypes.fields import (
    GenericRelation,
    ReverseGenericManyToOneDescriptor,
)
from django.db import DEFAULT_DB_ALIAS, models
from django.db.models.fields.related import lazy_related_operation  # type: ignore


class AuditLogsField(GenericRelation):
    """
    This field can be added to a model to allow easy access to audit log entries
    for that object (and also allow prefetching etc). This field is also used as
    a marker in the custom database engine to detect models we should add the
    audit logging trigger to.
    """

    model: Type[models.Model]
    attname: str
    opts: Any

    concrete = False
    hidden = True

    def __init__(self, to: str = settings.AUDIT_LOG_ENTRY_MODEL):
        super().__init__(to=to)

    def contribute_to_class(
        self, cls: Type[models.Model], name: str, private_only: bool = False
    ) -> None:

        # pylint: disable=arguments-differ,unused-argument

        self.name = name
        self.attname = name
        self.model = cls
        cls._meta.add_field(self, private=False)
        setattr(
            cls,
            self.name,
            ReverseGenericManyToOneDescriptor(self.remote_field),  # type: ignore
        )

        self.opts = cls._meta
        if not cls._meta.abstract:

            def resolve_related_class(model, related, field):  # type: ignore
                field.remote_field.model = related
                field.do_related_class(related, model)

            lazy_related_operation(
                resolve_related_class, cls, self.remote_field.model, field=self
            )

    def deconstruct(self) -> Tuple[Optional[str], str, List[Any], Dict[str, Any]]:

        # pylint: disable=invalid-name

        if isinstance(self.remote_field.model, str):
            to = self.remote_field.model.lower()
        else:
            to = self.remote_field.model._meta.label_lower

        return (
            self.name,
            f"{self.__class__.__module__}.{self.__class__.__qualname__}",
            [],
            {"to": to},
        )

    def bulk_related_objects(
        self, objs: List[models.Model], using: str = DEFAULT_DB_ALIAS
    ) -> models.QuerySet:
        """
        This method is only used by Django to detect related objects to delete
        when one of more objects are deleted. Since we never want an audit log
        entry to be deleted we override this to return an empty queryset.
        """

        # pylint: disable=protected-access

        return self.remote_field.model._base_manager.none()  # type: ignore
