import React, { useEffect, useState, useCallback } from "react";
import {
  Car,
  Building2,
  Clock,
  MapPin,
  CheckCircle2,
  ArrowRight,
  Send,
  X,
  Star,
} from "lucide-react";
import {
  Supplier,
  RideRequest,
  CarAdvisory,
  Offer,
  fetchSuppliers,
  fetchSupplierRequests,
  fetchSupplierCars,
  fetchSupplierOffers,
  fetchSupplierBookings,
  fetchSupplierChanges,
  createOffer,
  acceptChangeRequest,
  rejectChangeRequest,
  ApiError,
  ApiRuleError,
} from "../../api/client";
import { formatINR, formatAirportTime } from "../../lib/formatters";
import { RuleErrorAlert } from "../../components/common/RuleErrorAlert";
import { useLiveSync, emitSyncEvent } from "../../lib/sync";

export const SupplierPortal: React.FC = () => {
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [selectedSupplierId, setSelectedSupplierId] = useState<string>("TX-JP-01"); // Default: Sakura Cabs
  const [activeTab, setActiveTab] = useState<"requests" | "offers" | "bookings" | "changes">("requests");

  // Data states
  const [requests, setRequests] = useState<RideRequest[]>([]);
  const [offers, setOffers] = useState<Offer[]>([]);
  const [bookings, setBookings] = useState<any[]>([]);
  const [changes, setChanges] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  // Assignment Modal State
  const [assignModalRequest, setAssignModalRequest] = useState<RideRequest | null>(null);
  const [supplierCars, setSupplierCars] = useState<CarAdvisory[]>([]);
  const [selectedVehicleId, setSelectedVehicleId] = useState<string | null>(null);
  const [offerPrice, setOfferPrice] = useState<number>(0);
  const [submittingOffer, setSubmittingOffer] = useState<boolean>(false);
  const [offerError, setOfferError] = useState<ApiRuleError | string | null>(null);
  const [offerSuccess, setOfferSuccess] = useState<string | null>(null);

  // Load suppliers list
  useEffect(() => {
    fetchSuppliers().then((data) => {
      setSuppliers(data);
      if (data.length > 0 && !selectedSupplierId) {
        setSelectedSupplierId(data[0].supplier_id);
      }
    });
  }, []);

  // Reload data whenever selected company or tab changes
  const loadCompanyData = useCallback(async (supId: string, showLoading: boolean = false) => {
    if (showLoading) setLoading(true);
    try {
      const [reqsData, offersData, bookingsData, changesData] = await Promise.all([
        fetchSupplierRequests(supId),
        fetchSupplierOffers(supId),
        fetchSupplierBookings(supId),
        fetchSupplierChanges(supId),
      ]);
      setRequests(reqsData);
      setOffers(offersData);
      setBookings(bookingsData);
      setChanges(changesData);
    } catch (err) {
      console.error("Error loading supplier data:", err);
    } finally {
      if (showLoading) setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (selectedSupplierId) {
      loadCompanyData(selectedSupplierId, true);
    }
  }, [selectedSupplierId, loadCompanyData]);

  // Real-time synchronization across portals & tabs
  const refreshCompanyData = useCallback(() => {
    if (selectedSupplierId) {
      loadCompanyData(selectedSupplierId, false);
    }
  }, [selectedSupplierId, loadCompanyData]);

  useLiveSync(refreshCompanyData, 2500);

  // Open Assign Vehicle Modal
  const handleOpenAssignModal = async (req: RideRequest) => {
    setAssignModalRequest(req);
    setSelectedVehicleId(null);
    setOfferPrice(req.price_inr);
    setOfferError(null);
    setOfferSuccess(null);

    try {
      const cars = await fetchSupplierCars(selectedSupplierId, req.request_id);
      setSupplierCars(cars);
      // Auto-select first free fitting car if available
      const freeCar = cars.find((c) => c.badge === "FITS_FREE");
      if (freeCar) {
        setSelectedVehicleId(freeCar.vehicle_id);
      }
    } catch (err) {
      console.error("Error fetching cars:", err);
    }
  };

  // Submit Offer
  const handleSubmitOffer = async () => {
    if (!assignModalRequest || !selectedVehicleId) {
      setOfferError("Please select a vehicle to assign.");
      return;
    }

    setSubmittingOffer(true);
    setOfferError(null);

    try {
      await createOffer(assignModalRequest.request_id, {
        supplier_id: selectedSupplierId,
        vehicle_id: selectedVehicleId,
        price_inr: offerPrice,
      });

      emitSyncEvent("OFFER_CREATED");
      setOfferSuccess(`Vehicle ${selectedVehicleId} successfully assigned for ${formatINR(offerPrice)}!`);
      // Refresh company dashboard
      setTimeout(() => {
        loadCompanyData(selectedSupplierId, false);
        setAssignModalRequest(null);
      }, 1200);
    } catch (err: any) {
      if (err instanceof ApiError && err.data) {
        setOfferError(err.data as ApiRuleError);
      } else {
        setOfferError(err.message || "Failed to assign car.");
      }
    } finally {
      setSubmittingOffer(false);
    }
  };

  const handleAcceptChange = async (changeId: number) => {
    try {
      await acceptChangeRequest(changeId);
      emitSyncEvent("CHANGE_DECIDED");
      loadCompanyData(selectedSupplierId, false);
    } catch (err) {
      console.error("Error accepting change:", err);
    }
  };

  const handleRejectChange = async (changeId: number) => {
    try {
      await rejectChangeRequest(changeId, "Driver unavailable at new pickup time.");
      emitSyncEvent("CHANGE_DECIDED");
      loadCompanyData(selectedSupplierId, false);
    } catch (err) {
      console.error("Error rejecting change:", err);
    }
  };

  const currentSupplier = suppliers.find((s) => s.supplier_id === selectedSupplierId);

  return (
    <div className="max-w-5xl mx-auto py-8 px-4 sm:px-6 space-y-6">
      {/* Supplier Profile Selector Card */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center space-x-4">
          <div className="w-12 h-12 rounded-2xl bg-indigo-50 text-indigo-600 flex items-center justify-center font-bold">
            <Building2 className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-xs font-bold text-indigo-600 uppercase tracking-wider">
                Active Supplier
              </span>
              {currentSupplier?.rating && (
                <span className="flex items-center space-x-1 text-xs font-semibold text-amber-700 bg-amber-50 px-2 py-0.5 rounded-full border border-amber-200">
                  <Star className="w-3 h-3 fill-amber-400 text-amber-500" />
                  <span>{currentSupplier.rating}</span>
                </span>
              )}
            </div>

            <div className="mt-1">
              <select
                value={selectedSupplierId}
                onChange={(e) => setSelectedSupplierId(e.target.value)}
                className="text-xl font-black text-slate-900 bg-transparent outline-none cursor-pointer hover:text-indigo-600 transition-colors"
              >
                {suppliers.map((s) => (
                  <option key={s.supplier_id} value={s.supplier_id}>
                    {s.name} ({s.supplier_id})
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Operating Hours & Airport Coverage */}
        {currentSupplier && (
          <div className="flex flex-wrap items-center gap-4 text-xs text-slate-600 bg-slate-50 px-4 py-2.5 rounded-xl border border-slate-200">
            <div className="flex items-center space-x-1.5">
              <Clock className="w-3.5 h-3.5 text-indigo-600" />
              <span>
                Hours: <strong>{currentSupplier.service_from} – {currentSupplier.service_until}</strong>
              </span>
            </div>
            <div className="flex items-center space-x-1.5">
              <MapPin className="w-3.5 h-3.5 text-blue-600" />
              <span>
                Airports: <strong>{currentSupplier.airports.join(", ")}</strong>
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Navigation Tabs */}
      <div className="flex items-center space-x-2 border-b border-slate-200 pb-2">
        <button
          onClick={() => setActiveTab("requests")}
          className={`flex items-center space-x-2 px-4 py-2 rounded-xl text-xs font-bold transition-all ${
            activeTab === "requests"
              ? "bg-indigo-600 text-white shadow-sm"
              : "text-slate-600 hover:bg-slate-100"
          }`}
        >
          <span>Eligible Requests</span>
          <span className={`px-2 py-0.5 rounded-full text-[10px] font-black ${
            activeTab === "requests" ? "bg-white/20 text-white" : "bg-slate-200 text-slate-700"
          }`}>
            {requests.length}
          </span>
        </button>

        <button
          onClick={() => setActiveTab("offers")}
          className={`flex items-center space-x-2 px-4 py-2 rounded-xl text-xs font-bold transition-all ${
            activeTab === "offers"
              ? "bg-indigo-600 text-white shadow-sm"
              : "text-slate-600 hover:bg-slate-100"
          }`}
        >
          <span>Active Quotes</span>
          <span className={`px-2 py-0.5 rounded-full text-[10px] font-black ${
            activeTab === "offers" ? "bg-white/20 text-white" : "bg-slate-200 text-slate-700"
          }`}>
            {offers.length}
          </span>
        </button>

        <button
          onClick={() => setActiveTab("bookings")}
          className={`flex items-center space-x-2 px-4 py-2 rounded-xl text-xs font-bold transition-all ${
            activeTab === "bookings"
              ? "bg-indigo-600 text-white shadow-sm"
              : "text-slate-600 hover:bg-slate-100"
          }`}
        >
          <span>Confirmed Bookings</span>
          <span className={`px-2 py-0.5 rounded-full text-[10px] font-black ${
            activeTab === "bookings" ? "bg-white/20 text-white" : "bg-slate-200 text-slate-700"
          }`}>
            {bookings.length}
          </span>
        </button>

        <button
          onClick={() => setActiveTab("changes")}
          className={`flex items-center space-x-2 px-4 py-2 rounded-xl text-xs font-bold transition-all ${
            activeTab === "changes"
              ? "bg-indigo-600 text-white shadow-sm"
              : "text-slate-600 hover:bg-slate-100"
          }`}
        >
          <span>Schedule Changes</span>
          <span className={`px-2 py-0.5 rounded-full text-[10px] font-black ${
            activeTab === "changes" ? "bg-white/20 text-white" : "bg-slate-200 text-slate-700"
          }`}>
            {changes.length}
          </span>
        </button>
      </div>

      {/* ------------------------------------------------------------- */}
      {/* TAB 1: Requests You Can Serve (B.2 Query) */}
      {/* ------------------------------------------------------------- */}
      {activeTab === "requests" && (
        <div className="space-y-4">
          {loading ? (
            <div className="p-8 text-center text-xs text-slate-500">Loading eligible requests...</div>
          ) : requests.length === 0 ? (
            <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-8 text-center space-y-2">
              <p className="text-sm font-bold text-slate-800">No Eligible Requests Right Now</p>
              <p className="text-xs text-slate-500 max-w-md mx-auto">
                No active open requests currently match your operating airports, service areas, and fleet schedule.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-4">
              {requests.map((r) => (
                <div
                  key={r.request_id}
                  className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm hover:border-indigo-300 transition-all flex flex-col md:flex-row md:items-center justify-between gap-5"
                >
                  <div className="space-y-2">
                    <div className="flex items-center space-x-2.5">
                      <span className="text-lg font-black text-slate-900">{r.request_id}</span>
                      <span className="text-xs font-bold px-2.5 py-0.5 rounded-full bg-blue-50 text-blue-700 border border-blue-200">
                        {r.airport_code} → {r.area}
                      </span>
                      {r.car_type && (
                        <span className="text-xs font-semibold px-2 py-0.5 rounded-md bg-purple-50 text-purple-700 border border-purple-200">
                          {r.car_type} preferred
                        </span>
                      )}
                    </div>

                    <div className="text-xs text-slate-600 space-y-1">
                      <div>
                        Destination: <strong>{r.hotel_name || r.hotel_id}</strong> ({r.city})
                      </div>
                      <div>
                        Flight: <strong>{r.flight_id}</strong> • Landing: {formatAirportTime(r.arrival_local, r.airport_code)}
                      </div>
                      <div className="flex items-center space-x-3 text-slate-500 pt-0.5">
                        <span>Pickup: <strong>{formatAirportTime(r.pickup_local, r.airport_code)}</strong></span>
                        <span>•</span>
                        <span>Party: <strong>{r.passengers} pax</strong> ({r.large_bags}L / {r.small_bags}S)</span>
                      </div>
                    </div>
                  </div>

                  <div className="flex flex-col md:items-end justify-between space-y-3">
                    <div className="text-left md:text-right">
                      <span className="text-xs text-slate-400 block font-semibold">Traveler's Price</span>
                      <span className="text-xl font-black text-indigo-600">{formatINR(r.price_inr)}</span>
                    </div>

                    <button
                      type="button"
                      onClick={() => handleOpenAssignModal(r)}
                      className="inline-flex items-center space-x-2 bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs px-4 py-2.5 rounded-xl shadow-md shadow-indigo-500/20 transition-all"
                    >
                      <Car className="w-4 h-4" />
                      <span>Assign Vehicle & Offer</span>
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ------------------------------------------------------------- */}
      {/* TAB 2: Your Assigned Offers */}
      {/* ------------------------------------------------------------- */}
      {activeTab === "offers" && (
        <div className="space-y-4">
          {offers.length === 0 ? (
            <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-8 text-center text-xs text-slate-500">
              No offers posted yet by this supplier.
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-3">
              {offers.map((o) => (
                <div key={o.offer_id} className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm flex items-center justify-between">
                  <div>
                    <div className="flex items-center space-x-2">
                      <span className="font-bold text-sm text-slate-900">Offer #{o.offer_id}</span>
                      <span className="text-xs px-2 py-0.5 rounded font-mono font-bold bg-slate-100 text-slate-700">
                        Request: {o.request_id}
                      </span>
                      <span className={`text-xs px-2 py-0.5 rounded-full font-bold ${
                        o.status === "OPEN"
                          ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                          : o.status === "BOOKED"
                          ? "bg-blue-50 text-blue-700 border border-blue-200"
                          : "bg-slate-100 text-slate-600"
                      }`}>
                        {o.status}
                      </span>
                    </div>
                    <div className="text-xs text-slate-500 mt-1">
                      Assigned Vehicle: <strong>{o.vehicle_id}</strong> ({o.vehicle_type} • {o.vehicle_seats} seats)
                    </div>
                  </div>

                  <div className="text-right">
                    <span className="text-xs text-slate-400 block font-semibold">Offer Price</span>
                    <span className="text-lg font-black text-slate-900">{formatINR(o.price_inr)}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ------------------------------------------------------------- */}
      {/* TAB 3: Confirmed Bookings */}
      {/* ------------------------------------------------------------- */}
      {activeTab === "bookings" && (
        <div className="space-y-4">
          {bookings.length === 0 ? (
            <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-8 text-center text-xs text-slate-500">
              No confirmed bookings assigned to {currentSupplier?.name} yet.
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-3">
              {bookings.map((b) => (
                <div
                  key={b.booking_number}
                  className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4"
                >
                  <div className="space-y-1.5">
                    <div className="flex items-center space-x-2.5">
                      <span className="font-mono font-black text-sm text-slate-900 tracking-wider">
                        #{b.booking_number}
                      </span>
                      <span className="text-[10px] font-black uppercase px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
                        {b.status}
                      </span>
                      <span className="text-xs text-slate-500">
                        Vehicle: <strong>{b.vehicle_id}</strong> ({b.vehicle_type})
                      </span>
                    </div>

                    <div className="text-xs text-slate-600">
                      Destination: <strong>{b.city} ({b.area})</strong> • Flight: <strong>{b.flight_number || b.flight_id}</strong>
                    </div>

                    <div className="text-xs text-slate-500">
                      Pickup: <strong>{formatAirportTime(b.pickup_local, b.from_airport || "")}</strong> • Traveler: {b.traveler_name || "Traveler"} ({b.passengers} pax)
                    </div>
                  </div>

                  <div className="text-right">
                    <span className="text-xs text-slate-400 block font-semibold">Locked Price</span>
                    <span className="text-xl font-black text-emerald-700">{formatINR(b.price_inr)}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ------------------------------------------------------------- */}
      {/* TAB 4: Flight Change Requests */}
      {/* ------------------------------------------------------------- */}
      {activeTab === "changes" && (
        <div className="space-y-4">
          {changes.length === 0 ? (
            <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-8 text-center text-xs text-slate-500">
              No flight change requests for {currentSupplier?.name}.
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-3">
              {changes.map((c) => (
                <div
                  key={c.change_id}
                  className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4"
                >
                  <div className="space-y-1.5">
                    <div className="flex items-center space-x-2.5">
                      <span className="font-bold text-sm text-slate-900">
                        Change Request #{c.change_id}
                      </span>
                      <span className="font-mono text-xs font-semibold text-slate-500">
                        Booking: #{c.booking_number}
                      </span>
                      <span
                        className={`text-[10px] font-black uppercase px-2 py-0.5 rounded-full ${
                          c.status === "WAITING"
                            ? "bg-amber-50 text-amber-700 border border-amber-200"
                            : c.status === "ACCEPTED"
                            ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                            : "bg-rose-50 text-rose-700 border border-rose-200"
                        }`}
                      >
                        {c.status}
                      </span>
                    </div>

                    <div className="text-xs text-slate-600">
                      Vehicle: <strong>{c.vehicle_id}</strong> • Route: {c.city} ({c.area})
                    </div>

                    <div className="text-xs text-slate-500 flex flex-wrap items-center gap-2">
                      <span>Old: {c.old_flight_id} ({c.old_pickup_local.slice(11, 16)})</span>
                      <ArrowRight className="w-3 h-3 text-slate-400" />
                      <span className="text-indigo-600 font-bold">New: {c.new_flight_id} ({c.new_pickup_local.slice(11, 16)})</span>
                      {c.reason && <span className="italic text-slate-500">({c.reason})</span>}
                    </div>
                  </div>

                  {c.status === "WAITING" && (
                    <div className="flex items-center space-x-2 pt-2 md:pt-0">
                      <button
                        type="button"
                        onClick={() => handleRejectChange(c.change_id)}
                        className="px-3 py-2 rounded-xl text-xs font-bold text-rose-600 hover:bg-rose-50 border border-rose-200 transition-colors"
                      >
                        Reject
                      </button>
                      <button
                        type="button"
                        onClick={() => handleAcceptChange(c.change_id)}
                        className="px-4 py-2 rounded-xl text-xs font-bold text-white bg-indigo-600 hover:bg-indigo-700 shadow-md shadow-indigo-600/20 transition-all"
                      >
                        Accept Change
                      </button>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ------------------------------------------------------------- */}
      {/* ASSIGN VEHICLE MODAL / SIDE PANEL */}
      {/* ------------------------------------------------------------- */}
      {assignModalRequest && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl border border-slate-200 shadow-2xl max-w-xl w-full p-6 space-y-5 animate-in fade-in-50 zoom-in-95 duration-200">
            {/* Modal Header */}
            <div className="flex items-center justify-between border-b border-slate-100 pb-4">
              <div>
                <h3 className="text-lg font-bold text-slate-900">
                  Assign Vehicle to {assignModalRequest.request_id}
                </h3>
                <span className="text-xs text-slate-500">
                  {assignModalRequest.airport_code} → {assignModalRequest.city} ({assignModalRequest.area}) • {assignModalRequest.passengers} passengers
                </span>
              </div>
              <button
                type="button"
                onClick={() => setAssignModalRequest(null)}
                className="text-slate-400 hover:text-slate-700 p-1 rounded-lg"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Error / Success Banners */}
            <RuleErrorAlert error={offerError} onDismiss={() => setOfferError(null)} />
            {offerSuccess && (
              <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-xl text-xs font-semibold text-emerald-800 flex items-center space-x-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                <span>{offerSuccess}</span>
              </div>
            )}

            {/* Vehicle Advisory Badges List */}
            <div className="space-y-2">
              <label className="block text-xs font-bold text-slate-700">
                Select Vehicle ({supplierCars.length} vehicles available):
              </label>

              <div className="space-y-2 max-h-56 overflow-y-auto pr-1">
                {supplierCars.map((car) => {
                  const isSelected = selectedVehicleId === car.vehicle_id;

                  return (
                    <div
                      key={car.vehicle_id}
                      onClick={() => setSelectedVehicleId(car.vehicle_id)}
                      className={`p-3 rounded-xl border flex items-center justify-between cursor-pointer transition-all ${
                        isSelected
                          ? "border-indigo-600 bg-indigo-50/50 ring-2 ring-indigo-500/20"
                          : "border-slate-200 hover:border-slate-300"
                      }`}
                    >
                      <div className="flex items-center space-x-3">
                        <input
                          type="radio"
                          name="vehicle"
                          checked={isSelected}
                          onChange={() => setSelectedVehicleId(car.vehicle_id)}
                          className="w-4 h-4 text-indigo-600 focus:ring-indigo-500"
                        />
                        <div>
                          <div className="flex items-center space-x-2">
                            <span className="font-bold text-sm text-slate-900">{car.vehicle_id}</span>
                            <span className="text-xs font-semibold text-slate-600 bg-slate-100 px-2 py-0.5 rounded">
                              {car.type}
                            </span>
                          </div>
                          <div className="text-[11px] text-slate-500 mt-0.5">
                            {car.seats} seats • {car.large_bags} large • {car.small_bags} small
                          </div>
                        </div>
                      </div>

                      {/* Advisory Status Badge */}
                      <div>
                        {car.badge === "FITS_FREE" ? (
                          <span className="text-xs font-bold text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded-full border border-emerald-200">
                            Fits & Free
                          </span>
                        ) : car.badge === "BUSY" ? (
                          <span className="text-xs font-bold text-amber-700 bg-amber-50 px-2.5 py-1 rounded-full border border-amber-200">
                            {car.reason}
                          </span>
                        ) : (
                          <span className="text-xs font-bold text-rose-700 bg-rose-50 px-2.5 py-1 rounded-full border border-rose-200">
                            {car.reason}
                          </span>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Offer Price Input */}
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="block text-xs font-bold text-slate-700">
                  Your Offer Price (INR)
                </label>
                {assignModalRequest.price_min_inr && assignModalRequest.price_max_inr && (
                  <span className="text-xs text-slate-500">
                    Route Range: {formatINR(assignModalRequest.price_min_inr)} – {formatINR(assignModalRequest.price_max_inr)}
                  </span>
                )}
              </div>
              <div className="relative">
                <span className="absolute left-3.5 top-1/2 -translate-y-1/2 text-sm font-bold text-slate-400">₹</span>
                <input
                  type="number"
                  value={offerPrice || ""}
                  onChange={(e) => setOfferPrice(parseInt(e.target.value, 10) || 0)}
                  className="w-full pl-8 pr-4 py-2.5 rounded-xl border border-slate-300 font-bold text-base outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500"
                />
              </div>
            </div>

            {/* Actions */}
            <div className="flex items-center justify-end space-x-3 pt-3 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setAssignModalRequest(null)}
                className="px-4 py-2 text-xs font-semibold text-slate-600 hover:text-slate-800"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={submittingOffer || !selectedVehicleId}
                onClick={handleSubmitOffer}
                className="inline-flex items-center space-x-2 bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs px-5 py-2.5 rounded-xl shadow-md shadow-indigo-500/20 transition-all disabled:opacity-50"
              >
                <Send className="w-3.5 h-3.5" />
                <span>{submittingOffer ? "Assigning..." : "Assign Car & Send Offer"}</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
