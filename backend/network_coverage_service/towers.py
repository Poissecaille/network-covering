from dataclasses import dataclass

TECHNOLOGIES = ["2G", "3G", "4G"]


@dataclass
class Tower:
    operator: str
    x: float
    y: float
    has_technology: dict[str, bool]


class TowerDataset:
    def __init__(self, towers: list[Tower]) -> None:
        self.towers = towers
