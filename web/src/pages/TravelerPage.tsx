import React, { useEffect, useState } from "react";
import {
  PlusCircle,
  ListFilter,
  Search,
  ArrowRight,
} from "lucide-react";
import { RequestBuilder } from "../features/traveler/RequestBuilder";
import { RequestDetailView } from "../features/traveler/RequestDetailView";
import { BookingSummaryView } from "../features/booking/BookingSummaryView";
import { RideRequest, fetchRequests } from "../api/client";
import { formatINR, formatAirportTime } from "../lib/formatters";

interface TravelerPageProps {
  onSwitchToSupplier?: () => void;
}

export const TravelerPage: React.FC<TravelerPageProps> = ({
  onSwitchToSupplier,
}) => {
  const [activeTab, setActiveTab] = useState<"builder" | "list">("builder");
  const [activeRequest, setActiveRequest] = useState<RideRequest | null>(null);
  const [bookingLookupNumber, setBookingLookupNumber] = useState<string | null>(null);
  const [bookingSearchInput, setBookingSearchInput] = useState<string>("");

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

  useEffect(() => {
    loadRequests();
  }, []);

  // Handle viewing a specific booking number
  if (bookingLookupNumber) {
    return (
      <BookingSummaryView
        bookingNumber={bookingLookupNumber}
        onBackToSearch={() => setBookingLookupNumber(null)}
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
        }}
        onSwitchToSupplier={onSwitchToSupplier}
      />
    );
  }

  return (
    <div className="max-w-5xl mx-auto py-6 px-4 sm:px-6 space-y-6">
      {/* Top Traveler Navigation Sub-header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-4 rounded-2xl border border-slate-200 shadow-sm">
        {/* Tab switchers */}
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setActiveTab("builder")}
            className={`flex items-center space-x-2 px-4 py-2 rounded-xl text-xs font-bold transition-all ${
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
              setActiveTab("list");
              loadRequests();
            }}
            className={`flex items-center space-x-2 px-4 py-2 rounded-xl text-xs font-bold transition-all ${
              activeTab === "list"
                ? "bg-blue-600 text-white shadow-sm"
                : "text-slate-600 hover:bg-slate-100"
            }`}
          >
            <ListFilter className="w-4 h-4" />
            <span>Active Itineraries</span>
            <span
              className={`px-2 py-0.5 rounded-full text-[10px] font-black ${
                activeTab === "list"
                  ? "bg-white/20 text-white"
                  : "bg-slate-200 text-slate-700"
              }`}
            >
              {requestsList.length}
            </span>
          </button>
        </div>

        {/* 10-digit booking lookup */}
        <form
          onSubmit={(e) => {
            e.preventDefault();
            const trimmed = bookingSearchInput.trim();
            if (trimmed.length === 10) {
              setBookingLookupNumber(trimmed);
            }
          }}
          className="flex items-center space-x-2"
        >
          <div className="relative">
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Find 10-digit Booking ID"
              value={bookingSearchInput}
              onChange={(e) => setBookingSearchInput(e.target.value)}
              className="pl-8 pr-3 py-1.5 text-xs font-semibold rounded-xl border border-slate-300 outline-none focus:border-blue-500 w-56 font-mono"
              maxLength={10}
            />
          </div>
          <button
            type="submit"
            disabled={bookingSearchInput.trim().length !== 10}
            className="px-3 py-1.5 bg-slate-900 hover:bg-slate-800 disabled:opacity-40 text-white font-bold text-xs rounded-xl transition-all"
          >
            Find
          </button>
        </form>
      </div>

      {/* Main Body */}
      {activeTab === "builder" ? (
        <RequestBuilder
          onRequestCreated={(newReq) => {
            setActiveRequest(newReq);
            loadRequests();
          }}
        />
      ) : (
        /* Requests List View */
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-bold text-slate-900">
                Active Airport Rides ({requestsList.length})
              </h2>
              <p className="text-xs text-slate-500">
                Select any itinerary to view incoming chauffeur offers and status.
              </p>
            </div>
            <button
              onClick={loadRequests}
              disabled={loadingRequests}
              className="text-xs font-bold text-blue-600 hover:text-blue-800"
            >
              {loadingRequests ? "Refreshing..." : "Refresh"}
            </button>
          </div>

          {loadingRequests ? (
            <div className="p-8 text-center text-xs text-slate-500">
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
