import hashlib

import httpx
from django.core.cache import cache

from network_coverage_service.exceptions import (
    GeocodingResponseFormatError,
    GeocodingServiceUnavailableError,
)
from network_coverage_service.geocoding_csv_mapper import GeocodingCsvMapper
from network_coverage_service.schemas import GeocodeQuery, GeocodeResult


class GeocodingClient:
    api_url = "https://data.geopf.fr/geocodage/search/csv"
    # CACHE_TTL = 60 * 60 * 24 * 30
    CACHE_TTL = None  # durée de vie du cache à définir

    def __init__(self, mapper: GeocodingCsvMapper | None = None) -> None:
        self.mapper = mapper or GeocodingCsvMapper()

    async def geocode_addresses(
        self, queries: list[GeocodeQuery]
    ) -> list[GeocodeResult]:
        cached_results = []
        missing = []

        for query in queries:
            cached = cache.get(self._cache_key(query.address))
            if cached is None:
                missing.append(query)
            else:
                cached_results.append(
                    GeocodeResult(id=query.id, **cached.model_dump(exclude={"id"}))
                )

        new_results = await self._fetch(missing) if missing else []
        for query, result in zip(missing, new_results):
            cache.set(self._cache_key(query.address), result, timeout=self.CACHE_TTL)

        return cached_results + new_results

    async def _fetch(self, queries: list[GeocodeQuery]) -> list[GeocodeResult]:
        files = {"data": ("addresses.csv", self.mapper.to_csv(queries), "text/csv")}
        data = {
            "columns": "address",
            "result_columns": [
                "result_status",
                "latitude",
                "longitude",
                "result_x",
                "result_y",
                "result_score",
            ],
        }
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(self.api_url, data=data, files=files)
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise GeocodingServiceUnavailableError(str(exc)) from exc

        try:
            return self.mapper.from_csv(response.content)
        except (KeyError, ValueError) as exc:
            raise GeocodingResponseFormatError(str(exc)) from exc

    def _cache_key(self, address: str) -> str:
        normalized = address.strip().lower()
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
