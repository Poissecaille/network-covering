import logging

from django.conf import settings
from ninja import NinjaAPI
from ninja.errors import ValidationError
from ninja.openapi.docs import Redoc

from network_coverage_service.api import router as coverage_router
from network_coverage_service.exceptions import (
    GeocodingResponseFormatError,
    GeocodingServiceUnavailableError,
    InvalidGeocodeResultError,
)

logger = logging.getLogger(__name__)

API_DESCRIPTION = (settings.BASE_DIR.parent / "README.md").read_text(encoding="utf-8")

api = NinjaAPI(
    title="Network Coverage API",
    description=API_DESCRIPTION,
    docs=Redoc(),
)
api.add_router("", coverage_router)


@api.exception_handler(GeocodingServiceUnavailableError)
def handle_geocoding_service_unavailable(request, exc):
    logger.error("geocoding service unavailable: %s", exc)
    return api.create_response(
        request, {"detail": "geocoding service unavailable"}, status=502
    )


@api.exception_handler(GeocodingResponseFormatError)
def handle_geocoding_response_format_error(request, exc):
    logger.error("unexpected geocoding response format: %s", exc)
    return api.create_response(
        request,
        {"detail": "geocoding service returned an unexpected response"},
        status=502,
    )


@api.exception_handler(InvalidGeocodeResultError)
def handle_invalid_geocode_result(request, exc):
    logger.error("invalid geocode result: %s", exc)
    return api.create_response(
        request, {"detail": "internal error while computing coverage"}, status=500
    )


@api.exception_handler(ValidationError)
def handle_validation_error(request, exc):
    logger.warning("invalid request payload: %s", exc.errors)
    return api.create_response(request, {"detail": exc.errors}, status=422)
