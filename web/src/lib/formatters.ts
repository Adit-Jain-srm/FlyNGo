/**
 * Formatting helpers for FlyNGo UI
 * Enforces en-IN currency and local airport time representations.
 */

export function formatINR(amount: number): string {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(amount);
}

export function formatAirportTime(isoDateTime?: string, airportCode?: string): string {
  if (!isoDateTime) return "";
  const timePart = isoDateTime.includes("T") ? isoDateTime.split("T")[1].substring(0, 5) : isoDateTime;
  return airportCode ? `${timePart} (${airportCode} local)` : timePart;
}

export function formatDisplayDate(dateStr?: string): string {
  if (!dateStr) return "";
  const [year, month, day] = dateStr.split("T")[0].split("-").map(Number);
  const d = new Date(year, month - 1, day);
  return d.toLocaleDateString("en-US", {
    weekday: "short",
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}
