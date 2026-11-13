import React, { useEffect, useState } from "react";
import {
  PlusCircle,
  ListFilter,
  Search,
  ArrowRight,
  CheckCircle2,
  Car,
  Plane,
  Building,
  Clock,
  Star,
  RefreshCw,
} from "lucide-react";
import { RequestBuilder } from "../features/traveler/RequestBuilder";
import { RequestDetailView } from "../features/traveler/RequestDetailView";
import { BookingSummaryView } from "../features/booking/BookingSummaryView";
import {
  RideRequest,
  Booking,
  fetchRequests,
  fetchBookings,
} from "../api/client";
import { formatINR, formatAirportTime } from "../lib/formatters";

interface TravelerPageProps {
  onSwitchToSupplier?: () => void;
}

export const TravelerPage: React.FC<TravelerPageProps> = ({
  onSwitchToSupplier,
}) => {
  const [activeTab, setActiveTab] = useState<"builder" | "bookings" | "requests">("builder");
  const [activeRequest, setActiveRequest] = useState<RideRequest | null>(null);
  const [bookingLookupNumber, setBookingLookupNumber] = useState<string | null>(null);
  const [bookingSearchInput, setBookingSearchInput] = useState<string>("");
  const [searchError, setSearchError] = useState<string | null>(null);

  // Bookings list state
  const [bookingsList, setBookingsList] = useState<Booking[]>([]);
  const [loadingBookings, setLoadingBookings] = useState<boolean>(false);

  // Requests list state
  const [requestsList, setRequestsList] = useState<RideRequest[]>([]);
  const [loadingRequests, setLoadingRequests] = useState<boolean>(false);

  const loadRequests = async () => {
    setLoadingRequests(true);
    try {
      const data = await fetchRequests();
      setRequestsList(data);
    } catch (err) {
      console.error("Error loading requests list:", err);
    } finally {
      setLoadingRequests(false);
    }
  };

  const loadBookings = async () => {
    setLoadingBookings(true);
    try {
      const data = await fetchBookings();
      setBookingsList(data);
    } catch (err) {
      console.error("Error loading bookings list:", err);
    } finally {
      setLoadingBookings(false);
    }
  };

  useEffect(() => {
    loadRequests();
    loadBookings();
  }, []);

  // Handle viewing a specific booking number
  if (bookingLookupNumber) {
    return (
      <BookingSummaryView
        bookingNumber={bookingLookupNumber}
        onBackToSearch={() => {
          setBookingLookupNumber(null);
          loadBookings();
        }}
      />
    );
  }

  // Handle viewing a specific request detail
  if (activeRequest) {
    return (
      <RequestDetailView
        request={activeRequest}
        onBackToBuilder={() => {
          setActiveRequest(null);
          loadRequests();
          loadBookings();
        }}
        onSwitchToSupplier={onSwitchToSupplier}
      />
    );
  }

  const searchQuery = bookingSearchInput.trim().replace(/^#/, "");
  const filteredBookings = bookingsList.filter((b) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      b.booking_number.includes(searchQuery) ||
      b.request_id.toLowerCase().includes(q) ||
      (b.supplier_name && b.supplier_name.toLowerCase().includes(q)) ||
      (b.traveler_name && b.traveler_name.toLowerCase().includes(q)) ||
      (b.flight_number && b.flight_number.toLowerCase().includes(q)) ||
      (b.flight_id && b.flight_id.toLowerCase().includes(q)) ||
      (b.hotel_name && b.hotel_name.toLowerCase().includes(q))
    );
  });

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const query = bookingSearchInput.trim().replace(/^#/, "");
    if (!query) return;

    // 1. Exact match in loaded bookings
    const exact = bookingsList.find((b) => b.booking_number === query);
    if (exact) {
      setSearchError(null);
      setBookingLookupNumber(exact.booking_number);
      return;
    }

    // 2. Single match in filtered results
    if (filteredBookings.length === 1) {
      setSearchError(null);
      setBookingLookupNumber(filteredBookings[0].booking_number);
      return;
    }

    // 3. Exact 10-digit number not in loaded list (fetch from backend)
    if (query.length === 10 && /^\d+$/.test(query)) {
      setSearchError(null);
      setBookingLookupNumber(query);
      return;
    }

    // 4. Multiple matches in list (keep filtered view)
    if (filteredBookings.length > 1) {
      setSearchError(null);
      return;
    }

    setSearchError(`No booking found matching "${bookingSearchInput.trim()}".`);
  };

  return (
    <div className="max-w-5xl mx-auto py-6 px-4 sm:px-6 space-y-6">
      {/* Top Traveler Navigation Sub-header (Clean Tab Switcher) */}
      <div className="flex items-center space-x-2 bg-white p-3 rounded-2xl border border-slate-200 shadow-sm">
        <button
          onClick={() => setActiveTab("builder")}
          className={`flex items-center space-x-2 px-4 py-2.5 rounded-xl text-xs font-bold transition-all ${
            activeTab === "builder"
              ? "bg-blue-600 text-white shadow-sm"
              : "text-slate-600 hover:bg-slate-100"
          }`}
        >
          <PlusCircle className="w-4 h-4" />
          <span>Book a Transfer</span>
        </button>

        <button
          onClick={() => {
            setActiveTab("bookings");
            loadBookings();
          }}
          className={`flex items-center space-x-2 px-4 py-2.5 rounded-xl text-xs font-bold transition-all ${
            activeTab === "bookings"
              ? "bg-blue-600 text-white shadow-sm"
              : "text-slate-600 hover:bg-slate-100"
          }`}
        >
          <CheckCircle2 className="w-4 h-4" />
          <span>Booked Transfers</span>
          <span
            className={`px-2 py-0.5 rounded-full text-[10px] font-black ${
              activeTab === "bookings"
                ? "bg-white/20 text-white"
                : "bg-slate-200 text-slate-700"
            }`}
          >
            {bookingsList.length}
          </span>
        </button>

        <button
          onClick={() => {
            setActiveTab("requests");
            loadRequests();
          }}
          className={`flex items-center space-x-2 px-4 py-2.5 rounded-xl text-xs font-bold transition-all ${
            activeTab === "requests"
              ? "bg-blue-600 text-white shadow-sm"
              : "text-slate-600 hover:bg-slate-100"
          }`}
        >
          <ListFilter className="w-4 h-4" />
          <span>Active Requests</span>
          <span
            className={`px-2 py-0.5 rounded-full text-[10px] font-black ${
              activeTab === "requests"
                ? "bg-white/20 text-white"
                : "bg-slate-200 text-slate-700"
            }`}
          >
            {requestsList.length}
          </span>
        </button>
      </div>

      {/* ------------------------------------------------------------- */}
      {/* TAB 1: Book a Transfer (Clean Form) */}
      {/* ------------------------------------------------------------- */}
      {activeTab === "builder" && (
        <RequestBuilder
          onRequestCreated={(newReq) => {
            setActiveRequest(newReq);
            loadRequests();
            loadBookings();
          }}
        />
      )}

      {/* ------------------------------------------------------------- */}
      {/* TAB 2: Booked Transfers (With 10-digit ID Lookup & List) */}
      {/* ------------------------------------------------------------- */}
      {activeTab === "bookings" && (
        <div className="space-y-6">
          {/* Booking Lookup Search Banner */}
          <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div>
                <h2 className="text-base font-bold text-slate-900">
                  Find Booking by ID
                </h2>
                <p className="text-xs text-slate-500 mt-0.5">
                  Enter your 10-digit reference (or partial digits) to filter and inspect your confirmed transfer.
                </p>
              </div>

              <form onSubmit={handleSearchSubmit} className="flex items-center space-x-2">
                <div className="relative">
                  <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                  <input
                    type="text"
                    placeholder="Enter Booking ID (e.g. 51803...)"
                    value={bookingSearchInput}
                    onChange={(e) => {
                      setBookingSearchInput(e.target.value);
                      if (searchError) setSearchError(null);
                    }}
                    className="pl-8 pr-8 py-2 text-xs font-semibold rounded-xl border border-slate-300 outline-none focus:border-blue-500 w-64 font-mono"
                    maxLength={15}
                  />
                  {bookingSearchInput && (
                    <button
                      type="button"
                      onClick={() => {
                        setBookingSearchInput("");
                        setSearchError(null);
                      }}
                      className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 text-xs font-bold"
                    >
                      ✕
                    </button>
                  )}
                </div>
                <button
                  type="submit"
                  disabled={!bookingSearchInput.trim()}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-40 text-white font-bold text-xs rounded-xl shadow-sm transition-all"
                >
                  Find
                </button>
              </form>
            </div>

            {searchError && (
              <div className="mt-3 text-xs text-rose-600 font-semibold">
                {searchError}
              </div>
            )}
          </div>

          {/* Bookings List Header */}
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div>
                <h2 className="text-lg font-bold text-slate-900">
                  Confirmed Bookings ({filteredBookings.length})
                </h2>
                <p className="text-xs text-slate-500">
                  {searchQuery ? `Filtered by "${bookingSearchInput.trim()}"` : "Your locked airport transfer rides with verified suppliers."}
                </p>
              </div>
              {searchQuery && (
                <button
                  onClick={() => setBookingSearchInput("")}
                  className="text-xs text-blue-600 hover:underline font-semibold"
                >
                  Reset filter
                </button>
              )}
            </div>
            <button
              onClick={loadBookings}
              disabled={loadingBookings}
              className="inline-flex items-center space-x-1 text-xs font-bold text-blue-600 hover:text-blue-800"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loadingBookings ? "animate-spin" : ""}`} />
              <span>{loadingBookings ? "Refreshing..." : "Refresh"}</span>
            </button>
          </div>

          {/* Bookings Cards Grid */}
          {loadingBookings ? (
            <div className="p-8 text-center text-xs text-slate-500 bg-white rounded-2xl border border-slate-200">
              Loading bookings...
            </div>
          ) : filteredBookings.length === 0 ? (
            <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-10 text-center space-y-3">
              <div className="w-12 h-12 rounded-full bg-emerald-50 text-emerald-600 mx-auto flex items-center justify-center font-bold">
                <CheckCircle2 className="w-6 h-6" />
              </div>
              <h3 className="text-sm font-bold text-slate-800">
                {searchQuery ? "No Bookings Matching Your Search" : "No Confirmed Bookings Yet"}
              </h3>
              <p className="text-xs text-slate-500 max-w-sm mx-auto">
                {searchQuery
                  ? `No booking found matching "${bookingSearchInput.trim()}". Try entering the full 10-digit number or reset the filter.`
                  : "Once a supplier offers a quote and you book it, your locked ride with driver details will appear here."}
              </p>
              {searchQuery ? (
                <button
                  onClick={() => setBookingSearchInput("")}
                  className="inline-flex items-center space-x-1.5 text-xs font-bold text-blue-600 hover:underline pt-2"
                >
                  <span>Clear Search Filter</span>
                </button>
              ) : (
                <button
                  onClick={() => setActiveTab("builder")}
                  className="inline-flex items-center space-x-1.5 text-xs font-bold text-blue-600 hover:underline pt-2"
                >
                  <span>Book your first airport transfer →</span>
                </button>
              )}
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-4">
              {filteredBookings.map((b) => (
                <div
                  key={b.booking_number}
                  className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm hover:border-emerald-400 hover:shadow-md transition-all flex flex-col md:flex-row md:items-center justify-between gap-5"
                >
                  <div className="space-y-2">
                    <div className="flex items-center space-x-2.5">
                      <span className="font-mono text-base font-black text-slate-900 tracking-wider">
                        #{b.booking_number}
                      </span>
                      <span className="text-[10px] font-black uppercase px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
                        {b.status}
                      </span>
                      <span className="text-xs font-bold px-2 py-0.5 rounded-md bg-blue-50 text-blue-700 border border-blue-200">
                        {b.airport_code} → {b.area}
                      </span>
                    </div>

                    <div className="text-xs text-slate-600 space-y-1">
                      <div className="flex items-center space-x-2">
                        <Building className="w-3.5 h-3.5 text-slate-400" />
                        <span>
                          Destination: <strong>{b.hotel_name || b.hotel_id}</strong> ({b.city})
                        </span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Plane className="w-3.5 h-3.5 text-slate-400" />
                        <span>
                          Flight: <strong>{b.airline} {b.flight_number || b.flight_id}</strong> • Landing:{" "}
                          {formatAirportTime(b.arrival_local || "", b.airport_code || "")}
                        </span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Clock className="w-3.5 h-3.5 text-slate-400" />
                        <span>
                          Pickup: <strong>{formatAirportTime(b.pickup_local, b.airport_code || "")}</strong>
                        </span>
                      </div>
                      <div className="flex items-center space-x-2 text-slate-500 pt-0.5">
                        <Car className="w-3.5 h-3.5 text-indigo-500" />
                        <span>
                          Supplier: <strong>{b.supplier_name}</strong>
                        </span>
                        {b.supplier_rating && (
                          <span className="flex items-center space-x-0.5 text-amber-700 text-[11px] font-bold">
                            <Star className="w-3 h-3 fill-amber-400 text-amber-500" />
                            <span>{b.supplier_rating}</span>
                          </span>
                        )}
                        <span>• Vehicle: <strong>{b.vehicle_id}</strong> ({b.vehicle_type})</span>
                      </div>
                    </div>
                  </div>

                  <div className="flex flex-col md:items-end justify-between space-y-3">
                    <div className="text-left md:text-right">
                      <span className="text-xs text-slate-400 block font-semibold">
                        Locked Fare
                      </span>
                      <span className="text-xl font-black text-emerald-700">
                        {formatINR(b.price_inr)}
                      </span>
                    </div>

                    <button
                      type="button"
                      onClick={() => setBookingLookupNumber(b.booking_number)}
                      className="inline-flex items-center space-x-1.5 px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white font-bold text-xs rounded-xl shadow-sm transition-all"
                    >
                      <span>View Details & Flight Changes</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ------------------------------------------------------------- */}
      {/* TAB 3: Active Requests (Open Bids) */}
      {/* ------------------------------------------------------------- */}
      {activeTab === "requests" && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-bold text-slate-900">
                Active Requests ({requestsList.length})
              </h2>
              <p className="text-xs text-slate-500">
                Select any itinerary to view incoming supplier offers and status.
              </p>
            </div>
            <button
              onClick={loadRequests}
              disabled={loadingRequests}
              className="inline-flex items-center space-x-1 text-xs font-bold text-blue-600 hover:text-blue-800"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loadingRequests ? "animate-spin" : ""}`} />
              <span>{loadingRequests ? "Refreshing..." : "Refresh"}</span>
            </button>
          </div>

          {loadingRequests ? (
            <div className="p-8 text-center text-xs text-slate-500 bg-white rounded-2xl border border-slate-200">
              Loading requests...
            </div>
          ) : requestsList.length === 0 ? (
            <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-8 text-center space-y-2">
              <p className="text-sm font-bold text-slate-800">No requests yet</p>
              <button
                onClick={() => setActiveTab("builder")}
                className="text-xs font-bold text-blue-600 hover:underline"
              >
                Post the first request →
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-4">
              {requestsList.map((req) => (
                <div
                  key={req.request_id}
                  onClick={() => setActiveRequest(req)}
                  className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm hover:border-blue-400 hover:shadow-md transition-all cursor-pointer flex flex-col md:flex-row md:items-center justify-between gap-5"
                >
                  <div className="space-y-2">
                    <div className="flex items-center space-x-2.5">
                      <span className="text-lg font-black text-slate-900">
                        {req.request_id}
                      </span>
                      <span className="text-xs font-bold px-2.5 py-0.5 rounded-full bg-blue-50 text-blue-700 border border-blue-200">
                        {req.airport_code} → {req.area}
                      </span>
                      <span
                        className={`text-[10px] font-black uppercase px-2 py-0.5 rounded-full ${
                          req.status === "BOOKED"
                            ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                            : "bg-blue-50 text-blue-700 border border-blue-200"
                        }`}
                      >
                        {req.status}
                      </span>
                      {req.car_type && (
                        <span className="text-xs font-semibold px-2 py-0.5 rounded-md bg-purple-50 text-purple-700 border border-purple-200">
                          {req.car_type} preferred
                        </span>
                      )}
                    </div>

                    <div className="text-xs text-slate-600 space-y-1">
                      <div>
                        Destination: <strong>{req.hotel_name || req.hotel_id}</strong> ({req.city})
                      </div>
                      <div>
                        Flight: <strong>{req.flight_id}</strong> • Landing:{" "}
                        {formatAirportTime(req.arrival_local || "", req.airport_code)}
                      </div>
                      <div className="flex items-center space-x-3 text-slate-500 pt-0.5">
                        <span>
                          Pickup:{" "}
                          <strong>
                            {formatAirportTime(req.pickup_local, req.airport_code)}
                          </strong>
                        </span>
                        <span>•</span>
                        <span>
                          Party: <strong>{req.passengers} pax</strong> ({req.large_bags}L /{" "}
                          {req.small_bags}S)
                        </span>
                        {req.traveler_name && (
                          <>
                            <span>•</span>
                            <span>Traveler: <strong>{req.traveler_name}</strong></span>
                          </>
                        )}
                      </div>
                    </div>
                  </div>

                  <div className="flex flex-col md:items-end justify-between space-y-3">
                    <div className="text-left md:text-right">
                      <span className="text-xs text-slate-400 block font-semibold">
                        Offered Price
                      </span>
                      <span className="text-xl font-black text-blue-600">
                        {formatINR(req.price_inr)}
                      </span>
                    </div>

                    <div className="inline-flex items-center space-x-1.5 text-xs font-bold text-blue-600 hover:text-blue-800">
                      <span>View Offers</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

