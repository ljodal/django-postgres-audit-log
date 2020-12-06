from django.http import HttpRequest, JsonResponse
from django.views.decorators.http import require_POST

from .models import MyAuditLoggedModel


@require_POST
def create_object(request: HttpRequest) -> JsonResponse:
    """
    Test view that writes to an audit logged model.
    """

    model = MyAuditLoggedModel.objects.create(some_text=request.POST["value"])

    return JsonResponse({"id": model.id})
