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
        self._http_client = httpx.AsyncClient()

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

        unique_missing = self._deduplicate_by_address(missing)

        fetched = (
            await self._fetch_geocode_data(unique_missing) if unique_missing else []
        )

        results_by_address = {}
        for query, result in zip(unique_missing, fetched):
            cache.set(self._cache_key(query.address), result, timeout=self.CACHE_TTL)
            results_by_address[query.address] = result

        new_results = [
            GeocodeResult(
                id=query.id,
                **results_by_address[query.address].model_dump(exclude={"id"}),
            )
            for query in missing
        ]

        return cached_results + new_results

    async def _fetch_geocode_data(
        self, queries: list[GeocodeQuery]
    ) -> list[GeocodeResult]:
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
            response = await self._http_client.post(
                self.api_url, data=data, files=files
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise GeocodingServiceUnavailableError(str(exc)) from exc

        try:
            return self.mapper.from_csv(response.content)
        except (KeyError, ValueError) as exc:
            raise GeocodingResponseFormatError(str(exc)) from exc

    def _deduplicate_by_address(
        self, queries: list[GeocodeQuery]
    ) -> list[GeocodeQuery]:
        seen_addresses = set()
        unique_queries = []
        for query in queries:
            if query.address not in seen_addresses:
                seen_addresses.add(query.address)
                unique_queries.append(query)
        return unique_queries

    def _cache_key(self, address: str) -> str:
        normalized = address.strip().lower()
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
