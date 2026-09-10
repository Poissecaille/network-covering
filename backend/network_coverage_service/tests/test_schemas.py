from django.test import SimpleTestCase

from network_coverage_service.schemas import CoverageRequest, GeocodeQuery


class CoverageRequestTests(SimpleTestCase):
    def test_to_queries_object_converts_each_entry_into_a_geocode_query(self):
        payload = CoverageRequest(
            {
                "id1": "157 boulevard Mac Donald 75019 Paris",
                "id4": "5 avenue Anatole France 75007 Paris",
            }
        )

        queries = payload.to_queries_object()

        self.assertEqual(
            queries,
            [
                GeocodeQuery(id="id1", address="157 boulevard Mac Donald 75019 Paris"),
                GeocodeQuery(id="id4", address="5 avenue Anatole France 75007 Paris"),
            ],
        )

    def test_empty_payload_produces_no_queries(self):
        payload = CoverageRequest({})

        self.assertEqual(payload.to_queries_object(), [])
