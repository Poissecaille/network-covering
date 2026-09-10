from django.test import SimpleTestCase

from network_coverage_service.network_coverage import NetworkCoverageService
from network_coverage_service.towers import Tower, TowerDataset


class EuclideanDistanceTests(SimpleTestCase):
    def test_computes_distance_for_a_3_4_5_triangle(self):
        service = NetworkCoverageService(TowerDataset([]))

        distance = service.euclidean_distance(0, 0, 3, 4)

        self.assertEqual(distance, 5)

    def test_distance_is_zero_for_identical_points(self):
        service = NetworkCoverageService(TowerDataset([]))

        distance = service.euclidean_distance(10, 20, 10, 20)

        self.assertEqual(distance, 0)


class CoverageAtTests(SimpleTestCase):
    def setUp(self):
        self.towers = TowerDataset(
            [
                # à 0m de l'adresse testée, toutes technos actives
                Tower(
                    operator="Orange",
                    x=0,
                    y=0,
                    has_technology={"2G": True, "3G": True, "4G": True},
                ),
                # à 20 000m, seule la 2G est active sur cette antenne (rayon 2G = 30km)
                Tower(
                    operator="Orange",
                    x=20_000,
                    y=0,
                    has_technology={"2G": True, "3G": False, "4G": False},
                ),
                # proche (1000m) mais aucune techno active sur cette antenne
                Tower(
                    operator="Bouygues",
                    x=1_000,
                    y=0,
                    has_technology={"2G": False, "3G": False, "4G": False},
                ),
                # trop loin (100 000m) pour n'importe quel rayon
                Tower(
                    operator="SFR",
                    x=100_000,
                    y=0,
                    has_technology={"2G": True, "3G": True, "4G": True},
                ),
            ]
        )
        self.service = NetworkCoverageService(self.towers)

    def test_operator_covered_when_a_close_tower_has_the_technology(self):
        coverage = self.service.coverage_at(0, 0)

        self.assertEqual(coverage["Orange"], {"2G": True, "3G": True, "4G": True})

    def test_operator_partially_covered_depending_on_technology_radius(self):
        # isole l'antenne qui n'a que la 2G active, sur un point à 20km d'elle
        towers = TowerDataset(
            [
                Tower(
                    operator="Orange",
                    x=20_000,
                    y=0,
                    has_technology={"2G": True, "3G": False, "4G": False},
                ),
            ]
        )
        coverage = NetworkCoverageService(towers).coverage_at(0, 0)

        self.assertEqual(coverage["Orange"], {"2G": True, "3G": False, "4G": False})

    def test_operator_not_covered_when_no_technology_flag_is_true(self):
        coverage = self.service.coverage_at(0, 0)

        self.assertEqual(coverage["Bouygues"], {"2G": False, "3G": False, "4G": False})

    def test_operator_not_covered_when_all_towers_are_too_far(self):
        coverage = self.service.coverage_at(0, 0)

        self.assertEqual(coverage["SFR"], {"2G": False, "3G": False, "4G": False})

    def test_every_operator_present_in_the_dataset_appears_in_the_result(self):
        coverage = self.service.coverage_at(0, 0)

        self.assertEqual(set(coverage.keys()), {"Orange", "Bouygues", "SFR"})

    def test_no_towers_returns_no_operators(self):
        coverage = NetworkCoverageService(TowerDataset([])).coverage_at(0, 0)

        self.assertEqual(coverage, {})
