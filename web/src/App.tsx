import React, { useState } from "react";
import { RolePickerPage } from "./pages/RolePickerPage";
import { ArrowLeft } from "lucide-react";

export const App: React.FC = () => {
  const [currentRole, setCurrentRole] = useState<"picker" | "traveler" | "supplier">("picker");

  if (currentRole === "picker") {
    return <RolePickerPage onSelectRole={setCurrentRole} />;
  }

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <header className="border-b border-slate-200 bg-white px-6 h-16 flex items-center justify-between">
        <button
          onClick={() => setCurrentRole("picker")}
          className="flex items-center space-x-2 text-sm font-medium text-slate-600 hover:text-slate-900 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Role Selection</span>
        </button>
        <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-slate-100 text-slate-700 capitalize">
          {currentRole} Portal
        </span>
      </header>
      <main className="max-w-4xl mx-auto px-6 py-12">
        <div className="bg-white rounded-2xl border border-slate-200 p-8 shadow-sm text-center">
          <h2 className="text-2xl font-bold capitalize">{currentRole} Portal</h2>
          <p className="mt-2 text-slate-600 text-sm">
            {currentRole === "traveler"
              ? "Traveler request builder and active offers interface will load here (Phase 2)."
              : "Supplier fleet management and incoming request dashboard will load here (Phase 3)."}
          </p>
        </div>
      </main>
    </div>
  );
};

export default App;
