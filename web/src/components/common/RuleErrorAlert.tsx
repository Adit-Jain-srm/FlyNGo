import React from "react";
import { AlertCircle } from "lucide-react";
import { ApiRuleError } from "../../api/client";
import { formatINR } from "../../lib/formatters";

interface RuleErrorAlertProps {
  error: ApiRuleError | string | null;
  onDismiss?: () => void;
}

export const RuleErrorAlert: React.FC<RuleErrorAlertProps> = ({ error, onDismiss }) => {
  if (!error) return null;

  const isRuleObj = typeof error === "object" && error !== null && "message" in error;
  const message = isRuleObj ? error.message : String(error);
  const allowed = isRuleObj && "allowed" in error ? (error as any).allowed : null;

  return (
    <div className="rounded-2xl border border-rose-200 bg-rose-50/90 p-4 text-sm text-rose-900 shadow-sm animate-in fade-in-50 duration-200">
      <div className="flex items-start space-x-3">
        <div className="rounded-xl bg-rose-100 p-2 text-rose-600 mt-0.5">
          <AlertCircle className="w-4 h-4" />
        </div>
        <div className="flex-1">
          <div className="flex items-center space-x-2">
            <span className="inline-block px-2.5 py-0.5 text-[11px] font-bold rounded-md bg-rose-200 text-rose-800 uppercase tracking-wide">
              Please Review
            </span>
          </div>
          <p className="mt-1.5 font-medium text-rose-800 text-xs sm:text-sm leading-relaxed">{message}</p>

          {/* Suggested / Allowed range badge if provided */}
          {allowed && allowed.min !== undefined && allowed.max !== undefined && (
            <div className="mt-2.5 inline-flex items-center space-x-2 bg-white rounded-xl px-3 py-1.5 text-xs border border-rose-200 text-rose-900 shadow-xs">
              <span className="font-semibold text-slate-600">Standard Route Fare:</span>
              <span className="font-mono font-bold text-slate-900">
                {typeof allowed.min === "number" ? formatINR(allowed.min) : allowed.min} –{" "}
                {typeof allowed.max === "number" ? formatINR(allowed.max) : allowed.max}
              </span>
            </div>
          )}
        </div>
        {onDismiss && (
          <button
            onClick={onDismiss}
            className="text-rose-400 hover:text-rose-700 text-sm font-semibold p-1"
          >
            ✕
          </button>
        )}
      </div>
    </div>
  );
};
