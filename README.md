# Hackathon data pack: Problem 2: Airport Taxi → Ride Offers

Everything your team needs for this problem.

## Start here

| Step | Read | Why |
|---|---|---|
| 1 | `problem-2-airport-taxi-offers.md` | The problem statement: what to build, the rules, and how we judge |
| 2 | `DATA_DICTIONARY.md` | What each data file is, how the files link, every field, a worked example, and a data FAQ |
| 3 | `data/` | The mock data (below) |

## The data in this pack

| File | One record is | Your app uses it to |
|---|---|---|
| `data/problem-2/taxi_companies.json` | One taxi supplier, with its cars | Show a dashboard per supplier (M2). Decide who sees a request (R4) and which car fits (R5). |
| `data/problem-2/routes.json` | One drive from an airport to one hotel area | Suggest the price range (R3). Get the drive time for the busy time of a car (R6). |
| `data/problem-2/booked_rides.json` | One ride booked before the event | Keep those cars busy at those times (R6) |
| `data/problem-2/open_requests.json` | One ride request posted before the event | Show requests on supplier dashboards from the start |
| `data/catalog/flights.json` | One flight on one date | The traveler picks the arrival flight. Its arrival time gives the earliest pickup (R2). |
| `data/catalog/hotels.json` | One hotel | The traveler picks the hotel. Its city and area pick the route (R3) and the suppliers (R4). |
| `data/catalog/airports.json` | One airport | Check that the arrival airport serves the hotel's city (R1) |

All data is synthetic. All times are local times. All prices are in INR. The data files are read-only: keep your own data in your own database.

## Rules (short version)

1. Any language, framework, and database. AI tools to help you write code are allowed. **Your app must not call an AI or LLM model.**
2. Build a **backend** and a **frontend** that work together. The frontend gets data from your backend, not from the files.
3. Do not change the data files. Judges use the same files.
4. Write feature code during the event. Push to Git every hour.
5. Your app must start with 1–2 commands. Write them in your README.
6. At code freeze, upload a zip to HackerEarth (no `node_modules`, no virtual environments, no API keys).

## Questions

Read the FAQ at the end of `DATA_DICTIONARY.md` first. Then ask at the help desk or in the event chat channel. We send every answer to all teams.
