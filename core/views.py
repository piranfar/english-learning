from django.conf import settings
from django.shortcuts import redirect
from rest_framework.response import Response
from rest_framework.views import APIView


def root_redirect(request):
    return redirect(settings.FRONTEND_URL)


class HealthView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        return Response(
            {
                "app": "FluentBridge AI Backend",
                "status": "ok",
                "frontend": settings.FRONTEND_URL,
                "admin": "/admin/",
                "api": "/api/",
            }
        )
