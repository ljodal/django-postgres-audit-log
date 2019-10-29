from django.core.management.base import BaseCommand

from ..services import configure_audit_log_context


class AuditLoggedCommand(BaseCommand):
    """
    This sub-class of Django's `BaseCommand` overrides `execute` to add audit
    logging to the command.
    """

    def execute(self, *args, **kwargs):

        # Initialize audit logging before we call the command.
        configure_audit_log_context(
            request_type="management-command",
            context={
                # Get the name of the command in the same way Django does in
                # the call_command utility.
                "name": self.__class__.__module__.split(".")[-1],
                # Include args and kwargs in the request log. This handles
                # most common argument types like file etc. For anything not
                # handled by default the user must provide a function that
                # converts the value to a JSON encodeable value.
                "args": args,
                "kwargs": kwargs,
            },
        )

        # Continue as normal
        return super().execute(*args, **kwargs)

    def handle(self, *args, **kwargs):
        raise NotImplementedError(
            "Subclasses of AuditLoggedCommand must provide a handle() method"
        )
