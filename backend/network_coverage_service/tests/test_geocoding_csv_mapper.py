from django.test import SimpleTestCase

from network_coverage_service.geocoding_csv_mapper import GeocodingCsvMapper
from network_coverage_service.schemas import GeocodeQuery


class ToCsvTests(SimpleTestCase):
    def setUp(self):
        self.mapper = GeocodingCsvMapper()

    def test_writes_one_row_per_query_with_id_and_address(self):
        queries = [
            GeocodeQuery(id="id1", address="157 boulevard Mac Donald 75019 Paris"),
            GeocodeQuery(id="id4", address="5 avenue Anatole France 75007 Paris"),
        ]

        csv_bytes = self.mapper.to_csv(queries)

        expected = (
            "id,address\r\n"
            "id1,157 boulevard Mac Donald 75019 Paris\r\n"
            "id4,5 avenue Anatole France 75007 Paris\r\n"
        )
        self.assertEqual(csv_bytes.decode("utf-8"), expected)

    def test_quotes_addresses_containing_a_comma(self):
        queries = [GeocodeQuery(id="id5", address="1 Bd de Parc, 77700 Coupvray")]

        csv_bytes = self.mapper.to_csv(queries)

        self.assertIn('"1 Bd de Parc, 77700 Coupvray"', csv_bytes.decode("utf-8"))

    def test_empty_query_list_produces_only_the_header(self):
        csv_bytes = self.mapper.to_csv([])

        self.assertEqual(csv_bytes.decode("utf-8"), "id,address\r\n")


class FromCsvTests(SimpleTestCase):
    def setUp(self):
        self.mapper = GeocodingCsvMapper()

    def test_parses_a_successfully_geocoded_row(self):
        content = (
            b"id,address,result_status,latitude,longitude,result_x,result_y,result_score\n"
            b"id1,157 boulevard Mac Donald 75019 Paris,ok,48.898595,2.378185,654412.35,6866689.51,0.908\n"
        )

        results = self.mapper.from_csv(content)

        self.assertEqual(len(results), 1)
        result = results[0]
        self.assertEqual(result.id, "id1")
        self.assertTrue(result.found)
        self.assertEqual(result.latitude, 48.898595)
        self.assertEqual(result.longitude, 2.378185)
        self.assertEqual(result.x, 654412.35)
        self.assertEqual(result.y, 6866689.51)
        self.assertEqual(result.score, 0.908)
        self.assertIsNone(result.error)

    def test_parses_a_not_found_row_without_crashing_on_empty_fields(self):
        content = (
            b"id,address,result_status,latitude,longitude,result_x,result_y,result_score\n"
            b"id_bad,notanaddress,not-found,,,,,\n"
        )

        results = self.mapper.from_csv(content)

        self.assertEqual(len(results), 1)
        result = results[0]
        self.assertEqual(result.id, "id_bad")
        self.assertFalse(result.found)
        self.assertIsNone(result.latitude)
        self.assertIsNone(result.longitude)
        self.assertIsNone(result.x)
        self.assertIsNone(result.y)
        self.assertIsNone(result.score)
        self.assertEqual(result.error, "address not found")

    def test_parses_multiple_rows_in_order(self):
        content = (
            b"id,address,result_status,latitude,longitude,result_x,result_y,result_score\n"
            b"id1,a,ok,1.0,2.0,3.0,4.0,0.5\n"
            b"id2,b,not-found,,,,,\n"
        )

        results = self.mapper.from_csv(content)

        self.assertEqual([result.id for result in results], ["id1", "id2"])
