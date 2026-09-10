import csv
from pathlib import Path

from django.conf import settings

from network_coverage_service.towers import TECHNOLOGIES, Tower, TowerDataset

DEFAULT_CSV_PATH = (
    settings.BASE_DIR
    / "2018_01_Sites_mobiles_2G_3G_4G_France_metropolitaine_L93_ver2.csv"
)


class TowerCsvLoader:
    def load(self, csv_path: Path = DEFAULT_CSV_PATH) -> TowerDataset:
        towers = []

        with open(csv_path, newline="", encoding="utf-8") as csv_file:
            reader = csv.DictReader(csv_file)
            for row in reader:
                towers.append(
                    Tower(
                        operator=row["Operateur"],
                        x=float(row["x"]),
                        y=float(row["y"]),
                        has_technology={
                            technology: row[technology] == "1"
                            for technology in TECHNOLOGIES
                        },
                    )
                )

        return TowerDataset(towers)
