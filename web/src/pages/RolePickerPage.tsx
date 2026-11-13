import React from "react";
import { Plane, Car, ShieldCheck, ArrowRight, Building2, MapPin, CheckCircle2 } from "lucide-react";

interface RolePickerPageProps {
  onSelectRole: (role: "traveler" | "supplier") => void;
}

export const RolePickerPage: React.FC<RolePickerPageProps> = ({ onSelectRole }) => {

  return (
    <div className="min-h-screen flex flex-col justify-between">
      {/* Top Navbar */}
      <header className="border-b border-slate-200/80 bg-white/90 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-[var(--lane)] flex items-center justify-center text-white">
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
          <div className="inline-flex items-center space-x-2 bg-white border border-stone-200 px-3.5 py-1 rounded-full text-xs font-bold text-[var(--lane)]">
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>You name the fare. Suppliers answer with a car.</span>
          </div>
          <h1 className="text-4xl md:text-5xl font-black text-[var(--ink)] tracking-tight leading-tight">
            A ride from the airport, inside a fare you can see
          </h1>
          <p className="text-base text-stone-600 max-w-xl mx-auto">
            Pick a door. Travelers post a price inside the route range. Suppliers who can make that trip assign a car.
          </p>
        </div>

        {/* Portals Grid */}
        <div className="grid md:grid-cols-2 gap-8 w-full max-w-4xl">
          {/* Traveler Portal Card */}
          <button
            type="button"
            onClick={() => onSelectRole("traveler")}
            className="group relative bg-white rounded-3xl p-8 border border-stone-200 text-left shadow-sm hover:border-[var(--lane)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--lane)] transition-colors duration-300 cursor-pointer flex flex-col justify-between min-h-[44px]"
          >
            <span className="pointer-events-none absolute inset-y-4 left-0 w-1 origin-top scale-y-0 bg-[var(--lane)] transition-transform duration-300 group-hover:scale-y-100 group-focus-visible:scale-y-100" />
            <div>
              <div className="w-14 h-14 rounded-2xl bg-teal-50 text-[var(--lane)] flex items-center justify-center mb-6 group-hover:bg-[var(--lane)] group-hover:text-white transition-colors duration-300">
                <Plane className="w-7 h-7" />
              </div>
              <h2 className="text-2xl font-black text-slate-900 group-hover:text-[var(--lane)] transition-colors">
                Traveler Portal
              </h2>
              <p className="mt-2 text-slate-600 text-sm leading-relaxed">
                Enter your flight, hotel, party, and a price inside the route range. Book one of the cars that suppliers assign.
              </p>

              <div className="mt-6 space-y-2 border-t border-slate-100 pt-4 text-xs text-slate-500">
                <div className="flex items-center space-x-2">
                  <ShieldCheck className="w-4 h-4 text-emerald-500" />
                  <span>Pickup is at least 60 minutes after landing</span>
                </div>
                <div className="flex items-center space-x-2">
                  <MapPin className="w-4 h-4 text-blue-500" />
                  <span>Serving Tokyo (NRT/HND), Osaka (KIX), Dubai (DXB) & Abu Dhabi (AUH)</span>
                </div>
              </div>
            </div>

            <div className="mt-8 flex items-center justify-between pt-4 border-t border-slate-100">
              <span className="text-sm font-bold text-[var(--lane)]">Enter as Traveler</span>
              <div className="w-10 h-10 rounded-full bg-teal-50 group-hover:bg-[var(--lane)] group-hover:text-white text-[var(--lane)] flex items-center justify-center transition-colors duration-200">
                <ArrowRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
              </div>
            </div>
          </button>

          <button
            type="button"
            onClick={() => onSelectRole("supplier")}
            className="group relative bg-white rounded-3xl p-8 border border-stone-200 text-left shadow-sm hover:border-[var(--lane)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--lane)] transition-colors duration-300 cursor-pointer flex flex-col justify-between min-h-[44px]"
          >
            <span className="pointer-events-none absolute inset-y-4 left-0 w-1 origin-top scale-y-0 bg-[var(--lane)] transition-transform duration-300 group-hover:scale-y-100 group-focus-visible:scale-y-100" />
            <div>
              <div className="w-14 h-14 rounded-2xl bg-teal-50 text-[var(--lane)] flex items-center justify-center mb-6 group-hover:bg-[var(--lane)] group-hover:text-white transition-colors duration-300">
                <Car className="w-7 h-7" />
              </div>
              <h2 className="text-2xl font-black text-slate-900 group-hover:text-[var(--lane)] transition-colors">
                Supplier Portal
              </h2>
              <p className="mt-2 text-slate-600 text-sm leading-relaxed">
                See only the rides your company can do. Assign a car and a price inside the route range.
              </p>

              <div className="mt-6 space-y-2 border-t border-slate-100 pt-4 text-xs text-slate-500">
                <div className="flex items-center space-x-2">
                  <Building2 className="w-4 h-4 text-indigo-500" />
                  <span>11 companies already in the catalog</span>
                </div>
                <div className="flex items-center space-x-2">
                  <ShieldCheck className="w-4 h-4 text-emerald-500" />
                  <span>A busy car cannot be booked twice</span>
                </div>
              </div>
            </div>

            <div className="mt-8 flex items-center justify-between pt-4 border-t border-slate-100">
              <span className="text-sm font-bold text-[var(--lane)]">Enter as Supplier</span>
              <div className="w-10 h-10 rounded-full bg-teal-50 group-hover:bg-[var(--lane)] group-hover:text-white text-[var(--lane)] flex items-center justify-center transition-colors duration-200">
                <ArrowRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
              </div>
            </div>
          </button>
        </div>
      </main>
    </div>
  );
};
