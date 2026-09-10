from typing import Literal

from ninja import Schema
from pydantic import RootModel


class GeocodeQuery(Schema):
    id: str
    address: str


class CoverageRequest(RootModel[dict[str, str]]):
    def to_queries_object(self) -> list[GeocodeQuery]:
        return [
            GeocodeQuery(id=address_id, address=address_name)
            for address_id, address_name in self.root.items()
        ]


class GeocodeFeatureProperties(Schema):
    label: str
    score: float
    type: Literal["housenumber", "street", "locality", "municipality"]
    citycode: str | None = None
    postcode: str | None = None
    city: str | None = None


class GeocodePointGeometry(Schema):
    type: Literal["Point"]
    coordinates: tuple[float, float]


class GeocodeFeature(Schema):
    properties: GeocodeFeatureProperties
    geometry: GeocodePointGeometry


class GeocodeFeatureCollection(Schema):
    type: Literal["FeatureCollection"]
    query: str
    features: list[GeocodeFeature]


class GeocodeResult(Schema):
    id: str
    found: bool
    longitude: float | None = None
    latitude: float | None = None
    x: float | None = None
    y: float | None = None
    score: float | None = None
    error: str | None = None
