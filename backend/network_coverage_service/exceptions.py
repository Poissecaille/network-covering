class CoverageError(Exception):
    """Base class for all business errors raised by network_coverage_service."""


class GeocodingServiceUnavailableError(CoverageError):
    """The government geocoding API is unreachable or responded with an error."""


class GeocodingResponseFormatError(CoverageError):
    """The geocoding API responded, but the returned CSV does not have the expected format."""


class InvalidGeocodeResultError(CoverageError):
    """A geocoding result is marked as found but has no coordinates."""
