import React from "react";
import { Plane, Car, ShieldCheck, ArrowRight, Building2, MapPin, CheckCircle2 } from "lucide-react";

interface RolePickerPageProps {
  onSelectRole: (role: "traveler" | "supplier") => void;
}

export const RolePickerPage: React.FC<RolePickerPageProps> = ({ onSelectRole }) => {

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col justify-between">
      {/* Top Navbar */}
      <header className="border-b border-slate-200/80 bg-white/90 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-600 flex items-center justify-center text-white shadow-md shadow-blue-500/20">
              <Plane className="w-5 h-5 -rotate-45" />
            </div>
            <div>
              <span className="text-xl font-black tracking-tight text-slate-900">FlyNGo</span>
              <span className="ml-2 text-xs font-semibold px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 border border-slate-200">
                Airport Transfers
              </span>
            </div>
          </div>

          {/* Network Status */}
          <div className="flex items-center space-x-2 text-xs text-slate-500">
            <span className="inline-block w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
            <span className="font-semibold text-slate-700">Online</span>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <main className="flex-1 max-w-5xl mx-auto px-6 py-16 flex flex-col items-center justify-center">
        <div className="text-center max-w-2xl mb-12 space-y-3">
          <div className="inline-flex items-center space-x-2 bg-blue-50 border border-blue-200/80 px-3.5 py-1 rounded-full text-xs font-bold text-blue-700">
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>Guaranteed Flat Rates • Monitored Flight Arrivals</span>
          </div>
          <h1 className="text-4xl md:text-5xl font-black text-slate-900 tracking-tight leading-tight">
            Airport Taxi Ride Offers at <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-indigo-600">Your Agreed Fare</span>
          </h1>
          <p className="text-base text-slate-600 max-w-xl mx-auto">
            Choose your portal. Travelers propose fares and receive offers from verified suppliers; suppliers assign vehicles with instant confirmation.
          </p>
        </div>

        {/* Portals Grid */}
        <div className="grid md:grid-cols-2 gap-8 w-full max-w-4xl">
          {/* Traveler Portal Card */}
          <div
            onClick={() => onSelectRole("traveler")}
            className="group relative bg-white rounded-3xl p-8 border border-slate-200/80 shadow-sm hover:shadow-2xl hover:border-blue-400 transition-all duration-300 cursor-pointer flex flex-col justify-between"
          >
            <div>
              <div className="w-14 h-14 rounded-2xl bg-blue-50 text-blue-600 flex items-center justify-center mb-6 group-hover:scale-110 group-hover:bg-blue-600 group-hover:text-white transition-all duration-300 shadow-sm">
                <Plane className="w-7 h-7" />
              </div>
              <h2 className="text-2xl font-black text-slate-900 group-hover:text-blue-600 transition-colors">
                Traveler Portal
              </h2>
              <p className="mt-2 text-slate-600 text-sm leading-relaxed">
                Schedule your ride, enter arrival flight details, select your hotel, and set your preferred fare. Receive bids from licensed taxi suppliers and book with guaranteed wait times.
              </p>

              <div className="mt-6 space-y-2 border-t border-slate-100 pt-4 text-xs text-slate-500">
                <div className="flex items-center space-x-2">
                  <ShieldCheck className="w-4 h-4 text-emerald-500" />
                  <span>Complimentary 60-min wait after landing</span>
                </div>
                <div className="flex items-center space-x-2">
                  <MapPin className="w-4 h-4 text-blue-500" />
                  <span>Serving Tokyo (NRT/HND), Osaka (KIX), Dubai (DXB) & Abu Dhabi (AUH)</span>
                </div>
              </div>
            </div>

            <div className="mt-8 flex items-center justify-between pt-4 border-t border-slate-100">
              <span className="text-sm font-bold text-blue-600">Enter as Traveler</span>
              <div className="w-10 h-10 rounded-full bg-blue-50 group-hover:bg-blue-600 group-hover:text-white text-blue-600 flex items-center justify-center transition-all duration-200 shadow-xs">
                <ArrowRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
              </div>
            </div>
          </div>

          {/* Supplier Portal Card */}
          <div
            onClick={() => onSelectRole("supplier")}
            className="group relative bg-white rounded-3xl p-8 border border-slate-200/80 shadow-sm hover:shadow-2xl hover:border-indigo-400 transition-all duration-300 cursor-pointer flex flex-col justify-between"
          >
            <div>
              <div className="w-14 h-14 rounded-2xl bg-indigo-50 text-indigo-600 flex items-center justify-center mb-6 group-hover:scale-110 group-hover:bg-indigo-600 group-hover:text-white transition-all duration-300 shadow-sm">
                <Car className="w-7 h-7" />
              </div>
              <h2 className="text-2xl font-black text-slate-900 group-hover:text-indigo-600 transition-colors">
                Supplier Portal
              </h2>
              <p className="mt-2 text-slate-600 text-sm leading-relaxed">
                Access incoming traveler requests matching your operational zones. Assign available sedans, SUVs, or buses, manage confirmed bookings, and review schedule updates.
              </p>

              <div className="mt-6 space-y-2 border-t border-slate-100 pt-4 text-xs text-slate-500">
                <div className="flex items-center space-x-2">
                  <Building2 className="w-4 h-4 text-indigo-500" />
                  <span>Verified taxi companies & chauffeur dispatch</span>
                </div>
                <div className="flex items-center space-x-2">
                  <ShieldCheck className="w-4 h-4 text-emerald-500" />
                  <span>Automated schedule management & conflict protection</span>
                </div>
              </div>
            </div>

            <div className="mt-8 flex items-center justify-between pt-4 border-t border-slate-100">
              <span className="text-sm font-bold text-indigo-600">Enter as Supplier</span>
              <div className="w-10 h-10 rounded-full bg-indigo-50 group-hover:bg-indigo-600 group-hover:text-white text-indigo-600 flex items-center justify-center transition-all duration-200 shadow-xs">
                <ArrowRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};
