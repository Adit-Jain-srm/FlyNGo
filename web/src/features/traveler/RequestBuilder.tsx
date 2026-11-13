import React, { useEffect, useState } from "react";
import {
  Check,
  ChevronRight,
  Clock,
  Edit2,
  ArrowRight,
} from "lucide-react";
import {
  Airport,
  Flight,
  Hotel,
  RouteQuote,
  CarTypeSuitability,
  fetchAirports,
  fetchFlights,
  fetchHotels,
  fetchQuote,
  fetchCarTypes,
  createRideRequest,
  RideRequest,
  ApiError,
  ApiRuleError,
} from "../../api/client";
import { formatINR } from "../../lib/formatters";
import { PriceRangeBar } from "./PriceRangeBar";
import { RuleErrorAlert } from "../../components/common/RuleErrorAlert";
import { emitSyncEvent } from "../../lib/sync";

interface RequestBuilderProps {
  onRequestCreated: (request: RideRequest) => void;
}

export const RequestBuilder: React.FC<RequestBuilderProps> = ({ onRequestCreated }) => {
  // Current active step (1 to 7)
  const [activeStep, setActiveStep] = useState<number>(1);

  // Form states
  const [travelerName, setTravelerName] = useState<string>("");
  const [selectedAirport, setSelectedAirport] = useState<Airport | null>(null);
  const [selectedDate, setSelectedDate] = useState<string>("2027-04-10");
  const [selectedFlight, setSelectedFlight] = useState<Flight | null>(null);
  const [pickupTime, setPickupTime] = useState<string>("");
  const [hotelSearch, setHotelSearch] = useState<string>("");
  const [selectedHotel, setSelectedHotel] = useState<Hotel | null>(null);
  const [adults, setAdults] = useState<number>(2);
  const [childAges, setChildAges] = useState<number[]>([6]);
  const [largeBags, setLargeBags] = useState<number>(3);
  const [smallBags, setSmallBags] = useState<number>(2);
  const [selectedCarType, setSelectedCarType] = useState<string | null>(null);
  const [priceInr, setPriceInr] = useState<number>(12000);

  // Catalog loaded states
  const [airports, setAirports] = useState<Airport[]>([]);
  const [flights, setFlights] = useState<Flight[]>([]);
  const [hotels, setHotels] = useState<Hotel[]>([]);
  const [hotelsLoading, setHotelsLoading] = useState<boolean>(false);
  const [hotelsError, setHotelsError] = useState<string | null>(null);
  const [quote, setQuote] = useState<RouteQuote | null>(null);
  const [suitableCarTypes, setSuitableCarTypes] = useState<CarTypeSuitability[]>([]);

  // UI state
  const [loading, setLoading] = useState<boolean>(false);
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [ruleError, setRuleError] = useState<ApiRuleError | string | null>(null);

  // Load airports on mount
  useEffect(() => {
    fetchAirports().then(setAirports).catch(console.error);
  }, []);

  // Load flights when airport or date changes
  useEffect(() => {
    if (selectedAirport && selectedDate) {
      setLoading(true);
      fetchFlights(selectedAirport.code, selectedDate)
        .then((data) => {
          setFlights(data);
          setLoading(false);
        })
        .catch(() => setLoading(false));
    }
  }, [selectedAirport, selectedDate]);

  // Ask the API for hotels. A short pause keeps fast typing from showing an older result.
  useEffect(() => {
    if (!selectedAirport) {
      return;
    }
    let cancelled = false;
    setHotelsLoading(true);
    setHotelsError(null);
    const handle = window.setTimeout(() => {
      fetchHotels(selectedAirport.code, hotelSearch)
        .then((rows) => {
          if (!cancelled) {
            setHotels(rows);
            setHotelsLoading(false);
          }
        })
        .catch(() => {
          if (!cancelled) {
            setHotels([]);
            setHotelsLoading(false);
            setHotelsError("Could not load hotels. Try the search again.");
          }
        });
    }, 200);
    return () => {
      cancelled = true;
      window.clearTimeout(handle);
    };
  }, [selectedAirport, hotelSearch]);

  // Load quote when flight and hotel are selected
  useEffect(() => {
    if (selectedFlight && selectedHotel) {
      fetchQuote(selectedFlight.flight_id, selectedHotel.hotel_id)
        .then((q) => {
          setQuote(q);
          if (!pickupTime) {
            setPickupTime(q.recommended_pickup_local);
          }
          if (priceInr === 0 || priceInr < q.price_min_inr || priceInr > q.price_max_inr) {
            setPriceInr(Math.round((q.price_min_inr + q.price_max_inr) / 2));
          }
        })
        .catch(console.error);
    }
  }, [selectedFlight, selectedHotel]);

  // Load suitable car types when passenger or luggage counts change
  useEffect(() => {
    const totalPax = adults + childAges.length;
    fetchCarTypes(totalPax, largeBags, smallBags)
      .then(setSuitableCarTypes)
      .catch(console.error);
  }, [adults, childAges, largeBags, smallBags]);


  // Submit request
  const handleSubmit = async () => {
    if (!selectedFlight || !selectedHotel) {
      setRuleError("Please choose both a flight and a hotel.");
      return;
    }

    setSubmitting(true);
    setRuleError(null);

    try {
      const result = await createRideRequest({
        traveler_name: travelerName || undefined,
        flight_id: selectedFlight.flight_id,
        hotel_id: selectedHotel.hotel_id,
        adults,
        child_ages: childAges,
        large_bags: largeBags,
        small_bags: smallBags,
        pickup_local: pickupTime || undefined,
        car_type: selectedCarType,
        price_inr: priceInr,
      });

      emitSyncEvent("REQUEST_CREATED");
      onRequestCreated(result);
    } catch (err: any) {
      if (err instanceof ApiError && err.data) {
        setRuleError(err.data as ApiRuleError);
      } else {
        setRuleError(err.message || "Failed to post ride request.");
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto py-8 px-4 sm:px-6 space-y-6">
      {/* Header */}
      <div className="bg-white p-6 rounded-3xl border border-slate-200/80 shadow-sm">
        <div>
          <span className="text-[11px] font-bold text-blue-600 uppercase tracking-widest">
            Airport Ground Transfer
          </span>
          <h1 className="text-2xl font-black text-slate-900 mt-1">Book Your Airport Ride</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Select your arrival airport, flight schedule, hotel, and target fare.
          </p>
        </div>
      </div>

      {/* Global Error Banner */}
      <RuleErrorAlert error={ruleError} onDismiss={() => setRuleError(null)} />

      {/* ----------------------------------------------------------------- */}
      {/* CARD 1: Airport Selection */}
      {/* ----------------------------------------------------------------- */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden transition-all duration-200">
        <div
          onClick={() => setActiveStep(1)}
          className={`p-5 flex items-center justify-between cursor-pointer ${
            activeStep === 1 ? "bg-slate-50/50 border-b border-slate-200" : ""
          }`}
        >
          <div className="flex items-center space-x-3">
            <div
              className={`w-8 h-8 rounded-lg flex items-center justify-center font-bold text-sm ${
                selectedAirport
                  ? "bg-emerald-100 text-emerald-700"
                  : "bg-blue-100 text-blue-700"
              }`}
            >
              {selectedAirport ? <Check className="w-4 h-4" /> : "1"}
            </div>
            <div>
              <span className="text-sm font-bold text-slate-900">Arrival Airport</span>
              {selectedAirport && activeStep !== 1 && (
                <div className="text-xs text-slate-500">
                  {selectedAirport.name} ({selectedAirport.code}) • {selectedAirport.city}
                </div>
              )}
            </div>
          </div>
          {selectedAirport && activeStep !== 1 && (
            <span className="text-xs font-semibold text-blue-600 flex items-center space-x-1">
              <Edit2 className="w-3.5 h-3.5" />
              <span>Change</span>
            </span>
          )}
        </div>

        {activeStep === 1 && (
          <div className="p-6 space-y-4">
            <p className="text-xs text-slate-500">
              Select one of the 5 supported international hub airports:
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
              {airports.map((ap) => {
                const isSelected = selectedAirport?.code === ap.code;
                return (
                  <button
                    key={ap.code}
                    type="button"
                    onClick={() => {
                      setSelectedAirport(ap);
                      setSelectedFlight(null);
                      setSelectedHotel(null);
                      setHotelSearch("");
                      setActiveStep(2);
                    }}
                    className={`p-4 rounded-xl border text-left transition-all ${
                      isSelected
                        ? "border-blue-600 bg-blue-50/50 ring-2 ring-blue-500/20"
                        : "border-slate-200 hover:border-blue-300 hover:bg-slate-50"
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-lg font-black text-slate-900">{ap.code}</span>
                      <span className="text-xs px-2 py-0.5 rounded-full bg-slate-100 font-semibold text-slate-600">
                        {ap.city}
                      </span>
                    </div>
                    <div className="text-xs text-slate-600 font-medium mt-1 truncate">
                      {ap.name}
                    </div>
                  </button>
                );
              })}
            </div>
          </div>
        )}
      </div>

      {/* ----------------------------------------------------------------- */}
      {/* CARD 2: Date, Flight & Pickup Window */}
      {/* ----------------------------------------------------------------- */}
      <div
        className={`bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden transition-all duration-200 ${
          !selectedAirport ? "opacity-50 pointer-events-none" : ""
        }`}
      >
        <div
          onClick={() => selectedAirport && setActiveStep(2)}
          className={`p-5 flex items-center justify-between cursor-pointer ${
            activeStep === 2 ? "bg-slate-50/50 border-b border-slate-200" : ""
          }`}
        >
          <div className="flex items-center space-x-3">
            <div
              className={`w-8 h-8 rounded-lg flex items-center justify-center font-bold text-sm ${
                selectedFlight
                  ? "bg-emerald-100 text-emerald-700"
                  : "bg-blue-100 text-blue-700"
              }`}
            >
              {selectedFlight ? <Check className="w-4 h-4" /> : "2"}
            </div>
            <div>
              <span className="text-sm font-bold text-slate-900">
                Arrival Flight & Pickup Time
              </span>
              {selectedFlight && activeStep !== 2 && (
                <div className="text-xs text-slate-500">
                  {selectedFlight.airline} {selectedFlight.flight_number} • Lands at{" "}
                  {selectedFlight.arrival_local} • Pickup: {pickupTime}
                </div>
              )}
            </div>
          </div>
          {selectedFlight && activeStep !== 2 && (
            <span className="text-xs font-semibold text-blue-600 flex items-center space-x-1">
              <Edit2 className="w-3.5 h-3.5" />
              <span>Change</span>
            </span>
          )}
        </div>

        {activeStep === 2 && (
          <div className="p-6 space-y-5">
            {/* Date selection (1 to 20 April 2027) */}
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1.5">
                Arrival Date (Event Window: 1 – 20 April 2027)
              </label>
              <input
                type="date"
                min="2027-04-01"
                max="2027-04-20"
                value={selectedDate}
                onChange={(e) => setSelectedDate(e.target.value)}
                className="w-full sm:w-64 px-3.5 py-2 rounded-xl border border-slate-300 text-sm font-semibold text-slate-800 outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
              />
            </div>

            {/* Flights List */}
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-2">
                Available Inbound Flights to {selectedAirport?.code} on {selectedDate}:
              </label>
              {loading ? (
                <div className="text-xs text-slate-500 py-3">Loading flights...</div>
              ) : flights.length === 0 ? (
                <div className="text-xs text-amber-700 bg-amber-50 p-3 rounded-xl border border-amber-200">
                  No scheduled arrival flights found for {selectedAirport?.code} on this date.
                </div>
              ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {flights.map((fl) => {
                    const isSelected = selectedFlight?.flight_id === fl.flight_id;
                    return (
                      <button
                        key={fl.flight_id}
                        type="button"
                        onClick={() => {
                          setSelectedFlight(fl);
                          // Default pickup time is landing + 60 minutes
                          const landingDt = new Date(fl.arrival_local);
                          landingDt.setMinutes(landingDt.getMinutes() + 60);
                          const yr = landingDt.getFullYear();
                          const mo = String(landingDt.getMonth() + 1).padStart(2, "0");
                          const da = String(landingDt.getDate()).padStart(2, "0");
                          const hr = String(landingDt.getHours()).padStart(2, "0");
                          const mi = String(landingDt.getMinutes()).padStart(2, "0");
                          setPickupTime(`${yr}-${mo}-${da}T${hr}:${mi}`);
                        }}
                        className={`p-3.5 rounded-xl border text-left transition-all ${
                          isSelected
                            ? "border-blue-600 bg-blue-50/50 ring-2 ring-blue-500/20"
                            : "border-slate-200 hover:border-blue-300 hover:bg-slate-50"
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <span className="font-bold text-sm text-slate-900">
                            {fl.flight_id} • {fl.airline}
                          </span>
                          <span className="text-xs font-semibold text-slate-600 bg-slate-100 px-2 py-0.5 rounded">
                            {fl.from_airport} → {fl.to_airport}
                          </span>
                        </div>
                        <div className="mt-2 flex items-center justify-between text-xs text-slate-600">
                          <span>
                            Landing: <strong>{fl.arrival_local.substring(11, 16)}</strong> (local)
                          </span>
                          <span>{fl.duration_minutes} min</span>
                        </div>
                      </button>
                    );
                  })}
                </div>
              )}
            </div>

            {/* Pickup time configuration */}
            {selectedFlight && (
              <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-2">
                <div className="flex items-center space-x-2 text-xs font-bold text-slate-800">
                  <Clock className="w-4 h-4 text-blue-600" />
                  <span>Configured Taxi Pickup Time</span>
                </div>
                <div className="flex flex-col sm:flex-row sm:items-center gap-3">
                  <input
                    type="datetime-local"
                    value={pickupTime}
                    onChange={(e) => setPickupTime(e.target.value)}
                    className="px-3 py-2 rounded-lg border border-slate-300 text-sm font-semibold outline-none focus:ring-2 focus:ring-blue-500/20"
                  />
                  <span className="text-xs text-slate-500">
                    Complimentary 60-min wait time after landing ({selectedFlight.arrival_local.substring(11, 16)}) included.
                  </span>
                </div>
              </div>
            )}

            {selectedFlight && (
              <button
                type="button"
                onClick={() => setActiveStep(3)}
                className="inline-flex items-center space-x-1.5 bg-blue-600 text-white text-xs font-semibold px-4 py-2 rounded-xl hover:bg-blue-700 transition-colors"
              >
                <span>Continue to Hotel</span>
                <ChevronRight className="w-4 h-4" />
              </button>
            )}
          </div>
        )}
      </div>

      {/* ----------------------------------------------------------------- */}
      {/* CARD 3: Hotel Selection */}
      {/* ----------------------------------------------------------------- */}
      <div
        className={`bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden transition-all duration-200 ${
          !selectedFlight ? "opacity-50 pointer-events-none" : ""
        }`}
      >
        <div
          onClick={() => selectedFlight && setActiveStep(3)}
          className={`p-5 flex items-center justify-between cursor-pointer ${
            activeStep === 3 ? "bg-slate-50/50 border-b border-slate-200" : ""
          }`}
        >
          <div className="flex items-center space-x-3">
            <div
              className={`w-8 h-8 rounded-lg flex items-center justify-center font-bold text-sm ${
                selectedHotel
                  ? "bg-emerald-100 text-emerald-700"
                  : "bg-blue-100 text-blue-700"
              }`}
            >
              {selectedHotel ? <Check className="w-4 h-4" /> : "3"}
            </div>
            <div>
              <span className="text-sm font-bold text-slate-900">
                Destination Hotel & Resort
              </span>
              {selectedHotel && activeStep !== 3 && (
                <div className="text-xs text-slate-500">
                  {selectedHotel.name} • {selectedHotel.city} ({selectedHotel.area})
                </div>
              )}
            </div>
          </div>
          {selectedHotel && activeStep !== 3 && (
            <span className="text-xs font-semibold text-blue-600 flex items-center space-x-1">
              <Edit2 className="w-3.5 h-3.5" />
              <span>Change</span>
            </span>
          )}
        </div>

        {activeStep === 3 && (
          <div className="p-6 space-y-4">
            <div>
              <label htmlFor="hotel-search" className="block text-xs font-bold text-slate-700 mb-1.5">
                Search hotels served by {selectedAirport?.code}
              </label>
              <input
                id="hotel-search"
                type="search"
                aria-label={`Search hotels served by ${selectedAirport?.code ?? "the airport"}`}
                placeholder="Search name, area, or city (e.g. Ueno, Garden, Tokyo)"
                value={hotelSearch}
                onChange={(e) => setHotelSearch(e.target.value)}
                autoComplete="off"
                className="w-full px-3.5 py-2 rounded-xl border border-slate-300 text-sm font-medium outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
              />
            </div>

            <p className="text-xs text-slate-500">
              {hotelsLoading
                ? "Searching hotels…"
                : hotelSearch.trim()
                  ? `${hotels.length} match${hotels.length === 1 ? "" : "es"}`
                  : `${hotels.length} hotel${hotels.length === 1 ? "" : "s"}`}
            </p>
            {hotelsError && (
              <p className="text-sm text-rose-700" role="alert">
                {hotelsError}
              </p>
            )}
            {selectedHotel &&
              !hotels.some((htl) => htl.hotel_id === selectedHotel.hotel_id) &&
              !hotelsLoading && (
                <p className="text-xs text-slate-600">
                  Selected: {selectedHotel.name}. This search is hiding it.
                </p>
              )}

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-h-60 overflow-y-auto pr-1">
              {!hotelsLoading && hotels.length === 0 && !hotelsError && (
                <p className="text-sm text-slate-600 sm:col-span-2">
                  {hotelSearch.trim()
                    ? `No hotels match “${hotelSearch.trim()}” for ${selectedAirport?.code}.`
                    : "No hotels are served from this airport."}
                </p>
              )}
              {hotels.map((htl) => {
                const isSelected = selectedHotel?.hotel_id === htl.hotel_id;
                return (
                  <button
                    key={htl.hotel_id}
                    type="button"
                    onClick={() => {
                      setSelectedHotel(htl);
                      setActiveStep(4);
                    }}
                    className={`p-3 rounded-xl border text-left transition-all ${
                      isSelected
                        ? "border-blue-600 bg-blue-50/50 ring-2 ring-blue-500/20"
                        : "border-slate-200 hover:border-blue-300 hover:bg-slate-50"
                    }`}
                  >
                    <div className="font-bold text-sm text-slate-900">{htl.name}</div>
                    <div className="text-xs text-slate-500 mt-1 flex items-center justify-between">
                      <span>
                        {htl.city} • <span className="font-semibold text-slate-700">{htl.area}</span>
                      </span>
                      {htl.rating && (
                        <span className="text-emerald-700 font-semibold bg-emerald-50 px-1.5 py-0.5 rounded text-[10px]">
                          ★ {htl.rating}
                        </span>
                      )}
                    </div>
                  </button>
                );
              })}
            </div>
          </div>
        )}
      </div>

      {/* ----------------------------------------------------------------- */}
      {/* CARD 4: Passengers & Luggage */}
      {/* ----------------------------------------------------------------- */}
      <div
        className={`bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden transition-all duration-200 ${
          !selectedHotel ? "opacity-50 pointer-events-none" : ""
        }`}
      >
        <div
          onClick={() => selectedHotel && setActiveStep(4)}
          className={`p-5 flex items-center justify-between cursor-pointer ${
            activeStep === 4 ? "bg-slate-50/50 border-b border-slate-200" : ""
          }`}
        >
          <div className="flex items-center space-x-3">
            <div
              className={`w-8 h-8 rounded-lg flex items-center justify-center font-bold text-sm ${
                activeStep > 4
                  ? "bg-emerald-100 text-emerald-700"
                  : "bg-blue-100 text-blue-700"
              }`}
            >
              {activeStep > 4 ? <Check className="w-4 h-4" /> : "4"}
            </div>
            <div>
              <span className="text-sm font-bold text-slate-900">Passengers & Bags</span>
              {activeStep > 4 && (
                <div className="text-xs text-slate-500">
                  {adults} adults • {childAges.length} children • {largeBags} check-in • {smallBags} cabin
                </div>
              )}
            </div>
          </div>
          {activeStep > 4 && (
            <span className="text-xs font-semibold text-blue-600 flex items-center space-x-1">
              <Edit2 className="w-3.5 h-3.5" />
              <span>Change</span>
            </span>
          )}
        </div>

        {activeStep === 4 && (
          <div className="p-6 space-y-6">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
              {/* Adults Stepper */}
              <div className="bg-slate-50 p-4 rounded-xl border border-slate-200">
                <span className="block text-xs font-bold text-slate-700">Adults (Min. 1)</span>
                <div className="mt-2 flex items-center space-x-3">
                  <button
                    type="button"
                    onClick={() => setAdults((prev) => Math.max(1, prev - 1))}
                    className="w-8 h-8 rounded-lg bg-white border border-slate-300 font-bold hover:bg-slate-100"
                  >
                    -
                  </button>
                  <span className="text-lg font-black text-slate-900 w-8 text-center">
                    {adults}
                  </span>
                  <button
                    type="button"
                    onClick={() => setAdults((prev) => prev + 1)}
                    className="w-8 h-8 rounded-lg bg-white border border-slate-300 font-bold hover:bg-slate-100"
                  >
                    +
                  </button>
                </div>
              </div>

              {/* Children Stepper & Ages */}
              <div className="bg-slate-50 p-4 rounded-xl border border-slate-200">
                <span className="block text-xs font-bold text-slate-700">
                  Children (Ages 0 to 17)
                </span>
                <div className="mt-2 flex items-center space-x-3">
                  <button
                    type="button"
                    onClick={() => setChildAges((prev) => prev.slice(0, -1))}
                    className="w-8 h-8 rounded-lg bg-white border border-slate-300 font-bold hover:bg-slate-100"
                  >
                    -
                  </button>
                  <span className="text-lg font-black text-slate-900 w-8 text-center">
                    {childAges.length}
                  </span>
                  <button
                    type="button"
                    onClick={() => setChildAges((prev) => [...prev, 6])}
                    className="w-8 h-8 rounded-lg bg-white border border-slate-300 font-bold hover:bg-slate-100"
                  >
                    +
                  </button>
                </div>
                {/* Child age chips */}
                {childAges.length > 0 && (
                  <div className="mt-3 flex flex-wrap gap-2">
                    {childAges.map((age, idx) => (
                      <div key={idx} className="flex items-center space-x-1 bg-white px-2 py-1 rounded-lg border text-xs">
                        <span className="text-slate-500">Child #{idx + 1}:</span>
                        <input
                          type="number"
                          min="0"
                          max="17"
                          value={age}
                          onChange={(e) => {
                            const newAge = parseInt(e.target.value, 10) || 0;
                            setChildAges((prev) => prev.map((a, i) => (i === idx ? newAge : a)));
                          }}
                          className="w-12 px-1 text-center font-bold text-blue-700 outline-none"
                        />
                        <span className="text-[10px] text-slate-400">yr</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Large Bags */}
              <div className="bg-slate-50 p-4 rounded-xl border border-slate-200">
                <span className="block text-xs font-bold text-slate-700">
                  Large Bags (Check-in luggage)
                </span>
                <div className="mt-2 flex items-center space-x-3">
                  <button
                    type="button"
                    onClick={() => setLargeBags((prev) => Math.max(0, prev - 1))}
                    className="w-8 h-8 rounded-lg bg-white border border-slate-300 font-bold hover:bg-slate-100"
                  >
                    -
                  </button>
                  <span className="text-lg font-black text-slate-900 w-8 text-center">
                    {largeBags}
                  </span>
                  <button
                    type="button"
                    onClick={() => setLargeBags((prev) => prev + 1)}
                    className="w-8 h-8 rounded-lg bg-white border border-slate-300 font-bold hover:bg-slate-100"
                  >
                    +
                  </button>
                </div>
              </div>

              {/* Small Bags */}
              <div className="bg-slate-50 p-4 rounded-xl border border-slate-200">
                <span className="block text-xs font-bold text-slate-700">
                  Small Bags (Cabin luggage / backpacks)
                </span>
                <div className="mt-2 flex items-center space-x-3">
                  <button
                    type="button"
                    onClick={() => setSmallBags((prev) => Math.max(0, prev - 1))}
                    className="w-8 h-8 rounded-lg bg-white border border-slate-300 font-bold hover:bg-slate-100"
                  >
                    -
                  </button>
                  <span className="text-lg font-black text-slate-900 w-8 text-center">
                    {smallBags}
                  </span>
                  <button
                    type="button"
                    onClick={() => setSmallBags((prev) => prev + 1)}
                    className="w-8 h-8 rounded-lg bg-white border border-slate-300 font-bold hover:bg-slate-100"
                  >
                    +
                  </button>
                </div>
              </div>
            </div>

            <button
              type="button"
              onClick={() => setActiveStep(5)}
              className="inline-flex items-center space-x-1.5 bg-blue-600 text-white text-xs font-semibold px-4 py-2 rounded-xl hover:bg-blue-700 transition-colors"
            >
              <span>Continue to Car Type</span>
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        )}
      </div>

      {/* ----------------------------------------------------------------- */}
      {/* CARD 5: Car Type (G2 Optional Fit) */}
      {/* ----------------------------------------------------------------- */}
      <div
        className={`bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden transition-all duration-200 ${
          activeStep < 5 ? "opacity-50 pointer-events-none" : ""
        }`}
      >
        <div
          onClick={() => activeStep >= 5 && setActiveStep(5)}
          className={`p-5 flex items-center justify-between cursor-pointer ${
            activeStep === 5 ? "bg-slate-50/50 border-b border-slate-200" : ""
          }`}
        >
          <div className="flex items-center space-x-3">
            <div
              className={`w-8 h-8 rounded-lg flex items-center justify-center font-bold text-sm ${
                activeStep > 5
                  ? "bg-emerald-100 text-emerald-700"
                  : "bg-blue-100 text-blue-700"
              }`}
            >
              {activeStep > 5 ? <Check className="w-4 h-4" /> : "5"}
            </div>
            <div>
              <span className="text-sm font-bold text-slate-900">
                Preferred Car Type (Optional)
              </span>
              {activeStep > 5 && (
                <div className="text-xs text-slate-500">
                  {selectedCarType ? selectedCarType : "Any suitable type"}
                </div>
              )}
            </div>
          </div>
          {activeStep > 5 && (
            <span className="text-xs font-semibold text-blue-600 flex items-center space-x-1">
              <Edit2 className="w-3.5 h-3.5" />
              <span>Change</span>
            </span>
          )}
        </div>

        {activeStep === 5 && (
          <div className="p-6 space-y-4">
            <p className="text-xs text-slate-500">
              Only vehicle types with capacity for your {adults + childAges.length} passengers and{" "}
              {largeBags + smallBags} bags are enabled:
            </p>

            <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
              {/* Option: Any */}
              <button
                type="button"
                onClick={() => {
                  setSelectedCarType(null);
                  setActiveStep(6);
                }}
                className={`p-3 rounded-xl border text-center transition-all ${
                  selectedCarType === null
                    ? "border-blue-600 bg-blue-50/60 ring-2 ring-blue-500/20 font-bold text-blue-700"
                    : "border-slate-200 hover:border-slate-300 text-slate-700"
                }`}
              >
                <div className="text-sm">Any</div>
                <div className="text-[10px] text-slate-400 mt-0.5">Flexible</div>
              </button>

              {["HATCHBACK", "SEDAN", "SUV", "BUS"].map((type) => {
                const suitable = suitableCarTypes.find((s) => s.type === type);
                const isSelected = selectedCarType === type;
                const disabled = !suitable;

                return (
                  <button
                    key={type}
                    type="button"
                    disabled={disabled}
                    onClick={() => {
                      setSelectedCarType(type);
                      setActiveStep(6);
                    }}
                    className={`p-3 rounded-xl border text-center transition-all ${
                      disabled
                        ? "border-slate-100 bg-slate-50 opacity-40 cursor-not-allowed text-slate-400"
                        : isSelected
                        ? "border-blue-600 bg-blue-50/60 ring-2 ring-blue-500/20 font-bold text-blue-700"
                        : "border-slate-200 hover:border-blue-300 text-slate-700"
                    }`}
                  >
                    <div className="text-xs font-bold uppercase">{type}</div>
                    <div className="text-[10px] text-slate-500 mt-0.5">
                      {disabled ? "Too small" : `${suitable?.available_fleet_count} available`}
                    </div>
                  </button>
                );
              })}
            </div>
          </div>
        )}
      </div>

      {/* ----------------------------------------------------------------- */}
      {/* CARD 6: Target Fare */}
      {/* ----------------------------------------------------------------- */}
      <div
        className={`bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden transition-all duration-200 ${
          activeStep < 6 ? "opacity-50 pointer-events-none" : ""
        }`}
      >
        <div
          onClick={() => activeStep >= 6 && setActiveStep(6)}
          className={`p-5 flex items-center justify-between cursor-pointer ${
            activeStep === 6 ? "bg-slate-50/50 border-b border-slate-200" : ""
          }`}
        >
          <div className="flex items-center space-x-3">
            <div
              className={`w-8 h-8 rounded-lg flex items-center justify-center font-bold text-sm ${
                priceInr > 0
                  ? "bg-emerald-100 text-emerald-700"
                  : "bg-blue-100 text-blue-700"
              }`}
            >
              {priceInr > 0 ? <Check className="w-4 h-4" /> : "6"}
            </div>
            <div>
              <span className="text-sm font-bold text-slate-900">
                Your Target Fare
              </span>
              {priceInr > 0 && activeStep !== 6 && (
                <div className="text-xs text-slate-500">
                  {formatINR(priceInr)} • Suggested: {formatINR(quote?.price_min_inr || 0)} –{" "}
                  {formatINR(quote?.price_max_inr || 0)}
                </div>
              )}
            </div>
          </div>
          {priceInr > 0 && activeStep !== 6 && (
            <span className="text-xs font-semibold text-blue-600 flex items-center space-x-1">
              <Edit2 className="w-3.5 h-3.5" />
              <span>Change</span>
            </span>
          )}
        </div>

        {activeStep === 6 && quote && (
          <div className="p-6 space-y-4">
            <div className="text-xs text-slate-500 bg-slate-50 p-3 rounded-xl border border-slate-200">
              Estimated drive: <strong>{quote.drive_minutes} mins</strong> ({quote.distance_km} km) from{" "}
              {quote.airport} to {quote.city} ({quote.area}).
            </div>

            <PriceRangeBar
              minPrice={quote.price_min_inr}
              maxPrice={quote.price_max_inr}
              userPrice={priceInr}
              onChangePrice={setPriceInr}
            />

            <button
              type="button"
              onClick={() => setActiveStep(7)}
              className="inline-flex items-center space-x-1.5 bg-blue-600 text-white text-xs font-semibold px-4 py-2 rounded-xl hover:bg-blue-700 transition-colors"
            >
              <span>Review Request</span>
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        )}
      </div>

      {/* ----------------------------------------------------------------- */}
      {/* CARD 7: Review & Post */}
      {/* ----------------------------------------------------------------- */}
      {activeStep === 7 && quote && selectedFlight && selectedHotel && (
        <div className="bg-white rounded-2xl border border-blue-200 shadow-md p-6 space-y-6">
          <div className="flex items-center justify-between border-b border-slate-100 pb-4">
            <div>
              <h2 className="text-lg font-bold text-slate-900">Review & Post Ride Request</h2>
              <p className="text-xs text-slate-500">
                Confirm your ride details before publishing to airport taxi suppliers.
              </p>
            </div>
            <span className="text-xl font-black text-blue-700">{formatINR(priceInr)}</span>
          </div>

          {/* Traveler Name Field */}
          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1">
              Traveler / Party Name (Optional)
            </label>
            <input
              type="text"
              placeholder="e.g. John Doe / Family"
              value={travelerName}
              onChange={(e) => setTravelerName(e.target.value)}
              className="w-full sm:w-80 px-3.5 py-2 rounded-xl border border-slate-300 text-sm outline-none focus:ring-2 focus:ring-blue-500/20"
            />
          </div>

          {/* Summary Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs bg-slate-50 p-4 rounded-xl border border-slate-200">
            <div>
              <span className="text-slate-400 block font-semibold">Route</span>
              <span className="font-bold text-slate-800">
                {selectedAirport?.code} → {selectedHotel.area}
              </span>
            </div>
            <div>
              <span className="text-slate-400 block font-semibold">Flight</span>
              <span className="font-bold text-slate-800">{selectedFlight.flight_id}</span>
            </div>
            <div>
              <span className="text-slate-400 block font-semibold">Pickup Time</span>
              <span className="font-bold text-slate-800">{pickupTime}</span>
            </div>
            <div>
              <span className="text-slate-400 block font-semibold">Party</span>
              <span className="font-bold text-slate-800">
                {adults + childAges.length} pax ({largeBags}L / {smallBags}S)
              </span>
            </div>
          </div>

          <div className="flex items-center justify-end space-x-3 pt-2">
            <button
              type="button"
              disabled={submitting}
              onClick={handleSubmit}
              className="inline-flex items-center space-x-2 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white font-bold text-sm px-6 py-3 rounded-xl shadow-lg shadow-blue-500/25 transition-all hover:scale-[1.01] disabled:opacity-50"
            >
              <span>{submitting ? "Publishing Request..." : "Post Ride Request"}</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
