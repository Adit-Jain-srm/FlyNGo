import React from "react";
import { formatINR } from "../../lib/formatters";
import { AlertCircle, CheckCircle2 } from "lucide-react";

interface PriceRangeBarProps {
  minPrice: number;
  maxPrice: number;
  userPrice: number;
  onChangePrice: (val: number) => void;
}

export const PriceRangeBar: React.FC<PriceRangeBarProps> = ({
  minPrice,
  maxPrice,
  userPrice,
  onChangePrice,
}) => {
  const midpoint = Math.round((minPrice + maxPrice) / 2);
  const isTooLow = userPrice > 0 && userPrice < minPrice;
  const isValid = userPrice >= minPrice && userPrice <= maxPrice;

  return (
    <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <label className="block text-sm font-semibold text-slate-900">
            Your Proposed Ride Price (INR)
          </label>
          <span className="text-xs text-slate-500">
            Taxi suppliers will review your price and assign available vehicles.
          </span>
        </div>

        {/* Quick price status indicator */}
        {userPrice > 0 && (
          <div className="flex items-center space-x-1.5 text-xs font-semibold">
            {isValid ? (
              <span className="flex items-center space-x-1 text-emerald-600 bg-emerald-50 px-2.5 py-1 rounded-full border border-emerald-200">
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>Inside suggested range</span>
              </span>
            ) : isTooLow ? (
              <span className="flex items-center space-x-1 text-rose-600 bg-rose-50 px-2.5 py-1 rounded-full border border-rose-200">
                <AlertCircle className="w-3.5 h-3.5" />
                <span>Below route min ({formatINR(minPrice)})</span>
              </span>
            ) : (
              <span className="flex items-center space-x-1 text-rose-600 bg-rose-50 px-2.5 py-1 rounded-full border border-rose-200">
                <AlertCircle className="w-3.5 h-3.5" />
                <span>Above route max ({formatINR(maxPrice)})</span>
              </span>
            )}
          </div>
        )}
      </div>

      {/* Direct numeric input */}
      <div className="relative">
        <span className="absolute left-4 top-1/2 -translate-y-1/2 text-lg font-bold text-slate-400">
          ₹
        </span>
        <input
          type="number"
          value={userPrice || ""}
          onChange={(e) => onChangePrice(parseInt(e.target.value, 10) || 0)}
          placeholder={`e.g. ${midpoint}`}
          className={`w-full pl-9 pr-4 py-3 rounded-xl border text-xl font-bold tracking-tight outline-none transition-all ${
            isValid
              ? "border-emerald-300 focus:border-emerald-500 focus:ring-4 focus:ring-emerald-500/10 text-slate-900"
              : userPrice > 0
              ? "border-rose-300 focus:border-rose-500 focus:ring-4 focus:ring-rose-500/10 text-rose-900 bg-rose-50/20"
              : "border-slate-300 focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10 text-slate-900"
          }`}
        />
      </div>

      {/* Suggested Range Visualizer Bar */}
      <div className="pt-2">
        <div className="flex justify-between text-xs font-semibold text-slate-500 mb-2">
          <span>Min: {formatINR(minPrice)}</span>
          <span className="text-slate-400">Mid: {formatINR(midpoint)}</span>
          <span>Max: {formatINR(maxPrice)}</span>
        </div>

        <div className="relative h-3 w-full bg-slate-100 rounded-full overflow-hidden p-0.5 border border-slate-200">
          {/* Active safe zone */}
          <div className="h-full rounded-full bg-gradient-to-r from-blue-400 via-emerald-400 to-indigo-400 opacity-90" />
        </div>

        {/* Quick select buttons */}
        <div className="mt-3 flex items-center justify-center space-x-2">
          <span className="text-xs text-slate-500 font-medium">Quick set:</span>
          <button
            type="button"
            onClick={() => onChangePrice(minPrice)}
            className="text-xs font-semibold px-2.5 py-1 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 transition-colors"
          >
            Min {formatINR(minPrice)}
          </button>
          <button
            type="button"
            onClick={() => onChangePrice(midpoint)}
            className="text-xs font-semibold px-2.5 py-1 rounded-lg bg-blue-50 hover:bg-blue-100 text-blue-700 border border-blue-200 transition-colors"
          >
            Midpoint {formatINR(midpoint)}
          </button>
          <button
            type="button"
            onClick={() => onChangePrice(maxPrice)}
            className="text-xs font-semibold px-2.5 py-1 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 transition-colors"
          >
            Max {formatINR(maxPrice)}
          </button>
        </div>
      </div>
    </div>
  );
};
