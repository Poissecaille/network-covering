import logging
import math

from network_coverage_service.towers import TECHNOLOGIES, TowerDataset

logger = logging.getLogger(__name__)

TECHNOLOGY_RADIUS_METERS = {
    "2G": 30_000,
    "3G": 5_000,
    "4G": 10_000,
}


class NetworkCoverageService:
    def __init__(self, towers: TowerDataset) -> None:
        self.towers = towers

    def euclidean_distance(self, x1: float, y1: float, x2: float, y2: float) -> float:
        distance = math.dist((x1, y1), (x2, y2))
        logger.debug(
            "distance between (%s, %s) and (%s, %s) = %s", x1, y1, x2, y2, distance
        )
        return distance

    def coverage_at(self, x: float, y: float) -> dict[str, dict[str, bool]]:
        coverage_by_operator: dict[str, dict[str, bool]] = {}

        for tower in self.towers.towers:
            if tower.operator not in coverage_by_operator:
                coverage_by_operator[tower.operator] = {
                    technology: False for technology in TECHNOLOGIES
                }

            distance = self.euclidean_distance(tower.x, tower.y, x, y)

            for technology in TECHNOLOGIES:
                is_covered = (
                    tower.has_technology[technology]
                    and distance <= TECHNOLOGY_RADIUS_METERS[technology]
                )
                if is_covered:
                    coverage_by_operator[tower.operator][technology] = True

        return coverage_by_operator
