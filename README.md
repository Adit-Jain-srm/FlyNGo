# FlyNGo — Airport Taxi → Ride Offers

A traveler posts a ride from their arrival flight to a hotel, with the price they will pay. Taxi suppliers who can actually do that ride assign a car and a price. The traveler books one offer, gets a 10-digit booking number, and can ask for a new flight or pickup time.

There is no login. On the home screen, choose Traveler or a supplier company from the data.

## Start

Requires Python 3.13 and Node 20+.

```bash
npm run setup
```

Then two terminals:

```bash
npm run api
```

```bash
npm run web
```

| What | URL |
|---|---|
| App | http://localhost:5173 |
| API | http://localhost:8000 |
| Health | http://localhost:8000/api/health |

`npm run setup` creates `.venv`, installs Python packages, and installs the web app. It is not a start command. The browser talks to the API at `http://localhost:8000` (CORS allows the Vite origin). Optional settings are in `.env.example` (`FLYNGO_DB`, `FLYNGO_DATA_DIR`, `CORS_ORIGINS`).

Tests:

```bash
npm test
```

## Architecture

```
Browser :5173  →  web/src/api/client.ts
                      ↓  HTTP
FastAPI :8000  routers  →  services (rules R1–R9)  →  repositories (SQL)  →  SQLite
                                                                              ↑
                                                         data/*.json upserted on startup
```

- **Frontend** (`web/`): Vite, React, TypeScript. Traveler flow and supplier flow are separate feature folders. The page does not apply ride rules; it only shows what the API returns.
- **Backend** (`backend/app/`): FastAPI. Routers handle HTTP. Services check the rules. Repositories run the SQL. Reference data (flights, hotels, airports, suppliers, cars, routes, booked rides) is loaded from the JSON files into SQLite on every startup. Those files are never written.
- **Database**: `backend/flyngo.db`. Requests, offers, bookings, and change requests live here, so they survive a refresh and a backend restart. Rows are not deleted (`is_active` is set to 0 instead).
- **Times** are local airport time, stored as `YYYY-MM-DDTHH:MM`. A car is busy from pickup until pickup + 2 × drive minutes. A window that starts exactly when another ends does not overlap.
- **Errors** look like `{ "rule": "R3", "field": "price_inr", "message": "...", "allowed": { "min": 10200, "max": 16800 } }`.

Full schema, queries, and indexes: [docs/DESIGN.md](docs/DESIGN.md).

## What is finished

Phase 1 (must-haves) and the car-type step:

| ID | What you can do |
|---|---|
| M1 | Post a ride: airport, date and flight, hotel, passengers and bags, optional car type, price. The form shows the route’s min–max. A bad flight, pickup, or price is refused with the rule. |
| M2 | Each supplier sees only open requests it can serve (airport, area, opening hours, a car that fits and is free). If nobody can, the traveler sees which check failed. |
| M3 | Assign a car and a price. A car or price that breaks a rule is refused, and the message names the rule (R3–R7). |
| M4 | Book one offer or reject it. Booking returns a unique 10-digit number. Other offers on that request become “not chosen”. |
| M5 | Open the summary with that number (flight, hotel, pickup, supplier, car, price). A wrong number says not found. It still works after the API process restarts. |
| M6 | Booking checks the car’s busy window again, including rides in `booked_rides.json`. If the car was taken, the booking is refused. |
| M7 | After booking, ask for a new flight or a new pickup. The supplier accepts or rejects. Acceptance requires the new pickup to be at least 60 minutes after the new landing and the same car to be free. A rejected change keeps the old booking. |
| G1 | One supplier can assign several of its cars to the same request, each with its own price. The same car cannot be offered twice. |
| G2 | Optional car type. Only types that can carry the party are offered. Suppliers can assign only that type. |
| G4 | A supplier can set when an offer ends. After that time the traveler cannot book it. |
| G5 | The traveler can sort offers by price and filter them by car type. |

Seeded requests `REQ-0001`–`REQ-0003` load at startup. `REQ-0002` (Kansai → Namba, sedan only) is a built-in “no supplier can serve this” case.

## Known limitations

- **Not in the good-to-have list:** there is no separate fleet screen. Assigning another car stays on the same request panel.
- **Not built:** shared rides (S1), login, payments, maps, notifications, live price changes, and any AI or LLM call.
- **Pickup** must be at least 60 minutes after landing. A later time is allowed.
- **No race lock.** Two people confirming the same car at the same instant are not handled. The check runs when the booking is confirmed. The problem says that is enough.
- **No accounts.** Request history in the traveler list is what the API returns. The booking number is the way back to a summary.
- **Demo is local.** Nothing is deployed. Do not edit files under `data/`.

## Data pack

| File | Use |
|---|---|
| `problem-2-airport-taxi-offers.md` | Problem statement, rules, how the work is judged |
| `DATA_DICTIONARY.md` | Every field and how the files join |
| `data/catalog/` | Flights, hotels, airports |
| `data/problem-2/` | Suppliers, routes, booked rides, open requests |

Field questions: the FAQ at the end of `DATA_DICTIONARY.md`, then the event help desk.
