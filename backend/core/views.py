import mimetypes
from pathlib import PurePosixPath

from django.conf import settings
from django.http import FileResponse, Http404, HttpResponse, HttpResponseForbidden
from rest_framework.decorators import api_view
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.selectors import get_current_family


@api_view(["GET"])
def api_root(request):
    return Response(
        {
            "name": "Home First-Aid Kit API",
            "health": request.build_absolute_uri("health/"),
        }
    )


@api_view(["GET"])
def health(request):
    return Response({"status": "ok"})


PROTECTED_MEDIA_PREFIXES = ("medicine_photos", "medicine_instructions")


class ProtectedMediaView(APIView):
    """Отдаёт файлы из /media/ только членам той же семьи через X-Accel-Redirect."""

    permission_classes = [IsAuthenticated]

    def get(self, request, path):
        parts = PurePosixPath(path).parts
        if len(parts) != 3 or parts[0] not in PROTECTED_MEDIA_PREFIXES or ".." in parts:
            raise Http404

        _, family_id, _ = parts
        family = get_current_family(request.user)
        if family is None or str(family.id) != family_id:
            return HttpResponseForbidden()

        content_type, _ = mimetypes.guess_type(path)
        content_type = content_type or "application/octet-stream"

        if settings.DEBUG:
            file_path = settings.MEDIA_ROOT / path
            if not file_path.is_file():
                raise Http404
            return FileResponse(open(file_path, "rb"), content_type=content_type)

        response = HttpResponse(content_type=content_type)
        response["X-Accel-Redirect"] = f"/protected-media/{path}"
        return response

