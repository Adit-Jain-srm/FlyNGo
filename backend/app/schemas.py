"""Core Pydantic data schemas and response envelopes for FlyNGo."""

from typing import Any, Literal
from pydantic import BaseModel, Field, model_validator


# -------------------------------------------------------------
# System & Health Schemas
# -------------------------------------------------------------
class HealthResponse(BaseModel):
    """Health check response containing table record counts."""

    status: str = Field(default="healthy", description="Service health status")
    counts: dict[str, int] = Field(description="Record counts across reference and app tables")


class ErrorResponse(BaseModel):
    """Standardized rule error envelope."""

    rule: str
    message: str
    field: str | None = None
    allowed: Any | None = None


# -------------------------------------------------------------
# Catalog Schemas
# -------------------------------------------------------------
class AirportResponse(BaseModel):
    """Airport information."""

    code: str
    name: str
    city: str
    country: str
    timezone: str


class FlightResponse(BaseModel):
    """Catalog flight information."""

    flight_id: str
    airline: str
    flight_number: str
    from_airport: str
    to_airport: str
    departure_local: str
    arrival_local: str
    arrival_date: str
    stops: int
    duration_minutes: int
    cabin: str | None = None


class HotelResponse(BaseModel):
    """Hotel information."""

    hotel_id: str
    name: str
    city: str
    area: str
    stars: int | None = None
    rating: float | None = None


class RouteQuoteResponse(BaseModel):
    """Price suggestion and route travel estimates."""

    airport: str
    city: str
    area: str
    distance_km: float
    drive_minutes: int
    price_min_inr: int
    price_max_inr: int
    recommended_pickup_local: str
    earliest_pickup_local: str
    latest_pickup_local: str


class CarTypeSuitabilityResponse(BaseModel):
    """Vehicle type suitability based on party size and luggage (G2)."""

    type: str
    max_seats: int
    max_large_bags: int
    max_small_bags: int
    available_fleet_count: int


# -------------------------------------------------------------
# Request Schemas
# -------------------------------------------------------------
CarTypeLiteral = Literal["HATCHBACK", "SEDAN", "SUV", "BUS"]


class RideRequestCreate(BaseModel):
    """Payload to post a new ride request."""

    traveler_name: str | None = Field(default=None, description="Optional traveler contact name")
    flight_id: str = Field(description="Arrival flight ID from catalog (e.g. FL-401)")
    hotel_id: str = Field(description="Destination hotel ID from catalog (e.g. HTL-TYO-004)")
    adults: int = Field(ge=1, description="Number of adults (minimum 1)")
    child_ages: list[int] = Field(default_factory=list, description="Ages of children (0 to 17)")
    large_bags: int = Field(default=0, ge=0, description="Number of check-in / large bags")
    small_bags: int = Field(default=0, ge=0, description="Number of cabin / small bags")
    pickup_local: str | None = Field(default=None, description="Optional pickup time YYYY-MM-DDTHH:MM")
    car_type: CarTypeLiteral | None = Field(default=None, description="Optional preferred car type")
    price_inr: int = Field(gt=0, description="Traveler's proposed price in INR")


class RequestChildResponse(BaseModel):
    """Child age entry for a ride request."""

    child_no: int
    age: int


class RideRequestResponse(BaseModel):
    """Full details of a ride request."""

    request_id: str
    source: str
    traveler_name: str | None = None
    flight_id: str
    hotel_id: str
    airport_code: str
    city: str
    area: str
    adults: int
    passengers: int
    large_bags: int
    small_bags: int
    pickup_local: str
    car_type: str | None = None
    price_inr: int
    status: str
    created_at: str
    children: list[RequestChildResponse] = Field(default_factory=list)
    # Joined summary metadata for display convenience
    airline: str | None = None
    flight_number: str | None = None
    arrival_local: str | None = None
    hotel_name: str | None = None
    price_min_inr: int | None = None
    price_max_inr: int | None = None


# -------------------------------------------------------------
# Supplier & Fleet Schemas
# -------------------------------------------------------------
class SupplierResponse(BaseModel):
    """Taxi supplier company details."""

    supplier_id: str
    name: str
    service_from: str
    service_until: str
    rating: float | None = None
    airports: list[str] = Field(default_factory=list)
    areas: list[dict[str, str]] = Field(default_factory=list)


VehicleStatusLiteral = Literal["FITS_FREE", "BUSY", "TOO_SMALL", "WRONG_TYPE"]


class CarAdvisoryResponse(BaseModel):
    """Supplier vehicle with computed advisory fit badge for a request."""

    vehicle_id: str
    supplier_id: str
    type: str
    seats: int
    large_bags: int
    small_bags: int
    badge: VehicleStatusLiteral
    reason: str
    busy_until: str | None = None
    is_selectable: bool = True


class NoSupplierReasonResponse(BaseModel):
    """B.3 Funnel breakdown when no supplier can serve a request."""

    has_eligible_supplier: bool
    failing_step: str | None = None
    plain_reason: str
    at_airport_count: int
    in_area_count: int
    open_at_pickup_count: int
    has_fitting_car_count: int
    has_free_fitting_car_count: int


# -------------------------------------------------------------
# Offer Schemas
# -------------------------------------------------------------
OfferStatusLiteral = Literal["OPEN", "BOOKED", "REJECTED", "NOT_CHOSEN"]


class OfferCreatePayload(BaseModel):
    """Payload for a supplier to assign a vehicle with a price to a request."""

    supplier_id: str
    vehicle_id: str
    price_inr: int = Field(gt=0, description="Supplier's offer price in INR")


class OfferResponse(BaseModel):
    """Assigned vehicle offer details."""

    offer_id: int
    request_id: str
    supplier_id: str
    vehicle_id: str
    price_inr: int
    status: OfferStatusLiteral
    created_at: str
    # Joined metadata
    supplier_name: str | None = None
    supplier_rating: float | None = None
    vehicle_type: str | None = None
    vehicle_seats: int | None = None
    vehicle_large_bags: int | None = None
    vehicle_small_bags: int | None = None


# -------------------------------------------------------------
# Booking Schemas
# -------------------------------------------------------------
class BookingResponse(BaseModel):
    """Confirmed ride booking details."""

    booking_number: str
    request_id: str
    offer_id: int
    supplier_id: str
    vehicle_id: str
    flight_id: str
    pickup_local: str
    busy_start: str
    busy_end: str
    price_inr: int
    status: str
    created_at: str
    supplier_name: str | None = None
    supplier_rating: float | None = None
    vehicle_type: str | None = None
    vehicle_seats: int | None = None
    vehicle_large_bags: int | None = None
    vehicle_small_bags: int | None = None
    traveler_name: str | None = None
    airport_code: str | None = None
    city: str | None = None
    area: str | None = None
    passengers: int | None = None
    large_bags: int | None = None
    small_bags: int | None = None
    airline: str | None = None
    flight_number: str | None = None
    from_airport: str | None = None
    arrival_local: str | None = None
    hotel_id: str | None = None
    hotel_name: str | None = None
    hotel_address: str | None = None
    drive_minutes: int | None = None
    distance_km: float | None = None


# -------------------------------------------------------------
# Change Request Schemas
# -------------------------------------------------------------
class ChangeRequestCreate(BaseModel):
    """Payload to request a flight change on a confirmed booking."""

    new_flight_id: str | None = Field(default=None, description="New flight ID landing at the same airport")
    new_pickup_local: str | None = Field(default=None, description="New pickup time, local to the arrival airport")

    @model_validator(mode="after")
    def require_a_change(self) -> "ChangeRequestCreate":
        if not self.new_flight_id and not self.new_pickup_local:
            raise ValueError("Provide a new flight or a new pickup time.")
        return self


class ChangeDecisionPayload(BaseModel):
    """Payload for supplier to accept or reject a flight change request."""

    reason: str | None = Field(default=None, description="Optional rejection reason")


class ChangeRequestResponse(BaseModel):
    """Flight change request details."""

    change_id: int
    booking_number: str
    supplier_id: str
    old_flight_id: str
    old_pickup_local: str
    new_flight_id: str
    new_pickup_local: str
    status: Literal["WAITING", "ACCEPTED", "REJECTED"]
    reason: str | None = None
    created_at: str
    supplier_name: str | None = None
    new_airline: str | None = None
    new_arrival_local: str | None = None
    vehicle_id: str | None = None
    price_inr: int | None = None

