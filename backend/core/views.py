from rest_framework.decorators import api_view
from rest_framework.response import Response


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

