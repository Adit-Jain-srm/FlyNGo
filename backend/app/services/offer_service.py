"""Offer service managing supplier request views, car advisories, and offer creation."""

import sqlite3
from typing import Any

from backend.app.errors import ConflictException, NotFoundException, RuleViolationException
from backend.app.log import get_logger
from backend.app.repositories import catalog_repo, eligibility_repo, offer_repo, request_repo, supplier_repo
from backend.app.schemas import (
    CarAdvisoryResponse,
    NoSupplierReasonResponse,
    OfferCreatePayload,
    OfferResponse,
    RideRequestResponse,
)
from backend.app.services.rules import (
    compute_ride_busy_interval,
    is_supplier_open_at_time,
    validate_r3_price,
)


def _normalize_expiry(value: str | None) -> str | None:
    """Accept YYYY-MM-DDTHH:MM. Empty means the offer does not expire."""
    if value is None or not value.strip():
        return None
    text = value.strip().replace(" ", "T")
    if len(text) >= 16 and text[4] == "-" and text[7] == "-" and text[10] == "T" and text[13] == ":":
        return text[:16]
    raise RuleViolationException(
        rule="G4",
        field="expires_at",
        message="Offer expiry must be a time like 2027-04-10T18:00.",
    )


def get_requests_for_supplier(
    conn: sqlite3.Connection,
    supplier_id: str,
) -> list[RideRequestResponse]:
    """Retrieve all open ride requests eligible for this supplier (B.2 query)."""
    supplier = supplier_repo.get_supplier_by_id(conn, supplier_id)
    if not supplier:
        raise NotFoundException(f"Supplier {supplier_id} not found.")

    rows = eligibility_repo.get_open_requests_for_supplier(conn, supplier_id)
    return [RideRequestResponse(**dict(r)) for r in rows]


def get_car_advisories_for_request(
    conn: sqlite3.Connection,
    supplier_id: str,
    request_id: str,
) -> list[CarAdvisoryResponse]:
    """Evaluate supplier's vehicles against request requirements and assign advisory badges."""
    req = request_repo.get_request_by_id(conn, request_id)
    if not req:
        raise NotFoundException(f"Request {request_id} not found.")

    route = catalog_repo.get_route(conn, req["airport_code"], req["city"], req["area"])
    drive_minutes = route["drive_minutes"] if route else 60
    start_local, end_local = compute_ride_busy_interval(req["pickup_local"], drive_minutes)

    advisories = eligibility_repo.get_supplier_fleet_with_badges(
        conn=conn,
        supplier_id=supplier_id,
        passengers=req["passengers"],
        large_bags=req["large_bags"],
        small_bags=req["small_bags"],
        car_type=req["car_type"],
        start_local=start_local,
        end_local=end_local,
    )

    return [CarAdvisoryResponse(**item) for item in advisories]


def get_request_offers_and_status(
    conn: sqlite3.Connection,
    request_id: str,
) -> dict[str, Any]:
    """Retrieve offers for a request and compute B.3 funnel reason if no offers exist."""
    req = request_repo.get_request_by_id(conn, request_id)
    if not req:
        raise NotFoundException(f"Request {request_id} not found.")

    offers = offer_repo.get_offers_for_request(conn, request_id)

    route = catalog_repo.get_route(conn, req["airport_code"], req["city"], req["area"])
    drive_minutes = route["drive_minutes"] if route else 60
    start_local, end_local = compute_ride_busy_interval(req["pickup_local"], drive_minutes)

    funnel = eligibility_repo.get_no_supplier_funnel_counts(
        conn=conn,
        airport=req["airport_code"],
        city=req["city"],
        area=req["area"],
        pax=req["passengers"],
        large=req["large_bags"],
        small=req["small_bags"],
        car_type=req["car_type"],
        start_local=start_local,
        end_local=end_local,
    )

    failing_step: str | None = None
    plain_reason: str = ""

    if funnel["at_airport"] == 0:
        failing_step = "at_airport"
        plain_reason = "No registered taxi suppliers operate at this arrival airport."
    elif funnel["drives_to_area"] == 0:
        failing_step = "drives_to_area"
        plain_reason = "Suppliers at this airport do not provide service to this hotel area."
    elif funnel["open_at_pickup"] == 0:
        failing_step = "open_at_pickup"
        plain_reason = "Suppliers covering this area are closed during your scheduled pickup time."
    elif funnel["has_fitting_car"] == 0:
        failing_step = "has_fitting_car"
        plain_reason = "No supplier has a vehicle with enough seats/luggage capacity for your party."
    elif funnel["has_free_fitting_car"] == 0:
        failing_step = "has_free_fitting_car"
        plain_reason = "All fitting vehicles from suppliers covering this route are currently booked."
    else:
        plain_reason = f"{funnel['has_free_fitting_car']} suppliers can serve this request. Waiting for offers to be posted."

    funnel_result = NoSupplierReasonResponse(
        has_eligible_supplier=funnel["has_free_fitting_car"] > 0,
        failing_step=failing_step,
        plain_reason=plain_reason,
        at_airport_count=funnel["at_airport"],
        in_area_count=funnel["drives_to_area"],
        open_at_pickup_count=funnel["open_at_pickup"],
        has_fitting_car_count=funnel["has_fitting_car"],
        has_free_fitting_car_count=funnel["has_free_fitting_car"],
    )

    return {
        "offers": [OfferResponse(**o) for o in offers],
        "funnel": funnel_result,
    }


def create_supplier_offer(
    conn: sqlite3.Connection,
    request_id: str,
    payload: OfferCreatePayload,
) -> OfferResponse:
    """Validate R4-R7 and create a new offer."""
    # 1. Check request is OPEN
    req = request_repo.get_request_by_id(conn, request_id)
    if not req:
        raise NotFoundException(f"Request {request_id} not found.")

    if req["status"] != "OPEN":
        raise ConflictException(
            rule="R7",
            message=f"Request {request_id} is already {req['status']} and cannot receive new offers.",
        )

    # 2. Check supplier exists
    supplier = supplier_repo.get_supplier_by_id(conn, payload.supplier_id)
    if not supplier:
        raise NotFoundException(f"Supplier {payload.supplier_id} not found.")

    # 3. Check vehicle belongs to supplier (R7)
    vehicle = conn.execute(
        "SELECT * FROM vehicles WHERE vehicle_id = ? AND supplier_id = ? AND is_active = 1;",
        (payload.vehicle_id, payload.supplier_id),
    ).fetchone()
    if not vehicle:
        raise RuleViolationException(
            rule="R7",
            field="vehicle_id",
            message=f"Vehicle {payload.vehicle_id} does not belong to supplier {payload.supplier_id}.",
        )

    # 4. Check car_type preference (G2 / R5)
    if req["car_type"] and vehicle["type"] != req["car_type"]:
        raise RuleViolationException(
            rule="R5",
            field="vehicle_id",
            message=f"Vehicle type {vehicle['type']} does not match requested car type {req['car_type']}.",
            allowed=req["car_type"],
        )

    # 5. Check operational eligibility: airport, area, and hours (R4)
    airports = supplier_repo.get_supplier_airports(conn, payload.supplier_id)
    if req["airport_code"] not in airports:
        raise RuleViolationException(
            rule="R4",
            field="supplier_id",
            message=f"Supplier does not serve arrival airport {req['airport_code']}.",
        )

    areas = supplier_repo.get_supplier_areas(conn, payload.supplier_id)
    area_match = any(
        a["city"] == req["city"] and a["area"] == req["area"] for a in areas
    )
    if not area_match:
        raise RuleViolationException(
            rule="R4",
            field="supplier_id",
            message=f"Supplier does not drive to {req['city']} ({req['area']}).",
        )

    if not is_supplier_open_at_time(supplier["service_from"], supplier["service_until"], req["pickup_local"]):
        raise RuleViolationException(
            rule="R4",
            field="supplier_id",
            message=f"Supplier is closed at pickup time {req['pickup_local'][11:16]} (Operating hours: {supplier['service_from']} – {supplier['service_until']}).",
        )

    # 6. Check vehicle capacity (R5)
    if vehicle["seats"] < req["passengers"]:
        raise RuleViolationException(
            rule="R5",
            field="vehicle_id",
            message=f"Vehicle has {vehicle['seats']} seats, but request requires {req['passengers']} passengers.",
            allowed={"min_seats": req["passengers"]},
        )

    if vehicle["large_bags"] < req["large_bags"]:
        raise RuleViolationException(
            rule="R5",
            field="vehicle_id",
            message=f"Vehicle capacity of {vehicle['large_bags']} large bags is less than requested {req['large_bags']}.",
            allowed={"min_large_bags": req["large_bags"]},
        )

    if vehicle["small_bags"] < req["small_bags"]:
        raise RuleViolationException(
            rule="R5",
            field="vehicle_id",
            message=f"Vehicle capacity of {vehicle['small_bags']} small bags is less than requested {req['small_bags']}.",
            allowed={"min_small_bags": req["small_bags"]},
        )

    # 7. Check vehicle is free (R6)
    route = catalog_repo.get_route(conn, req["airport_code"], req["city"], req["area"])
    drive_minutes = route["drive_minutes"] if route else 60
    start_local, end_local = compute_ride_busy_interval(req["pickup_local"], drive_minutes)

    conflicts = conn.execute(
        """
        SELECT busy_end AS conflict_end
        FROM bookings
        WHERE vehicle_id = ? AND is_active = 1
          AND busy_start < ? AND ? < busy_end
        UNION ALL
        SELECT end_local AS conflict_end
        FROM booked_rides
        WHERE vehicle_id = ? AND is_active = 1
          AND start_local < ? AND ? < end_local;
        """,
        (payload.vehicle_id, end_local, start_local, payload.vehicle_id, end_local, start_local),
    ).fetchall()

    if conflicts:
        conflict_end = conflicts[0]["conflict_end"]
        raise RuleViolationException(
            rule="R6",
            field="vehicle_id",
            message=f"Vehicle {payload.vehicle_id} is busy until {conflict_end[11:16]}.",
            allowed={"busy_until": conflict_end},
        )

    # 8. Check price within route range (R3 / R7)
    if route:
        validate_r3_price(payload.price_inr, route["price_min_inr"], route["price_max_inr"])

    # 9. Check duplicate offer for same vehicle
    if offer_repo.check_existing_offer_for_car(conn, request_id, payload.vehicle_id):
        raise ConflictException(
            rule="R7",
            field="vehicle_id",
            message=f"Vehicle {payload.vehicle_id} has already been offered for request {request_id}.",
        )

    # 10. Persist offer
    conn.execute("BEGIN TRANSACTION;")
    try:
        offer_id = offer_repo.create_offer(
            conn=conn,
            request_id=request_id,
            supplier_id=payload.supplier_id,
            vehicle_id=payload.vehicle_id,
            price_inr=payload.price_inr,
            expires_at=_normalize_expiry(payload.expires_at),
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise

    saved = offer_repo.get_offer_by_id(conn, offer_id)
    if not saved:
        raise NotFoundException("Offer created could not be retrieved.")

    created = OfferResponse(**saved)
    get_logger().info(
        "offer assigned id=%s request=%s supplier=%s vehicle=%s price=%s",
        created.offer_id,
        created.request_id,
        created.supplier_id,
        created.vehicle_id,
        created.price_inr,
    )
    return created
