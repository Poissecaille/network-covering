import logging

from ninja import Router

from network_coverage_service.exceptions import InvalidGeocodeResultError
from network_coverage_service.geocoding import GeocodingClient
from network_coverage_service.network_coverage import NetworkCoverageService
from network_coverage_service.schemas import CoverageRequest
from network_coverage_service.tower_csv_loader import TowerCsvLoader

logger = logging.getLogger(__name__)

router = Router()

geocoding_client = GeocodingClient()
network_coverage_service = NetworkCoverageService(TowerCsvLoader().load())


@router.post("/coverage")
async def coverage_endpoint(request, payload: CoverageRequest):
    geocode_results = await geocoding_client.geocode_addresses(
        payload.to_queries_object()
    )

    response = {}
    failures = 0
    for result in geocode_results:
        if result.found:
            if result.x is None or result.y is None:
                raise InvalidGeocodeResultError(
                    f"geocoded result for {result.id} is missing coordinates"
                )
            response[result.id] = network_coverage_service.coverage_at(
                result.x, result.y
            )
        else:
            failures += 1
            response[result.id] = {"error": result.error}

    logger.info(
        "coverage request processed: %d addresses, %d geocoding failures",
        len(geocode_results),
        failures,
    )

    return response
