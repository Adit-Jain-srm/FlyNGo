import React, { useState } from "react";
import { RolePickerPage } from "./pages/RolePickerPage";
import { TravelerPage } from "./pages/TravelerPage";
import { SupplierPortal } from "./features/supplier/SupplierPortal";
import { ChevronLeft, Car, Plane } from "lucide-react";

export const App: React.FC = () => {
  const [currentRole, setCurrentRole] = useState<"picker" | "traveler" | "supplier">("picker");

  if (currentRole === "picker") {
    return <RolePickerPage onSelectRole={setCurrentRole} />;
  }

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 flex flex-col font-sans">
      {/* Top Navbar */}
      <header className="border-b border-slate-200/80 bg-white/95 backdrop-blur-md px-6 h-16 flex items-center justify-between sticky top-0 z-50 shadow-xs">
        <div className="flex items-center space-x-4">
          <button
            onClick={() => setCurrentRole("picker")}
            className="flex items-center space-x-1.5 text-xs font-bold text-slate-600 hover:text-slate-900 bg-slate-100 hover:bg-slate-200/80 px-3 py-1.5 rounded-xl transition-colors"
          >
            <ChevronLeft className="w-4 h-4" />
            <span>Home</span>
          </button>

          <div className="flex items-center space-x-2.5 border-l border-slate-200 pl-4">
            <div className={`w-8 h-8 rounded-xl flex items-center justify-center text-white shadow-xs ${
              currentRole === "traveler" ? "bg-blue-600" : "bg-indigo-600"
            }`}>
              {currentRole === "traveler" ? <Plane className="w-4 h-4" /> : <Car className="w-4 h-4" />}
            </div>
            <div>
              <span className="text-sm font-black text-slate-900">
                {currentRole === "traveler" ? "Traveler Portal" : "Supplier Portal"}
              </span>
            </div>
          </div>
        </div>

        {/* Quick Portal Switcher */}
        <div className="flex items-center space-x-1.5 bg-slate-100 p-1 rounded-2xl border border-slate-200">
          <button
            onClick={() => setCurrentRole("traveler")}
            className={`text-xs font-bold px-3.5 py-1.5 rounded-xl transition-all ${
              currentRole === "traveler"
                ? "bg-white text-blue-600 shadow-sm"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            Traveler
          </button>
          <button
            onClick={() => setCurrentRole("supplier")}
            className={`text-xs font-bold px-3.5 py-1.5 rounded-xl transition-all ${
              currentRole === "supplier"
                ? "bg-white text-indigo-600 shadow-sm"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            Supplier
          </button>
        </div>
      </header>

      {/* Main Body */}
      <main className="flex-1">
        {currentRole === "traveler" ? (
          <TravelerPage
            onSwitchToSupplier={() => setCurrentRole("supplier")}
          />
        ) : (
          <SupplierPortal />
        )}
      </main>
    </div>
  );
};

export default App;
