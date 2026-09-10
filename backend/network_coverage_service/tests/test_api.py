from unittest.mock import AsyncMock, patch

from django.test import SimpleTestCase

from network_coverage_service.exceptions import GeocodingServiceUnavailableError
from network_coverage_service.schemas import GeocodeResult


class CoverageEndpointTests(SimpleTestCase):
    def test_returns_coverage_for_a_found_address(self):
        geocode_result = GeocodeResult(id="id1", found=True, x=100.0, y=200.0)
        fake_coverage = {"Orange": {"2G": True, "3G": True, "4G": False}}

        with (
            patch(
                "network_coverage_service.api.geocoding_client.geocode_addresses",
                new=AsyncMock(return_value=[geocode_result]),
            ),
            patch(
                "network_coverage_service.api.network_coverage_service.coverage_at",
                return_value=fake_coverage,
            ) as mocked_coverage_at,
        ):
            response = self.client.post(
                "/api/coverage",
                data={"id1": "157 boulevard Mac Donald 75019 Paris"},
                content_type="application/json",
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"id1": fake_coverage})
        mocked_coverage_at.assert_called_once_with(100.0, 200.0)

    def test_returns_an_error_for_an_address_that_could_not_be_geocoded(self):
        geocode_result = GeocodeResult(
            id="id_bad", found=False, error="address not found"
        )

        with patch(
            "network_coverage_service.api.geocoding_client.geocode_addresses",
            new=AsyncMock(return_value=[geocode_result]),
        ):
            response = self.client.post(
                "/api/coverage",
                data={"id_bad": "zzzzzznotanaddress"},
                content_type="application/json",
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"id_bad": {"error": "address not found"}})

    def test_handles_multiple_addresses_in_one_request(self):
        results = [
            GeocodeResult(id="id1", found=True, x=1.0, y=2.0),
            GeocodeResult(id="id2", found=False, error="address not found"),
        ]

        with (
            patch(
                "network_coverage_service.api.geocoding_client.geocode_addresses",
                new=AsyncMock(return_value=results),
            ),
            patch(
                "network_coverage_service.api.network_coverage_service.coverage_at",
                return_value={"Orange": {"2G": True, "3G": True, "4G": True}},
            ),
        ):
            response = self.client.post(
                "/api/coverage",
                data={"id1": "adresse valide", "id2": "adresse invalide"},
                content_type="application/json",
            )

        self.assertEqual(
            response.json(),
            {
                "id1": {"Orange": {"2G": True, "3G": True, "4G": True}},
                "id2": {"error": "address not found"},
            },
        )

    def test_returns_502_when_the_geocoding_service_is_unavailable(self):
        with patch(
            "network_coverage_service.api.geocoding_client.geocode_addresses",
            new=AsyncMock(side_effect=GeocodingServiceUnavailableError("boom")),
        ):
            response = self.client.post(
                "/api/coverage",
                data={"id1": "157 boulevard Mac Donald 75019 Paris"},
                content_type="application/json",
            )

        self.assertEqual(response.status_code, 502)
        self.assertEqual(response.json(), {"detail": "geocoding service unavailable"})

    def test_returns_500_when_a_geocode_result_is_missing_coordinates(self):
        geocode_result = GeocodeResult(id="id1", found=True, x=None, y=None)

        with patch(
            "network_coverage_service.api.geocoding_client.geocode_addresses",
            new=AsyncMock(return_value=[geocode_result]),
        ):
            response = self.client.post(
                "/api/coverage",
                data={"id1": "157 boulevard Mac Donald 75019 Paris"},
                content_type="application/json",
            )

        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            response.json(), {"detail": "internal error while computing coverage"}
        )

    def test_returns_422_and_logs_a_warning_for_an_invalid_payload(self):
        with self.assertLogs("network_coverage.api", level="WARNING") as logs:
            response = self.client.post(
                "/api/coverage",
                data=[1, 2, 3],
                content_type="application/json",
            )

        self.assertEqual(response.status_code, 422)
        self.assertIn("detail", response.json())
        self.assertEqual(len(logs.records), 1)
        self.assertEqual(logs.records[0].levelname, "WARNING")
