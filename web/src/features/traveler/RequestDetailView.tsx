import React, { useEffect, useState } from "react";
import {
  Plane,
  Clock,
  Building,
  Users,
  ArrowLeft,
  RefreshCw,
  CarFront,
  Star,
  CheckCircle2,
  AlertTriangle,
  Car,
} from "lucide-react";
import {
  RideRequest,
  Offer,
  FunnelBreakdown,
  fetchRequest,
  fetchRequestOffers,
  bookOffer,
  rejectOffer,
  ApiError,
  ApiRuleError,
} from "../../api/client";
import { formatINR, formatAirportTime } from "../../lib/formatters";
import { RuleErrorAlert } from "../../components/common/RuleErrorAlert";
import { BookingSummaryView } from "../booking/BookingSummaryView";

interface RequestDetailViewProps {
  request: RideRequest;
  onBackToBuilder: () => void;
  onSwitchToSupplier?: () => void;
}

export const RequestDetailView: React.FC<RequestDetailViewProps> = ({
  request: initialRequest,
  onBackToBuilder,
  onSwitchToSupplier,
}) => {
  const [request, setRequest] = useState<RideRequest>(initialRequest);
  const [offers, setOffers] = useState<Offer[]>([]);
  const [funnel, setFunnel] = useState<FunnelBreakdown | null>(null);
  const [refreshing, setRefreshing] = useState<boolean>(false);
  const [confirmedBookingNo, setConfirmedBookingNo] = useState<string | null>(null);
  const [bookingOfferId, setBookingOfferId] = useState<number | null>(null);
  const [actionError, setActionError] = useState<ApiRuleError | string | null>(null);

  const loadData = async () => {
    try {
      setRefreshing(true);
      const [reqData, offersData] = await Promise.all([
        fetchRequest(request.request_id),
        fetchRequestOffers(request.request_id),
      ]);
      setRequest(reqData);
      setOffers(offersData.offers);
      setFunnel(offersData.funnel);
    } catch (err) {
      console.error("Error loading offers:", err);
    } finally {
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [request.request_id]);

  const handleBook = async (offerId: number) => {
    setBookingOfferId(offerId);
    setActionError(null);
    try {
      const b = await bookOffer(offerId);
      setConfirmedBookingNo(b.booking_number);
    } catch (err: any) {
      if (err instanceof ApiError && err.data) {
        setActionError(err.data as ApiRuleError);
      } else {
        setActionError(err.message || "Failed to book offer.");
      }
    } finally {
      setBookingOfferId(null);
    }
  };

  const handleReject = async (offerId: number) => {
    try {
      await rejectOffer(offerId);
      loadData();
    } catch (err) {
      console.error("Error rejecting offer:", err);
    }
  };

  if (confirmedBookingNo) {
    return (
      <BookingSummaryView
        bookingNumber={confirmedBookingNo}
        onBackToSearch={onBackToBuilder}
      />
    );
  }

  return (
    <div className="max-w-4xl mx-auto py-8 px-4 sm:px-6 space-y-6">
      {/* Top Navigation */}
      <div className="flex items-center justify-between">
        <button
          onClick={onBackToBuilder}
          className="inline-flex items-center space-x-1.5 text-xs font-semibold text-slate-600 hover:text-slate-900 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Post Another Request</span>
        </button>

        <button
          onClick={loadData}
          disabled={refreshing}
          className="inline-flex items-center space-x-1.5 text-xs font-semibold text-blue-600 hover:text-blue-800 transition-colors"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? "animate-spin" : ""}`} />
          <span>Refresh Offers</span>
        </button>
      </div>

      <RuleErrorAlert error={actionError} onDismiss={() => setActionError(null)} />

      {/* Main Request Banner Card */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-100 pb-5">
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-2xl font-black text-slate-900">{request.request_id}</span>
              <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider ${
                request.status === "BOOKED"
                  ? "bg-blue-50 text-blue-700 border border-blue-200"
                  : "bg-emerald-50 text-emerald-700 border border-emerald-200"
              }`}>
                {request.status}
              </span>
            </div>
            {request.traveler_name && (
              <span className="text-xs text-slate-500 font-medium mt-0.5 block">
                Traveler: {request.traveler_name}
              </span>
            )}
          </div>

          <div className="text-right">
            <span className="text-xs text-slate-400 block font-semibold">Offered Ride Price</span>
            <span className="text-2xl font-black text-blue-600">{formatINR(request.price_inr)}</span>
          </div>
        </div>

        {/* Details Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4 text-xs">
          <div className="bg-slate-50 p-3.5 rounded-xl border border-slate-200 space-y-1">
            <div className="flex items-center space-x-1.5 text-slate-500 font-semibold">
              <Plane className="w-3.5 h-3.5 text-blue-500" />
              <span>Arrival Flight</span>
            </div>
            <div className="font-bold text-slate-900 text-sm">
              {request.flight_id} ({request.airport_code})
            </div>
            <div className="text-slate-500">
              Landing: {formatAirportTime(request.arrival_local, request.airport_code)}
            </div>
          </div>

          <div className="bg-slate-50 p-3.5 rounded-xl border border-slate-200 space-y-1">
            <div className="flex items-center space-x-1.5 text-slate-500 font-semibold">
              <Building className="w-3.5 h-3.5 text-indigo-500" />
              <span>Destination Hotel</span>
            </div>
            <div className="font-bold text-slate-900 text-sm truncate">
              {request.hotel_name || request.hotel_id}
            </div>
            <div className="text-slate-500">
              {request.city} ({request.area})
            </div>
          </div>

          <div className="bg-slate-50 p-3.5 rounded-xl border border-slate-200 space-y-1">
            <div className="flex items-center space-x-1.5 text-slate-500 font-semibold">
              <Clock className="w-3.5 h-3.5 text-amber-500" />
              <span>Scheduled Pickup</span>
            </div>
            <div className="font-bold text-slate-900 text-sm">
              {formatAirportTime(request.pickup_local, request.airport_code)}
            </div>
            <div className="text-slate-500">Local airport time</div>
          </div>

          <div className="bg-slate-50 p-3.5 rounded-xl border border-slate-200 space-y-1">
            <div className="flex items-center space-x-1.5 text-slate-500 font-semibold">
              <Users className="w-3.5 h-3.5 text-emerald-500" />
              <span>Party & Bags</span>
            </div>
            <div className="font-bold text-slate-900 text-sm">
              {request.passengers} passengers
            </div>
            <div className="text-slate-500">
              {request.large_bags} large • {request.small_bags} small
            </div>
          </div>
        </div>
      </div>

      {/* Supplier Offers Section */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 space-y-5">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-base font-bold text-slate-900">
              Incoming Taxi Offers ({offers.length})
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Verified taxi suppliers in {request.airport_code} reviewing this request.
            </p>
          </div>
        </div>

        {offers.length > 0 ? (
          <div className="grid grid-cols-1 gap-4">
            {offers.map((offer) => {
              const isOpen = offer.status === "OPEN";
              return (
                <div
                  key={offer.offer_id}
                  className={`p-5 rounded-2xl border transition-all flex flex-col md:flex-row md:items-center justify-between gap-4 ${
                    offer.status === "BOOKED"
                      ? "border-emerald-300 bg-emerald-50/30"
                      : offer.status === "REJECTED" || offer.status === "NOT_CHOSEN"
                      ? "border-slate-200 bg-slate-50/50 opacity-60"
                      : "border-slate-200 bg-white hover:border-indigo-300 shadow-sm"
                  }`}
                >
                  <div className="flex items-center space-x-4">
                    <div className="w-12 h-12 rounded-2xl bg-indigo-50 text-indigo-600 flex items-center justify-center font-bold">
                      <Car className="w-6 h-6" />
                    </div>
                    <div>
                      <div className="flex items-center space-x-2">
                        <span className="font-black text-slate-900 text-sm">{offer.supplier_name}</span>
                        {offer.supplier_rating && (
                          <span className="flex items-center space-x-1 text-xs font-semibold text-amber-700 bg-amber-50 px-2 py-0.5 rounded-full border border-amber-200">
                            <Star className="w-3 h-3 fill-amber-400 text-amber-500" />
                            <span>{offer.supplier_rating}</span>
                          </span>
                        )}
                        <span className={`text-[10px] font-black uppercase px-2 py-0.5 rounded-full ${
                          offer.status === "OPEN"
                            ? "bg-blue-50 text-blue-700 border border-blue-200"
                            : offer.status === "BOOKED"
                            ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                            : "bg-slate-100 text-slate-500"
                        }`}>
                          {offer.status}
                        </span>
                      </div>

                      <div className="text-xs text-slate-500 mt-1">
                        Vehicle: <strong>{offer.vehicle_id}</strong> ({offer.vehicle_type} • {offer.vehicle_seats} seats • {offer.vehicle_large_bags}L / {offer.vehicle_small_bags}S bags)
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center space-x-5 justify-between md:justify-end">
                    <div className="text-right">
                      <span className="text-xs text-slate-400 block font-semibold">Offer Price</span>
                      <span className="text-xl font-black text-slate-900">{formatINR(offer.price_inr)}</span>
                    </div>

                    {isOpen && (
                      <div className="flex items-center space-x-2">
                        <button
                          type="button"
                          onClick={() => handleReject(offer.offer_id)}
                          className="px-3 py-2 rounded-xl text-xs font-bold text-slate-500 hover:text-slate-800 hover:bg-slate-100 transition-colors"
                        >
                          Reject
                        </button>
                        <button
                          type="button"
                          disabled={bookingOfferId === offer.offer_id}
                          onClick={() => handleBook(offer.offer_id)}
                          className="inline-flex items-center space-x-1.5 px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs shadow-md shadow-emerald-600/20 transition-all disabled:opacity-50"
                        >
                          <CheckCircle2 className="w-3.5 h-3.5" />
                          <span>{bookingOfferId === offer.offer_id ? "Booking..." : "Book Ride"}</span>
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        ) : funnel && !funnel.has_eligible_supplier ? (
          <div className="rounded-2xl border border-amber-200 bg-amber-50/50 p-6 space-y-4">
            <div className="flex items-center space-x-2.5 text-amber-900 font-bold text-sm">
              <AlertTriangle className="w-5 h-5 text-amber-600" />
              <span>Supplier Availability Notice: No Suppliers Currently Match</span>
            </div>

            <p className="text-xs text-amber-800 font-medium">
              {funnel.plain_reason}
            </p>

            <div className="grid grid-cols-2 sm:grid-cols-5 gap-2.5 pt-2">
              <div className="bg-white p-3 rounded-xl border border-amber-200 text-center">
                <span className="text-[10px] uppercase font-bold text-slate-400 block">1. At Airport</span>
                <span className="text-base font-black text-slate-900">{funnel.at_airport_count}</span>
              </div>
              <div className="bg-white p-3 rounded-xl border border-amber-200 text-center">
                <span className="text-[10px] uppercase font-bold text-slate-400 block">2. In Area</span>
                <span className="text-base font-black text-slate-900">{funnel.in_area_count}</span>
              </div>
              <div className="bg-white p-3 rounded-xl border border-amber-200 text-center">
                <span className="text-[10px] uppercase font-bold text-slate-400 block">3. Operating</span>
                <span className="text-base font-black text-slate-900">{funnel.open_at_pickup_count}</span>
              </div>
              <div className="bg-white p-3 rounded-xl border border-amber-200 text-center">
                <span className="text-[10px] uppercase font-bold text-slate-400 block">4. Fits Class</span>
                <span className={`text-base font-black ${funnel.has_fitting_car_count === 0 ? "text-rose-600" : "text-slate-900"}`}>
                  {funnel.has_fitting_car_count}
                </span>
              </div>
              <div className="bg-white p-3 rounded-xl border border-amber-200 text-center">
                <span className="text-[10px] uppercase font-bold text-slate-400 block">5. Free Schedule</span>
                <span className={`text-base font-black ${funnel.has_free_fitting_car_count === 0 ? "text-rose-600" : "text-slate-900"}`}>
                  {funnel.has_free_fitting_car_count}
                </span>
              </div>
            </div>
          </div>
        ) : (
          /* Waiting for offers */
          <div className="rounded-xl border border-dashed border-slate-300 bg-slate-50/70 p-8 text-center space-y-3">
            <div className="w-12 h-12 rounded-full bg-blue-50 text-blue-600 mx-auto flex items-center justify-center">
              <CarFront className="w-6 h-6" />
            </div>
            <div>
              <div className="text-sm font-bold text-slate-800">
                Request Published • Waiting for Supplier Offers
              </div>
              <p className="text-xs text-slate-500 max-w-md mx-auto mt-1">
                Your ride request is active and visible to eligible suppliers operating at {request.airport_code}.
              </p>
            </div>

            {onSwitchToSupplier && (
              <div className="pt-2">
                <button
                  type="button"
                  onClick={onSwitchToSupplier}
                  className="inline-flex items-center space-x-2 text-xs font-semibold px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white shadow-sm transition-colors"
                >
                  <span>Switch to Supplier Portal to Assign Cars</span>
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
