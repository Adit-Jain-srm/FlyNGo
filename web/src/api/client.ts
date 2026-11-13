/**
 * FlyNGo API Client
 * Uses VITE_API_URL (default: http://localhost:8000)
 */

export const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export interface ApiRuleError {
  rule: string;
  message: string;
  field?: string;
  allowed?: any;
}

export class ApiError extends Error {
  status: number;
  data: ApiRuleError | { message: string };

  constructor(status: number, data: any) {
    super(data?.message || `HTTP error ${status}`);
    this.name = "ApiError";
    this.status = status;
    this.data = data;
  }
}

export async function apiFetch<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_URL}${endpoint.startsWith("/") ? endpoint : `/${endpoint}`}`;

  const headers = {
    "Content-Type": "application/json",
    ...options.headers,
  };

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let errorData;
    try {
      errorData = await response.json();
    } catch {
      errorData = { message: response.statusText };
    }
    throw new ApiError(response.status, errorData);
  }

  return response.json();
}

// -------------------------------------------------------------
// System & Health
// -------------------------------------------------------------
export interface HealthResponse {
  status: string;
  counts: Record<string, number>;
}

export async function fetchHealth(): Promise<HealthResponse> {
  return apiFetch<HealthResponse>("/api/health");
}

// -------------------------------------------------------------
// Catalog Models & APIs
// -------------------------------------------------------------
export interface Airport {
  code: string;
  name: string;
  city: string;
  country: string;
  timezone: string;
}

export interface Flight {
  flight_id: string;
  airline: string;
  flight_number: string;
  from_airport: string;
  to_airport: string;
  departure_local: string;
  arrival_local: string;
  arrival_date: string;
  stops: number;
  duration_minutes: number;
  cabin?: string;
}

export interface Hotel {
  hotel_id: string;
  name: string;
  city: string;
  area: string;
  stars?: number;
  rating?: number;
}

export interface RouteQuote {
  airport: string;
  city: string;
  area: string;
  distance_km: number;
  drive_minutes: number;
  price_min_inr: number;
  price_max_inr: number;
  recommended_pickup_local: string;
  earliest_pickup_local: string;
  latest_pickup_local: string;
}

export interface CarTypeSuitability {
  type: string;
  max_seats: number;
  max_large_bags: number;
  max_small_bags: number;
  available_fleet_count: number;
}

export async function fetchAirports(): Promise<Airport[]> {
  return apiFetch<Airport[]>("/api/airports");
}

export async function fetchFlights(airport: string, date: string): Promise<Flight[]> {
  return apiFetch<Flight[]>(`/api/flights?airport=${encodeURIComponent(airport)}&date=${encodeURIComponent(date)}`);
}

export async function fetchHotels(airport: string, query?: string): Promise<Hotel[]> {
  const url = query && query.trim()
    ? `/api/hotels?airport=${encodeURIComponent(airport)}&q=${encodeURIComponent(query.trim())}`
    : `/api/hotels?airport=${encodeURIComponent(airport)}`;
  return apiFetch<Hotel[]>(url);
}

export async function fetchQuote(flightId: string, hotelId: string): Promise<RouteQuote> {
  return apiFetch<RouteQuote>(`/api/quote?flight_id=${encodeURIComponent(flightId)}&hotel_id=${encodeURIComponent(hotelId)}`);
}

export async function fetchCarTypes(pax: number, large: number, small: number): Promise<CarTypeSuitability[]> {
  return apiFetch<CarTypeSuitability[]>(`/api/car-types?pax=${pax}&large=${large}&small=${small}`);
}

// -------------------------------------------------------------
// Requests Models & APIs
// -------------------------------------------------------------
export interface RideRequestCreatePayload {
  traveler_name?: string;
  flight_id: string;
  hotel_id: string;
  adults: number;
  child_ages: number[];
  large_bags: number;
  small_bags: number;
  pickup_local?: string;
  car_type?: string | null;
  price_inr: number;
}

export interface RequestChild {
  child_no: number;
  age: number;
}

export interface RideRequest {
  request_id: string;
  source: string;
  traveler_name?: string;
  flight_id: string;
  hotel_id: string;
  airport_code: string;
  city: string;
  area: string;
  adults: number;
  passengers: number;
  large_bags: number;
  small_bags: number;
  pickup_local: string;
  car_type?: string | null;
  price_inr: number;
  status: string;
  created_at: string;
  children: RequestChild[];
  airline?: string;
  flight_number?: string;
  arrival_local?: string;
  hotel_name?: string;
  drive_minutes?: number;
  distance_km?: number;
  price_min_inr?: number;
  price_max_inr?: number;
}

export async function createRideRequest(payload: RideRequestCreatePayload): Promise<RideRequest> {
  return apiFetch<RideRequest>("/api/requests", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function fetchRequest(requestId: string): Promise<RideRequest> {
  return apiFetch<RideRequest>(`/api/requests/${encodeURIComponent(requestId)}`);
}

export async function fetchRequests(status?: string): Promise<RideRequest[]> {
  const url = status ? `/api/requests?status=${encodeURIComponent(status)}` : "/api/requests";
  return apiFetch<RideRequest[]>(url);
}

// -------------------------------------------------------------
// Supplier & Offer Models & APIs
// -------------------------------------------------------------
export interface Supplier {
  supplier_id: string;
  name: string;
  service_from: string;
  service_until: string;
  rating?: number;
  airports: string[];
  areas: Array<{ city: string; area: string }>;
}

export interface CarAdvisory {
  vehicle_id: string;
  supplier_id: string;
  type: string;
  seats: number;
  large_bags: number;
  small_bags: number;
  badge: "FITS_FREE" | "BUSY" | "TOO_SMALL" | "WRONG_TYPE";
  reason: string;
  busy_until?: string | null;
  is_selectable: boolean;
}

export interface Offer {
  offer_id: number;
  request_id: string;
  supplier_id: string;
  vehicle_id: string;
  price_inr: number;
  status: "OPEN" | "BOOKED" | "REJECTED" | "NOT_CHOSEN";
  expires_at?: string | null;
  created_at: string;
  supplier_name?: string;
  supplier_rating?: number;
  vehicle_type?: string;
  vehicle_seats?: number;
  vehicle_large_bags?: number;
  vehicle_small_bags?: number;
}

export interface FunnelBreakdown {
  has_eligible_supplier: boolean;
  failing_step?: string | null;
  plain_reason: string;
  at_airport_count: number;
  in_area_count: number;
  open_at_pickup_count: number;
  has_fitting_car_count: number;
  has_free_fitting_car_count: number;
}

export interface RequestOffersResult {
  offers: Offer[];
  funnel: FunnelBreakdown;
}

export async function fetchSuppliers(): Promise<Supplier[]> {
  return apiFetch<Supplier[]>("/api/suppliers");
}

export async function fetchSupplierRequests(supplierId: string): Promise<RideRequest[]> {
  return apiFetch<RideRequest[]>(`/api/suppliers/${encodeURIComponent(supplierId)}/requests`);
}

export async function fetchSupplierCars(supplierId: string, requestId: string): Promise<CarAdvisory[]> {
  return apiFetch<CarAdvisory[]>(`/api/suppliers/${encodeURIComponent(supplierId)}/requests/${encodeURIComponent(requestId)}/cars`);
}

export async function fetchSupplierOffers(supplierId: string): Promise<Offer[]> {
  return apiFetch<Offer[]>(`/api/suppliers/${encodeURIComponent(supplierId)}/offers`);
}

export async function fetchSupplierBookings(supplierId: string): Promise<any[]> {
  return apiFetch<any[]>(`/api/suppliers/${encodeURIComponent(supplierId)}/bookings`);
}

export async function fetchSupplierChanges(supplierId: string): Promise<any[]> {
  return apiFetch<any[]>(`/api/suppliers/${encodeURIComponent(supplierId)}/changes`);
}

export async function createOffer(
  requestId: string,
  payload: { supplier_id: string; vehicle_id: string; price_inr: number; expires_at?: string }
): Promise<Offer> {
  return apiFetch<Offer>(`/api/requests/${encodeURIComponent(requestId)}/offers`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function rejectOffer(offerId: number): Promise<{ status: string; message: string }> {
  return apiFetch<{ status: string; message: string }>(`/api/offers/${offerId}/reject`, {
    method: "POST",
  });
}

export async function fetchRequestOffers(requestId: string): Promise<RequestOffersResult> {
  return apiFetch<RequestOffersResult>(`/api/requests/${encodeURIComponent(requestId)}/offers`);
}

// -------------------------------------------------------------
// Booking & Change Request Models & APIs
// -------------------------------------------------------------
export interface Booking {
  booking_number: string;
  request_id: string;
  offer_id: number;
  supplier_id: string;
  vehicle_id: string;
  flight_id: string;
  pickup_local: string;
  busy_start: string;
  busy_end: string;
  price_inr: number;
  status: string;
  created_at: string;
  supplier_name?: string;
  supplier_rating?: number;
  vehicle_type?: string;
  vehicle_seats?: number;
  vehicle_large_bags?: number;
  vehicle_small_bags?: number;
  traveler_name?: string;
  airport_code?: string;
  city?: string;
  area?: string;
  passengers?: number;
  large_bags?: number;
  small_bags?: number;
  airline?: string;
  flight_number?: string;
  from_airport?: string;
  arrival_local?: string;
  hotel_id?: string;
  hotel_name?: string;
  hotel_city?: string;
  hotel_area?: string;
  drive_minutes?: number;
  distance_km?: number;
}

export interface ChangeRequest {
  change_id: number;
  booking_number: string;
  supplier_id: string;
  old_flight_id: string;
  old_pickup_local: string;
  new_flight_id: string;
  new_pickup_local: string;
  status: "WAITING" | "ACCEPTED" | "REJECTED";
  reason?: string | null;
  created_at: string;
  supplier_name?: string;
  new_airline?: string;
  new_arrival_local?: string;
  vehicle_id?: string;
  price_inr?: number;
}

export async function bookOffer(offerId: number): Promise<Booking> {
  return apiFetch<Booking>(`/api/offers/${offerId}/book`, {
    method: "POST",
  });
}

export async function fetchBookings(): Promise<Booking[]> {
  return apiFetch<Booking[]>("/api/bookings");
}

export async function fetchBooking(bookingNumber: string): Promise<Booking> {
  return apiFetch<Booking>(`/api/bookings/${encodeURIComponent(bookingNumber)}`);
}

export async function requestFlightChange(
  bookingNumber: string,
  payload: { new_flight_id?: string; new_pickup_local?: string }
): Promise<ChangeRequest> {
  return apiFetch<ChangeRequest>(`/api/bookings/${encodeURIComponent(bookingNumber)}/changes`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function fetchBookingChanges(bookingNumber: string): Promise<ChangeRequest[]> {
  return apiFetch<ChangeRequest[]>(`/api/bookings/${encodeURIComponent(bookingNumber)}/changes`);
}

export async function acceptChangeRequest(changeId: number): Promise<ChangeRequest> {
  return apiFetch<ChangeRequest>(`/api/changes/${changeId}/accept`, {
    method: "POST",
  });
}

export async function rejectChangeRequest(changeId: number, reason?: string): Promise<ChangeRequest> {
  return apiFetch<ChangeRequest>(`/api/changes/${changeId}/reject`, {
    method: "POST",
    body: JSON.stringify({ reason }),
  });
}
