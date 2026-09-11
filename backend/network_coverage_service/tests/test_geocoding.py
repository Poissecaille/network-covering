from unittest.mock import AsyncMock, MagicMock, patch

import httpx
from django.core.cache import cache
from django.test import SimpleTestCase

from network_coverage_service.exceptions import (
    GeocodingResponseFormatError,
    GeocodingServiceUnavailableError,
)
from network_coverage_service.geocoding import GeocodingClient
from network_coverage_service.schemas import GeocodeQuery, GeocodeResult


class GeocodingClientCacheTests(SimpleTestCase):
    def setUp(self):
        cache.clear()
        self.geocoding_client = GeocodingClient()

    async def test_calls_the_api_when_address_is_not_cached(self):
        fake_result = GeocodeResult(id="id1", found=True, x=1.0, y=2.0)
        with patch.object(
            GeocodingClient,
            "_fetch_geocode_data",
            new=AsyncMock(return_value=[fake_result]),
        ) as mocked_fetch_geocode_data:
            results = await self.geocoding_client.geocode_addresses(
                [GeocodeQuery(id="id1", address="1 rue de Paris")]
            )

        mocked_fetch_geocode_data.assert_awaited_once()
        self.assertEqual(results, [fake_result])

    async def test_second_call_for_the_same_address_uses_the_cache(self):
        fake_result = GeocodeResult(id="id1", found=True, x=1.0, y=2.0)
        with patch.object(
            GeocodingClient,
            "_fetch_geocode_data",
            new=AsyncMock(return_value=[fake_result]),
        ) as mocked_fetch_geocode_data:
            await self.geocoding_client.geocode_addresses(
                [GeocodeQuery(id="id1", address="1 rue de Paris")]
            )
            await self.geocoding_client.geocode_addresses(
                [GeocodeQuery(id="id9", address="1 rue de Paris")]
            )

        mocked_fetch_geocode_data.assert_awaited_once()

    async def test_cached_result_is_relabeled_with_the_current_query_id(self):
        fake_result = GeocodeResult(id="id1", found=True, x=1.0, y=2.0)
        with patch.object(
            GeocodingClient,
            "_fetch_geocode_data",
            new=AsyncMock(return_value=[fake_result]),
        ):
            await self.geocoding_client.geocode_addresses(
                [GeocodeQuery(id="id1", address="1 rue de Paris")]
            )
            results = await self.geocoding_client.geocode_addresses(
                [GeocodeQuery(id="id9", address="1 rue de Paris")]
            )

        self.assertEqual(results[0].id, "id9")
        self.assertEqual(results[0].x, 1.0)
        self.assertEqual(results[0].y, 2.0)

    async def test_only_missing_addresses_are_sent_to_the_api(self):
        cached_result = GeocodeResult(id="id1", found=True, x=1.0, y=2.0)
        fresh_result = GeocodeResult(id="id2", found=True, x=3.0, y=4.0)

        with patch.object(
            GeocodingClient,
            "_fetch_geocode_data",
            new=AsyncMock(return_value=[cached_result]),
        ):
            await self.geocoding_client.geocode_addresses(
                [GeocodeQuery(id="id1", address="1 rue de Paris")]
            )

        with patch.object(
            GeocodingClient,
            "_fetch_geocode_data",
            new=AsyncMock(return_value=[fresh_result]),
        ) as mocked_fetch_geocode_data:
            await self.geocoding_client.geocode_addresses(
                [
                    GeocodeQuery(id="id1", address="1 rue de Paris"),
                    GeocodeQuery(id="id2", address="2 rue de Paris"),
                ]
            )

        mocked_fetch_geocode_data.assert_awaited_once_with(
            [GeocodeQuery(id="id2", address="2 rue de Paris")]
        )


class FetchTests(SimpleTestCase):
    async def test_fetch_geocode_data_sends_the_request_and_parses_the_csv_response(
        self,
    ):
        client = GeocodingClient()
        queries = [
            GeocodeQuery(id="id1", address="157 boulevard Mac Donald 75019 Paris")
        ]

        csv_response = (
            b"id,address,result_status,latitude,longitude,result_x,result_y,result_score\n"
            b"id1,157 boulevard Mac Donald 75019 Paris,ok,48.898595,2.378185,"
            b"654412.35,6866689.51,0.908\n"
        )
        fake_response = MagicMock()
        fake_response.content = csv_response

        with patch(
            "httpx.AsyncClient.post", new=AsyncMock(return_value=fake_response)
        ) as mocked_post:
            results = await client._fetch_geocode_data(queries)

        fake_response.raise_for_status.assert_called_once()

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].id, "id1")
        self.assertTrue(results[0].found)
        self.assertEqual(results[0].x, 654412.35)
        self.assertEqual(results[0].y, 6866689.51)

        _, kwargs = mocked_post.call_args
        self.assertEqual(kwargs["data"]["columns"], "address")
        self.assertIn("result_x", kwargs["data"]["result_columns"])
        self.assertIn("result_y", kwargs["data"]["result_columns"])
        self.assertIn("data", kwargs["files"])

    async def test_fetch_geocode_data_raises_geocoding_service_unavailable_on_network_error(
        self,
    ):
        client = GeocodingClient()
        queries = [GeocodeQuery(id="id1", address="1 rue de Paris")]

        with patch(
            "httpx.AsyncClient.post",
            new=AsyncMock(side_effect=httpx.ConnectError("connection refused")),
        ), self.assertRaises(GeocodingServiceUnavailableError):
            await client._fetch_geocode_data(queries)

    async def test_fetch_geocode_data_raises_geocoding_service_unavailable_on_http_error_status(
        self,
    ):
        client = GeocodingClient()
        queries = [GeocodeQuery(id="id1", address="1 rue de Paris")]

        fake_response = MagicMock()
        fake_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "server error", request=MagicMock(), response=MagicMock()
        )

        with (
            patch("httpx.AsyncClient.post", new=AsyncMock(return_value=fake_response)),
            self.assertRaises(GeocodingServiceUnavailableError),
        ):
            await client._fetch_geocode_data(queries)

    async def test_fetch_geocode_data_raises_geocoding_response_format_error_on_malformed_csv(
        self,
    ):
        client = GeocodingClient()
        queries = [GeocodeQuery(id="id1", address="1 rue de Paris")]

        fake_response = MagicMock()
        fake_response.content = (
            b"id,address\nid1,1 rue de Paris\n"  # colonnes manquantes
        )

        with (
            patch("httpx.AsyncClient.post", new=AsyncMock(return_value=fake_response)),
            self.assertRaises(GeocodingResponseFormatError),
        ):
            await client._fetch_geocode_data(queries)


class GeocodingClientCacheKeyTests(SimpleTestCase):
    def setUp(self):
        self.geocoding_client = GeocodingClient()

    def test_cache_key_ignores_case_and_surrounding_whitespace(self):
        key1 = self.geocoding_client._cache_key("  Rue de Paris  ")
        key2 = self.geocoding_client._cache_key("rue de paris")

        self.assertEqual(key1, key2)

    def test_cache_key_differs_for_different_addresses(self):
        key1 = self.geocoding_client._cache_key("1 rue de Paris")
        key2 = self.geocoding_client._cache_key("2 rue de Paris")

        self.assertNotEqual(key1, key2)
