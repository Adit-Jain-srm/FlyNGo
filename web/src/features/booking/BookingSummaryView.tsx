import React, { useEffect, useState } from "react";
import {
  CheckCircle2,
  Copy,
  Check,
  Plane,
  Building,
  Car,
  AlertCircle,
  RefreshCw,
  Send,
  X,
  Star,
} from "lucide-react";
import {
  Booking,
  ChangeRequest,
  Flight,
  fetchBooking,
  fetchBookingChanges,
  requestFlightChange,
  fetchFlights,
  ApiError,
  ApiRuleError,
} from "../../api/client";
import { formatINR, formatAirportTime } from "../../lib/formatters";
import { RuleErrorAlert } from "../../components/common/RuleErrorAlert";

function addMinutesLocal(localIso: string, minutes: number): string {
  const [date, time] = localIso.slice(0, 16).split("T");
  const [year, month, day] = date.split("-").map(Number);
  const [hour, minute] = time.split(":").map(Number);
  const utc = new Date(Date.UTC(year, month - 1, day, hour, minute + minutes));
  const pad = (value: number) => String(value).padStart(2, "0");
  return `${utc.getUTCFullYear()}-${pad(utc.getUTCMonth() + 1)}-${pad(utc.getUTCDate())}T${pad(utc.getUTCHours())}:${pad(utc.getUTCMinutes())}`;
}

interface BookingSummaryViewProps {
  bookingNumber: string;
  onBackToSearch?: () => void;
}

export const BookingSummaryView: React.FC<BookingSummaryViewProps> = ({
  bookingNumber,
  onBackToSearch,
}) => {
  const [booking, setBooking] = useState<Booking | null>(null);
  const [changes, setChanges] = useState<ChangeRequest[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [copied, setCopied] = useState<boolean>(false);

  // Change modal state
  const [showChangeModal, setShowChangeModal] = useState<boolean>(false);
  const [flights, setFlights] = useState<Flight[]>([]);
  const [changeDate, setChangeDate] = useState<string>("");
  const [selectedFlightId, setSelectedFlightId] = useState<string>("");
  const [newPickupLocal, setNewPickupLocal] = useState<string>("");
  const [submittingChange, setSubmittingChange] = useState<boolean>(false);
  const [changeError, setChangeError] = useState<ApiRuleError | string | null>(null);

  const loadBookingData = async () => {
    try {
      setLoading(true);
      const [bData, cData] = await Promise.all([
        fetchBooking(bookingNumber),
        fetchBookingChanges(bookingNumber),
      ]);
      setBooking(bData);
      setChanges(cData);
      if (bData.arrival_local) {
        setChangeDate(bData.arrival_local.slice(0, 10));
      }
    } catch (err) {
      console.error("Error loading booking:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadBookingData();
  }, [bookingNumber]);

  // Load flights for change modal when date changes
  useEffect(() => {
    if (showChangeModal && booking && changeDate) {
      fetchFlights(booking.airport_code || "", changeDate)
        .then((data) => {
          setFlights(data);
        })
        .catch(console.error);
    }
  }, [showChangeModal, changeDate, booking?.airport_code]);

  const handleFlightSelect = (fId: string) => {
    setSelectedFlightId(fId);
    if (!fId) {
      setNewPickupLocal(booking?.pickup_local?.slice(0, 16) ?? "");
      return;
    }
    const fl = flights.find((f) => f.flight_id === fId);
    if (fl?.arrival_local) {
      setNewPickupLocal(addMinutesLocal(fl.arrival_local, 60));
    }
  };

  const handleCopyBooking = () => {
    navigator.clipboard.writeText(bookingNumber);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const openChangeModal = () => {
    setSelectedFlightId("");
    setNewPickupLocal(booking?.pickup_local?.slice(0, 16) ?? "");
    setChangeError(null);
    setShowChangeModal(true);
  };

  const handleSubmitChange = async () => {
    if (!booking) return;
    const flightChanged = selectedFlightId !== "" && selectedFlightId !== booking.flight_id;
    const currentPickup = booking.pickup_local.slice(0, 16);
    const pickupChanged = newPickupLocal !== "" && newPickupLocal !== currentPickup;
    if (!flightChanged && !pickupChanged) return;

    setSubmittingChange(true);
    setChangeError(null);

    try {
      await requestFlightChange(bookingNumber, {
        ...(flightChanged ? { new_flight_id: selectedFlightId } : {}),
        ...(pickupChanged ? { new_pickup_local: newPickupLocal } : {}),
      });
      setShowChangeModal(false);
      loadBookingData();
    } catch (err: any) {
      if (err instanceof ApiError && err.data) {
        setChangeError(err.data as ApiRuleError);
      } else {
        setChangeError(err.message || "Failed to submit flight change request.");
      }
    } finally {
      setSubmittingChange(false);
    }
  };

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto py-16 px-4 text-center text-slate-500">
        <RefreshCw className="w-8 h-8 animate-spin mx-auto text-blue-600 mb-3" />
        <p className="font-semibold text-sm">Loading booking details...</p>
      </div>
    );
  }

  if (!booking) {
    return (
      <div className="max-w-md mx-auto py-16 px-4 text-center space-y-4">
        <AlertCircle className="w-12 h-12 text-rose-500 mx-auto" />
        <h2 className="text-xl font-bold text-slate-900">Booking Not Found</h2>
        <p className="text-xs text-slate-500">
          No confirmed booking was found matching booking number <strong>{bookingNumber}</strong>.
        </p>
        {onBackToSearch && (
          <button
            onClick={onBackToSearch}
            className="text-xs font-bold text-blue-600 hover:text-blue-800"
          >
            ← Back to Search
          </button>
        )}
      </div>
    );
  }

  const hasWaitingChange = changes.some((c) => c.status === "WAITING");

  return (
    <div className="max-w-4xl mx-auto py-8 px-4 sm:px-6 space-y-6">
      {/* Success Confirmation Header */}
      <div className="bg-gradient-to-r from-emerald-600 to-teal-700 rounded-3xl p-6 sm:p-8 text-white shadow-xl flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div className="space-y-2">
          <div className="inline-flex items-center space-x-2 bg-white/20 backdrop-blur-md px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider">
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>Booking Confirmed</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-black tracking-tight">Your Airport Ride is Locked</h1>
          <p className="text-xs sm:text-sm text-emerald-100 max-w-lg">
            A dedicated driver from <strong>{booking.supplier_name}</strong> will meet you at{" "}
            {booking.airport_code} terminal exit.
          </p>
        </div>

        {/* 10-Digit Booking Badge */}
        <div className="bg-white/10 backdrop-blur-md p-4 rounded-2xl border border-white/20 flex flex-col items-end">
          <span className="text-[11px] uppercase tracking-wider text-emerald-200 font-bold">
            10-Digit Booking ID
          </span>
          <div className="flex items-center space-x-2 mt-1">
            <span className="text-2xl sm:text-3xl font-mono font-black tracking-widest">
              {booking.booking_number}
            </span>
            <button
              onClick={handleCopyBooking}
              className="p-2 rounded-xl bg-white/20 hover:bg-white/30 transition-colors"
              title="Copy Booking Number"
            >
              {copied ? <Check className="w-4 h-4 text-emerald-300" /> : <Copy className="w-4 h-4" />}
            </button>
          </div>
        </div>
      </div>

      {/* Main Details Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Journey Card */}
        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <div className="flex items-center space-x-2">
              <Plane className="w-4 h-4 text-blue-600" />
              <h2 className="text-sm font-bold text-slate-900">Flight & Pickup</h2>
            </div>
            <span className="text-xs font-bold text-slate-500">{booking.airport_code} Airport</span>
          </div>

          <div className="space-y-3 text-xs">
            <div>
              <span className="text-slate-400 block font-semibold">Arrival Flight</span>
              <span className="text-sm font-black text-slate-900">
                {booking.airline} • {booking.flight_number || booking.flight_id}
              </span>
              <span className="text-slate-500 block">
                Landing: {formatAirportTime(booking.arrival_local || "", booking.airport_code || "")}
              </span>
            </div>

            <div>
              <span className="text-slate-400 block font-semibold">Scheduled Taxi Pickup</span>
              <span className="text-base font-black text-indigo-600">
                {formatAirportTime(booking.pickup_local, booking.airport_code || "")}
              </span>
              <span className="text-slate-500 block">
                (Estimated drive: {booking.drive_minutes} mins • {booking.distance_km} km)
              </span>
            </div>
          </div>
        </div>

        {/* Destination & Hotel Card */}
        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <div className="flex items-center space-x-2">
              <Building className="w-4 h-4 text-indigo-600" />
              <h2 className="text-sm font-bold text-slate-900">Hotel Destination</h2>
            </div>
            <span className="text-xs font-bold text-slate-500">{booking.city}</span>
          </div>

          <div className="space-y-3 text-xs">
            <div>
              <span className="text-slate-400 block font-semibold">Hotel Property</span>
              <span className="text-sm font-black text-slate-900">{booking.hotel_name}</span>
              <span className="text-slate-500 block">
                {booking.city} ({booking.area})
              </span>
            </div>

            <div>
              <span className="text-slate-400 block font-semibold">Traveler Details</span>
              <span className="text-xs font-bold text-slate-800">
                {booking.traveler_name || "Traveler"} • {booking.passengers} passengers
              </span>
              <span className="text-slate-500 block">
                {booking.large_bags} large bags • {booking.small_bags} small bags
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Taxi Company & Vehicle Card */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-5">
        <div className="flex items-center space-x-4">
          <div className="w-12 h-12 rounded-2xl bg-indigo-50 text-indigo-600 flex items-center justify-center font-bold">
            <Car className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-sm font-black text-slate-900">{booking.supplier_name}</span>
              {booking.supplier_rating && (
                <span className="flex items-center space-x-1 text-xs font-semibold text-amber-700 bg-amber-50 px-2 py-0.5 rounded-full border border-amber-200">
                  <Star className="w-3 h-3 fill-amber-400 text-amber-500" />
                  <span>{booking.supplier_rating}</span>
                </span>
              )}
            </div>
            <div className="text-xs text-slate-500 mt-1">
              Assigned Vehicle: <strong>{booking.vehicle_id}</strong> ({booking.vehicle_type} •{" "}
              {booking.vehicle_seats} seats • {booking.vehicle_large_bags}L/{booking.vehicle_small_bags}S bags)
            </div>
          </div>
        </div>

        <div className="flex items-center space-x-6 border-t md:border-t-0 md:border-l border-slate-100 pt-4 md:pt-0 md:pl-6 justify-between md:justify-end">
          <div>
            <span className="text-xs text-slate-400 block font-semibold">Confirmed Price</span>
            <span className="text-2xl font-black text-slate-900">{formatINR(booking.price_inr)}</span>
          </div>

          {/* Change Flight Button */}
          <button
            onClick={openChangeModal}
            disabled={hasWaitingChange}
            className="inline-flex items-center space-x-2 px-4 py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-white text-xs font-bold shadow-sm transition-all disabled:opacity-50"
          >
            <span>Request Flight Change</span>
          </button>
        </div>
      </div>

      {/* Flight Change History Section */}
      {changes.length > 0 && (
        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm space-y-4">
          <h2 className="text-sm font-bold text-slate-900">Flight Schedule Adjustments</h2>
          <div className="space-y-3">
            {changes.map((c) => (
              <div
                key={c.change_id}
                className="p-4 rounded-xl border border-slate-100 bg-slate-50/50 flex flex-col md:flex-row md:items-center justify-between gap-3 text-xs"
              >
                <div>
                  <div className="flex items-center space-x-2">
                    <span className="font-bold text-slate-900">
                      Change to {c.new_flight_id}
                    </span>
                    <span
                      className={`px-2 py-0.5 rounded-full font-bold text-[10px] ${
                        c.status === "WAITING"
                          ? "bg-amber-100 text-amber-800 border border-amber-200"
                          : c.status === "ACCEPTED"
                          ? "bg-emerald-100 text-emerald-800 border border-emerald-200"
                          : "bg-rose-100 text-rose-800 border border-rose-200"
                      }`}
                    >
                      {c.status}
                    </span>
                  </div>
                  <div className="text-slate-500 mt-1">
                    Requested Pickup: <strong>{formatAirportTime(c.new_pickup_local, booking.airport_code || "")}</strong>
                    {c.reason && <span className="ml-2 italic text-slate-600">({c.reason})</span>}
                  </div>
                </div>

                <div className="text-slate-400 text-[11px]">
                  Submitted {new Date(c.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Flight Change Modal */}
      {showChangeModal && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl border border-slate-200 shadow-2xl max-w-lg w-full p-6 space-y-5 animate-in fade-in-50 zoom-in-95 duration-200">
            <div className="flex items-center justify-between border-b border-slate-100 pb-4">
              <div>
                <h3 className="text-lg font-bold text-slate-900">Change Arrival Flight</h3>
                <span className="text-xs text-slate-500">
                  Select a new flight arriving at {booking.airport_code}
                </span>
              </div>
              <button
                type="button"
                onClick={() => setShowChangeModal(false)}
                className="text-slate-400 hover:text-slate-700 p-1 rounded-lg"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <RuleErrorAlert error={changeError} onDismiss={() => setChangeError(null)} />

            {/* Date Input */}
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">
                New Arrival Date:
              </label>
              <input
                type="date"
                value={changeDate}
                onChange={(e) => setChangeDate(e.target.value)}
                className="w-full px-3 py-2 rounded-xl border border-slate-300 text-xs font-bold"
              />
            </div>

            {/* Flight Select */}
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">
                Select Flight ({flights.length} flights landing at {booking.airport_code}):
              </label>
              <select
                value={selectedFlightId}
                onChange={(e) => handleFlightSelect(e.target.value)}
                className="w-full px-3 py-2.5 rounded-xl border border-slate-300 text-xs font-bold outline-none"
              >
                <option value="">Keep current flight ({booking.flight_id})</option>
                {flights.map((f) => (
                  <option key={f.flight_id} value={f.flight_id}>
                    {f.airline} ({f.flight_number || f.flight_id}) • From {f.from_airport} • Landing {f.arrival_local.slice(11, 16)}
                  </option>
                ))}
              </select>
            </div>

            {/* Pickup Time */}
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">
                Requested Pickup Time (Local Time):
              </label>
              <input
                type="datetime-local"
                value={newPickupLocal}
                onChange={(e) => setNewPickupLocal(e.target.value)}
                className="w-full px-3 py-2 rounded-xl border border-slate-300 text-xs font-bold"
              />
              <span className="text-[11px] text-slate-400 mt-1 block">
                Pickup must be scheduled at least 60 minutes after landing to clear customs.
              </span>
            </div>

            {/* Actions */}
            <div className="flex items-center justify-end space-x-3 pt-3 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setShowChangeModal(false)}
                className="px-4 py-2 text-xs font-semibold text-slate-600"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={
                  submittingChange ||
                  (selectedFlightId === "" && newPickupLocal.slice(0, 16) === booking.pickup_local.slice(0, 16))
                }
                onClick={handleSubmitChange}
                className="inline-flex items-center space-x-2 bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs px-5 py-2.5 rounded-xl shadow-md transition-all disabled:opacity-50"
              >
                <Send className="w-3.5 h-3.5" />
                <span>{submittingChange ? "Submitting..." : "Send Request to Supplier"}</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
