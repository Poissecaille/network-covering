import csv
import io
from typing import ClassVar

from network_coverage_service.schemas import GeocodeQuery, GeocodeResult

# Score de confiance renvoyé par l'API Adresse (data.gouv.fr) :
#   >= 0.95     correspondance quasi exacte
#   0.85 - 0.95 très proche, fiable dans la grande majorité des cas
#   0.70 - 0.85 approximative : risque réel d'erreur (bonne rue, mauvaise commune)
#   < 0.70      faible, nécessite une validation manuelle

MIN_GEOCODING_THRESHOLD = 0.70


class GeocodingCsvMapper:
    fieldnames: ClassVar[list[str]] = ["id", "address"]

    def to_csv(self, queries: list[GeocodeQuery]) -> bytes:
        buffer = io.StringIO()
        writer = csv.DictWriter(buffer, fieldnames=self.fieldnames)
        writer.writeheader()
        for query in queries:
            writer.writerow({"id": query.id, "address": query.address})
        return buffer.getvalue().encode("utf-8")

    def from_csv(self, content: bytes) -> list[GeocodeResult]:
        reader = csv.DictReader(io.StringIO(content.decode("utf-8")))
        return [self._to_result(row) for row in reader]

    def _to_result(self, row: dict[str, str]) -> GeocodeResult:
        if row["result_status"] != "ok":
            return GeocodeResult(id=row["id"], found=False, error="address not found")

        score = float(row["result_score"])

        if score < MIN_GEOCODING_THRESHOLD:
            return GeocodeResult(
                id=row["id"],
                found=False,
                score=score,
                error=(
                    f"address matched with low confidence "
                    f"({score:.2f} < {MIN_GEOCODING_THRESHOLD:.2f}), "
                    f"manual validation required"
                ),
            )

        return GeocodeResult(
            id=row["id"],
            found=True,
            longitude=float(row["longitude"]),
            latitude=float(row["latitude"]),
            x=float(row["result_x"]),
            y=float(row["result_y"]),
            score=score,
        )
