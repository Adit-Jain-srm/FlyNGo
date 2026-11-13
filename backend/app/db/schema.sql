-- FlyNGo SQLite DDL Schema (Appendix A from docs/DESIGN.md)
-- Enforces soft delete (is_active IN (0,1)), PRAGMA foreign_keys = ON, and strict constraints.

-- Reference tables (upserted from data/*.json on startup)
CREATE TABLE IF NOT EXISTS airports (
  code TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  city TEXT NOT NULL,
  country TEXT NOT NULL,
  timezone TEXT NOT NULL,
  is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0,1)),
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS airport_cities (
  airport_code TEXT NOT NULL REFERENCES airports(code),
  city TEXT NOT NULL,
  is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0,1)),
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (airport_code, city)
);

CREATE TABLE IF NOT EXISTS flights (
  flight_id TEXT PRIMARY KEY,
  airline TEXT NOT NULL,
  flight_number TEXT NOT NULL,
  from_airport TEXT NOT NULL REFERENCES airports(code),
  to_airport TEXT NOT NULL REFERENCES airports(code),
  departure_local TEXT NOT NULL,
  arrival_local TEXT NOT NULL,
  arrival_date TEXT NOT NULL,
  stops INTEGER NOT NULL,
  duration_minutes INTEGER NOT NULL,
  cabin TEXT,
  is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0,1)),
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS hotels (
  hotel_id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  city TEXT NOT NULL,
  area TEXT NOT NULL,
  stars INTEGER,
  rating REAL,
  is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0,1)),
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS routes (
  airport TEXT NOT NULL REFERENCES airports(code),
  city TEXT NOT NULL,
  area TEXT NOT NULL,
  distance_km REAL NOT NULL,
  drive_minutes INTEGER NOT NULL CHECK (drive_minutes > 0),
  price_min_inr INTEGER NOT NULL,
  price_max_inr INTEGER NOT NULL CHECK (price_max_inr >= price_min_inr),
  is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0,1)),
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (airport, city, area)
);

CREATE TABLE IF NOT EXISTS suppliers (
  supplier_id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  service_from TEXT NOT NULL,
  service_until TEXT NOT NULL,
  rating REAL,
  is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0,1)),
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS supplier_airports (
  airport_code TEXT NOT NULL REFERENCES airports(code),
  supplier_id TEXT NOT NULL REFERENCES suppliers(supplier_id),
  is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0,1)),
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (airport_code, supplier_id)
);

CREATE TABLE IF NOT EXISTS supplier_areas (
  city TEXT NOT NULL,
  area TEXT NOT NULL,
  supplier_id TEXT NOT NULL REFERENCES suppliers(supplier_id),
  is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0,1)),
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (city, area, supplier_id)
);

CREATE TABLE IF NOT EXISTS vehicles (
  vehicle_id TEXT PRIMARY KEY,
  supplier_id TEXT NOT NULL REFERENCES suppliers(supplier_id),
  type TEXT NOT NULL CHECK (type IN ('HATCHBACK','SEDAN','SUV','BUS')),
  seats INTEGER NOT NULL,
  large_bags INTEGER NOT NULL,
  small_bags INTEGER NOT NULL,
  is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0,1)),
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS booked_rides (
  ride_id TEXT PRIMARY KEY,
  supplier_id TEXT NOT NULL REFERENCES suppliers(supplier_id),
  vehicle_id TEXT NOT NULL REFERENCES vehicles(vehicle_id),
  start_local TEXT NOT NULL,
  end_local TEXT NOT NULL CHECK (end_local > start_local),
  is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0,1)),
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- App tables
CREATE TABLE IF NOT EXISTS ride_requests (
  request_id TEXT PRIMARY KEY,
  source TEXT NOT NULL CHECK (source IN ('SEED','APP')),
  traveler_name TEXT,
  flight_id TEXT NOT NULL REFERENCES flights(flight_id),
  hotel_id TEXT NOT NULL REFERENCES hotels(hotel_id),
  airport_code TEXT NOT NULL,
  city TEXT NOT NULL,
  area TEXT NOT NULL,
  adults INTEGER NOT NULL CHECK (adults >= 1),
  passengers INTEGER NOT NULL CHECK (passengers >= adults),
  large_bags INTEGER NOT NULL CHECK (large_bags >= 0),
  small_bags INTEGER NOT NULL CHECK (small_bags >= 0),
  pickup_local TEXT NOT NULL,
  car_type TEXT CHECK (car_type IS NULL OR car_type IN ('HATCHBACK','SEDAN','SUV','BUS')),
  price_inr INTEGER NOT NULL CHECK (price_inr > 0),
  status TEXT NOT NULL DEFAULT 'OPEN' CHECK (status IN ('OPEN','BOOKED')),
  is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0,1)),
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS request_children (
  request_id TEXT NOT NULL REFERENCES ride_requests(request_id),
  child_no INTEGER NOT NULL,
  age INTEGER NOT NULL CHECK (age BETWEEN 0 AND 17),
  is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0,1)),
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (request_id, child_no)
);

CREATE TABLE IF NOT EXISTS offers (
  offer_id INTEGER PRIMARY KEY AUTOINCREMENT,
  request_id TEXT NOT NULL REFERENCES ride_requests(request_id),
  supplier_id TEXT NOT NULL REFERENCES suppliers(supplier_id),
  vehicle_id TEXT NOT NULL REFERENCES vehicles(vehicle_id),
  price_inr INTEGER NOT NULL CHECK (price_inr > 0),
  status TEXT NOT NULL DEFAULT 'OPEN' CHECK (status IN ('OPEN','BOOKED','REJECTED','NOT_CHOSEN')),
  is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0,1)),
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bookings (
  booking_number TEXT PRIMARY KEY
    CHECK (length(booking_number) = 10 AND booking_number NOT GLOB '*[^0-9]*' AND substr(booking_number, 1, 1) <> '0'),
  request_id TEXT NOT NULL REFERENCES ride_requests(request_id),
  offer_id INTEGER NOT NULL REFERENCES offers(offer_id),
  supplier_id TEXT NOT NULL REFERENCES suppliers(supplier_id),
  vehicle_id TEXT NOT NULL REFERENCES vehicles(vehicle_id),
  flight_id TEXT NOT NULL REFERENCES flights(flight_id),
  pickup_local TEXT NOT NULL,
  busy_start TEXT NOT NULL,
  busy_end TEXT NOT NULL CHECK (busy_end > busy_start),
  price_inr INTEGER NOT NULL,
  status TEXT NOT NULL DEFAULT 'CONFIRMED' CHECK (status IN ('CONFIRMED')),
  is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0,1)),
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS change_requests (
  change_id INTEGER PRIMARY KEY AUTOINCREMENT,
  booking_number TEXT NOT NULL REFERENCES bookings(booking_number),
  supplier_id TEXT NOT NULL REFERENCES suppliers(supplier_id),
  old_flight_id TEXT NOT NULL,
  old_pickup_local TEXT NOT NULL,
  new_flight_id TEXT NOT NULL,
  new_pickup_local TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'WAITING' CHECK (status IN ('WAITING','ACCEPTED','REJECTED')),
  reason TEXT,
  is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0,1)),
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Partial indexes for active rows (WHERE is_active = 1)
CREATE INDEX IF NOT EXISTS ix_flights_arrival ON flights(to_airport, arrival_date) WHERE is_active = 1;
CREATE INDEX IF NOT EXISTS ix_hotels_city_name ON hotels(city, name COLLATE NOCASE) WHERE is_active = 1;
CREATE INDEX IF NOT EXISTS ix_vehicles_supplier ON vehicles(supplier_id, type) WHERE is_active = 1;
CREATE INDEX IF NOT EXISTS ix_booked_rides_vehicle ON booked_rides(vehicle_id, start_local, end_local) WHERE is_active = 1;
CREATE INDEX IF NOT EXISTS ix_bookings_vehicle ON bookings(vehicle_id, busy_start, busy_end) WHERE is_active = 1;
CREATE INDEX IF NOT EXISTS ix_requests_status ON ride_requests(status, airport_code) WHERE is_active = 1;
CREATE INDEX IF NOT EXISTS ix_offers_request ON offers(request_id, status) WHERE is_active = 1;
CREATE INDEX IF NOT EXISTS ix_offers_supplier ON offers(supplier_id, status) WHERE is_active = 1;
CREATE INDEX IF NOT EXISTS ix_changes_supplier ON change_requests(supplier_id, status) WHERE is_active = 1;

-- Partial unique indexes enforcing business rules
CREATE UNIQUE INDEX IF NOT EXISTS ux_booking_per_request ON bookings(request_id) WHERE is_active = 1;
CREATE UNIQUE INDEX IF NOT EXISTS ux_offer_per_vehicle ON offers(request_id, vehicle_id) WHERE is_active = 1;
CREATE UNIQUE INDEX IF NOT EXISTS ux_waiting_change ON change_requests(booking_number) WHERE status = 'WAITING' AND is_active = 1;
