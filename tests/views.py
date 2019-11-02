from django.http import HttpRequest, JsonResponse
from django.views.decorators.http import require_POST

from .models import AuditLoggedModel


@require_POST
def create_object(request: HttpRequest) -> JsonResponse:
    model = AuditLoggedModel.objects.create(some_text=request.POST["value"])

    return JsonResponse({"id": model.id})
