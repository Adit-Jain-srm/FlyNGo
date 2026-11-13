import React, { useEffect, useState } from "react";
import { Plane, Car, ShieldCheck, ArrowRight, Activity, Building2, MapPin } from "lucide-react";
import { fetchHealth, HealthResponse } from "../api/client";

interface RolePickerPageProps {
  onSelectRole: (role: "traveler" | "supplier") => void;
}

export const RolePickerPage: React.FC<RolePickerPageProps> = ({ onSelectRole }) => {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchHealth()
      .then((data) => {
        setHealth(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message || "Failed to connect to API");
        setLoading(false);
      });
  }, []);

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col justify-between">
      {/* Top Navbar */}
      <header className="border-b border-slate-200 bg-white/80 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-600 flex items-center justify-center text-white shadow-md shadow-blue-500/20">
              <Plane className="w-5 h-5 -rotate-45" />
            </div>
            <div>
              <span className="text-xl font-bold tracking-tight text-slate-900">FlyNGo</span>
              <span className="ml-2 text-xs font-semibold px-2 py-0.5 rounded-full bg-blue-50 text-blue-700 border border-blue-200">
                Phase 1 MVP
              </span>
            </div>
          </div>

          {/* Backend Status Indicator */}
          <div className="flex items-center space-x-2 text-sm">
            <Activity className={`w-4 h-4 ${health?.status === "healthy" ? "text-emerald-500 animate-pulse" : "text-amber-500"}`} />
            {loading ? (
              <span className="text-slate-500 text-xs">Checking backend...</span>
            ) : health?.status === "healthy" ? (
              <div className="flex items-center space-x-2">
                <span className="inline-block w-2 h-2 rounded-full bg-emerald-500"></span>
                <span className="text-xs font-medium text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-md border border-emerald-200">
                  API Connected (:8000)
                </span>
              </div>
            ) : (
              <span
                className="text-xs font-medium text-amber-700 bg-amber-50 px-2 py-0.5 rounded-md border border-amber-200"
                title={error || "API unavailable"}
              >
                Backend Offline
              </span>
            )}
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <main className="flex-1 max-w-5xl mx-auto px-6 py-12 flex flex-col items-center justify-center">
        <div className="text-center max-w-2xl mb-12">
          <h1 className="text-4xl md:text-5xl font-extrabold text-slate-900 tracking-tight leading-tight">
            Seamless Airport Rides at <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-indigo-600">Your Agreed Price</span>
          </h1>
          <p className="mt-4 text-base md:text-lg text-slate-600">
            Pick your role to get started. Travelers post requests with verified routes; suppliers assign vehicles with transparent pricing.
          </p>
        </div>

        {/* Role Cards Grid */}
        <div className="grid md:grid-cols-2 gap-8 w-full max-w-4xl">
          {/* Traveler Portal Card */}
          <div
            onClick={() => onSelectRole("traveler")}
            className="group relative bg-white rounded-2xl p-8 border border-slate-200 shadow-sm hover:shadow-xl hover:border-blue-400 transition-all duration-300 cursor-pointer flex flex-col justify-between"
          >
            <div>
              <div className="w-14 h-14 rounded-2xl bg-blue-50 text-blue-600 flex items-center justify-center mb-6 group-hover:scale-110 group-hover:bg-blue-600 group-hover:text-white transition-all duration-300">
                <Plane className="w-7 h-7" />
              </div>
              <h2 className="text-2xl font-bold text-slate-900 group-hover:text-blue-600 transition-colors">
                Traveler Portal
              </h2>
              <p className="mt-2 text-slate-600 text-sm leading-relaxed">
                Enter your flight, select your hotel, see route price suggestions, and post a ride request. Receive offers from verified suppliers and book instantly.
              </p>

              <div className="mt-6 space-y-2 border-t border-slate-100 pt-4 text-xs text-slate-500">
                <div className="flex items-center space-x-2">
                  <ShieldCheck className="w-4 h-4 text-emerald-500" />
                  <span>Rule-checked pickup times & pricing ranges</span>
                </div>
                <div className="flex items-center space-x-2">
                  <MapPin className="w-4 h-4 text-blue-500" />
                  <span>Serving NRT, HND, KIX, DXB & AUH</span>
                </div>
              </div>
            </div>

            <div className="mt-8 flex items-center justify-between pt-4 border-t border-slate-100">
              <span className="text-sm font-semibold text-blue-600">Open Traveler Portal</span>
              <div className="w-9 h-9 rounded-full bg-blue-50 group-hover:bg-blue-600 group-hover:text-white text-blue-600 flex items-center justify-center transition-all duration-200">
                <ArrowRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
              </div>
            </div>
          </div>

          {/* Supplier Portal Card */}
          <div
            onClick={() => onSelectRole("supplier")}
            className="group relative bg-white rounded-2xl p-8 border border-slate-200 shadow-sm hover:shadow-xl hover:border-indigo-400 transition-all duration-300 cursor-pointer flex flex-col justify-between"
          >
            <div>
              <div className="w-14 h-14 rounded-2xl bg-indigo-50 text-indigo-600 flex items-center justify-center mb-6 group-hover:scale-110 group-hover:bg-indigo-600 group-hover:text-white transition-all duration-300">
                <Car className="w-7 h-7" />
              </div>
              <h2 className="text-2xl font-bold text-slate-900 group-hover:text-indigo-600 transition-colors">
                Supplier Portal
              </h2>
              <p className="mt-2 text-slate-600 text-sm leading-relaxed">
                Log in as any registered taxi company (e.g. Sakura Cabs, Edo Prime). View open requests, assign available vehicles, manage active bookings and flight changes.
              </p>

              <div className="mt-6 space-y-2 border-t border-slate-100 pt-4 text-xs text-slate-500">
                <div className="flex items-center space-x-2">
                  <Building2 className="w-4 h-4 text-indigo-500" />
                  <span>11 verified taxi suppliers & 28 vehicles</span>
                </div>
                <div className="flex items-center space-x-2">
                  <ShieldCheck className="w-4 h-4 text-emerald-500" />
                  <span>Automated schedule & vehicle conflict protection</span>
                </div>
              </div>
            </div>

            <div className="mt-8 flex items-center justify-between pt-4 border-t border-slate-100">
              <span className="text-sm font-semibold text-indigo-600">Open Supplier Portal</span>
              <div className="w-9 h-9 rounded-full bg-indigo-50 group-hover:bg-indigo-600 group-hover:text-white text-indigo-600 flex items-center justify-center transition-all duration-200">
                <ArrowRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
              </div>
            </div>
          </div>
        </div>

        {/* Live Data Summary Pills */}
        {health?.counts && (
          <div className="mt-12 bg-white rounded-xl border border-slate-200 px-6 py-4 shadow-sm max-w-3xl w-full">
            <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider text-center mb-3">
              Catalog & Live State Snapshot
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-center">
              <div>
                <div className="text-xl font-bold text-slate-800">{health.counts.flights || 0}</div>
                <div className="text-xs text-slate-500">Active Flights</div>
              </div>
              <div>
                <div className="text-xl font-bold text-slate-800">{health.counts.hotels || 0}</div>
                <div className="text-xs text-slate-500">Hotels (5 Hubs)</div>
              </div>
              <div>
                <div className="text-xl font-bold text-slate-800">{health.counts.suppliers || 0}</div>
                <div className="text-xs text-slate-500">Taxi Companies</div>
              </div>
              <div>
                <div className="text-xl font-bold text-slate-800">{health.counts.vehicles || 0}</div>
                <div className="text-xs text-slate-500">Fleet Vehicles</div>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-200 py-6 text-center text-xs text-slate-500">
        FlyNGo Hackathon Platform • Built with FastAPI, SQLite, React & Vite
      </footer>
    </div>
  );
};
