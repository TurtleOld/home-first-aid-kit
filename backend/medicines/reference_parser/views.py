from urllib.parse import urlparse
from hashlib import sha256

from django.core.cache import cache
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from accounts.permissions import IsFamilyMember

from .parser import ReferenceParserError, list_variants, parse_variant


CACHE_TTL_SECONDS = 60 * 60 * 24


def is_http_url(value):
    parsed = urlparse(value or "")
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def cache_key(*parts):
    raw = "\x1f".join(parts)
    return "drug-lookup:" + sha256(raw.encode("utf-8")).hexdigest()


class UrlSerializer(serializers.Serializer):
    url = serializers.URLField()

    def validate_url(self, value):
        if not is_http_url(value):
            raise serializers.ValidationError("Введите корректную http(s)-ссылку.")
        return value


class ParseSerializer(UrlSerializer):
    form = serializers.CharField(max_length=120, allow_blank=True, required=False)
    dosage = serializers.CharField(max_length=120, allow_blank=True, required=False)


class DrugLookupBaseView(APIView):
    permission_classes = [IsAuthenticated, IsFamilyMember]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "drug_lookup"

    def error_response(self, message, response_status=status.HTTP_400_BAD_REQUEST):
        return Response({"ok": False, "error": message}, status=response_status)


class DrugLookupFormsView(DrugLookupBaseView):
    def post(self, request):
        serializer = UrlSerializer(data=request.data)
        if not serializer.is_valid():
            return self.error_response(serializer.errors)

        url = serializer.validated_data["url"]
        key = cache_key("forms", url)
        cached = cache.get(key)
        if cached:
            return Response({"ok": True, **cached})

        try:
            result = list_variants(url)
        except ReferenceParserError as exc:
            return self.error_response(str(exc))

        cache.set(key, result, CACHE_TTL_SECONDS)
        return Response({"ok": True, **result})


class DrugLookupParseView(DrugLookupBaseView):
    def post(self, request):
        serializer = ParseSerializer(data=request.data)
        if not serializer.is_valid():
            return self.error_response(serializer.errors)

        url = serializer.validated_data["url"]
        form = serializer.validated_data.get("form", "")
        dosage = serializer.validated_data.get("dosage", "")
        key = cache_key("parse", url, form, dosage)
        cached = cache.get(key)
        if cached:
            return Response({"ok": True, **cached})

        try:
            result = parse_variant(url, form, dosage)
        except ReferenceParserError as exc:
            return self.error_response(str(exc))

        cache.set(key, result, CACHE_TTL_SECONDS)
        return Response({"ok": True, **result})
