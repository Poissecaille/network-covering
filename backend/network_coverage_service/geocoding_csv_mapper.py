import csv
import io
from typing import ClassVar

from network_coverage_service.schemas import GeocodeQuery, GeocodeResult


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
        results = []
        for row in reader:
            found = row["result_status"] == "ok"
            results.append(
                GeocodeResult(
                    id=row["id"],
                    found=found,
                    longitude=float(row["longitude"]) if found else None,
                    latitude=float(row["latitude"]) if found else None,
                    x=float(row["result_x"]) if found else None,
                    y=float(row["result_y"]) if found else None,
                    score=float(row["result_score"]) if found else None,
                    error=None if found else "address not found",
                )
            )
        return results
