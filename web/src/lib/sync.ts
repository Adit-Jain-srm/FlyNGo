import { useEffect } from "react";

const SYNC_CHANNEL_NAME = "flyngo_live_sync";

export type SyncEvent =
  | "REQUEST_CREATED"
  | "OFFER_CREATED"
  | "OFFER_REJECTED"
  | "BOOKING_CREATED"
  | "CHANGE_REQUESTED"
  | "CHANGE_DECIDED";

/**
 * Broadcast an event across all tabs and within the current window.
 */
export function emitSyncEvent(event: SyncEvent) {
  try {
    if (typeof window !== "undefined" && "BroadcastChannel" in window) {
      const channel = new BroadcastChannel(SYNC_CHANNEL_NAME);
      channel.postMessage({ event, timestamp: Date.now() });
      channel.close();
    }
  } catch {
    // Ignore BroadcastChannel errors in unsupported environments
  }

  // Also dispatch within the current window
  if (typeof window !== "undefined") {
    window.dispatchEvent(new CustomEvent("flyngo_local_sync", { detail: event }));
  }
}

/**
 * Custom React hook to automatically synchronize data across tabs and components:
 * 1. Listens to cross-tab BroadcastChannel events
 * 2. Listens to in-tab window events
 * 3. Auto-refreshes when the tab/window gains focus or becomes visible
 * 4. Runs a gentle background heartbeat poll (default: 3000ms) while tab is visible
 */
export function useLiveSync(onSync: () => void | Promise<void>, intervalMs: number = 3000) {
  useEffect(() => {
    let channel: BroadcastChannel | null = null;

    try {
      if (typeof window !== "undefined" && "BroadcastChannel" in window) {
        channel = new BroadcastChannel(SYNC_CHANNEL_NAME);
        channel.onmessage = () => {
          onSync();
        };
      }
    } catch {
      // Ignore
    }

    const handleLocal = () => {
      onSync();
    };

    const handleFocus = () => {
      onSync();
    };

    const handleVisibility = () => {
      if (document.visibilityState === "visible") {
        onSync();
      }
    };

    window.addEventListener("flyngo_local_sync", handleLocal);
    window.addEventListener("focus", handleFocus);
    document.addEventListener("visibilitychange", handleVisibility);

    const timer = setInterval(() => {
      if (document.visibilityState === "visible") {
        onSync();
      }
    }, intervalMs);

    return () => {
      if (channel) {
        try {
          channel.close();
        } catch {
          // Ignore
        }
      }
      window.removeEventListener("flyngo_local_sync", handleLocal);
      window.removeEventListener("focus", handleFocus);
      document.removeEventListener("visibilitychange", handleVisibility);
      clearInterval(timer);
    };
  }, [onSync, intervalMs]);
}
