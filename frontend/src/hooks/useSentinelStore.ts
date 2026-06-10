import { useCallback, useEffect, useMemo, useState } from "react";
import {
  fetchSnapshot,
  fetchWhitelist,
  addToWhitelist,
  removeFromWhitelist,
  type ProcessRow,
  type TelemetrySnapshot,
} from "@/lib/api";

export interface SentinelView {
  snapshot: TelemetrySnapshot | null;
  processes: ProcessRow[];          // whitelist overlay already applied
  whitelist: string[];
  metrics: {
    total: number;
    anomalies: number;
    whitelisted: number;
    anomalyRate: number;
    deltas: { total: number; anomalies: number; whitelisted: number; anomalyRate: number };
  };
  isRefreshing: boolean;
  error: string | null;
  refresh: () => void;
  addToWhitelistFn: (names: string[]) => void;
  removeFromWhitelistFn: (name: string) => void;
}

// ── helpers ──────────────────────────────────────────────────────────────────

/**
 * Apply whitelist overlay to raw snapshot processes.
 * The backend always returns status = "anomaly" | "normal".
 * We override locally so UI reacts instantly without a re-fetch.
 */
function applyWhitelist(processes: ProcessRow[], whitelist: string[]): ProcessRow[] {
  const wlSet = new Set(whitelist);
  return processes.map((p) => {
    if (p.status === "anomaly" && wlSet.has(p.process_name)) {
      return { ...p, status: "whitelisted" as const };
    }
    // If the process was previously "whitelisted" but is no longer in the list,
    // restore it to "anomaly". The backend always sends the raw model verdict
    // so p.status here is already "anomaly" or "normal" — no extra logic needed.
    return p;
  });
}

function computeMetrics(rows: ProcessRow[]) {
  const total = rows.length;
  const anomalies = rows.filter((r) => r.status === "anomaly").length;
  const whitelisted = rows.filter((r) => r.status === "whitelisted").length;
  const anomalyRate = total === 0 ? 0 : (anomalies / total) * 100;
  return { total, anomalies, whitelisted, anomalyRate };
}

// ── hook ─────────────────────────────────────────────────────────────────────

export function useSentinelStore(): SentinelView {
  // Raw snapshot from the API — statuses are "anomaly"/"normal" only
  const [snapshot, setSnapshot] = useState<TelemetrySnapshot | null>(null);
  const [prevMetrics, setPrevMetrics] = useState<ReturnType<typeof computeMetrics> | null>(null);

  // Local whitelist — source of truth for the overlay; synced to backend asynchronously
  const [whitelist, setWhitelist] = useState<string[]>([]);

  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load persisted whitelist from backend on mount
  useEffect(() => {
    fetchWhitelist()
      .then(setWhitelist)
      .catch(() => { /* non-fatal */ });
  }, []);

  // Derive display processes by applying the whitelist overlay to raw snapshot data
  const processes = useMemo(
    () => applyWhitelist(snapshot?.processes ?? [], whitelist),
    [snapshot, whitelist],
  );

  const metrics = useMemo(() => {
    const cur = computeMetrics(processes);
    const prev = prevMetrics ?? cur;
    return {
      ...cur,
      deltas: {
        total:       cur.total       - prev.total,
        anomalies:   cur.anomalies   - prev.anomalies,
        whitelisted: cur.whitelisted - prev.whitelisted,
        anomalyRate: cur.anomalyRate - prev.anomalyRate,
      },
    };
  }, [processes, prevMetrics]);

  const doRefresh = useCallback(() => {
    setIsRefreshing(true);
    setError(null);
    fetchSnapshot()
      .then((snap) => {
        setSnapshot((prev) => {
          if (prev) setPrevMetrics(computeMetrics(applyWhitelist(prev.processes, whitelist)));
          return snap;
        });
      })
      .catch((err: Error) => setError(err.message))
      .finally(() => setIsRefreshing(false));
  // whitelist is intentionally excluded — refresh should not depend on it changing
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Auto-fetch on mount
  useEffect(() => {
    doRefresh();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  /**
   * Optimistically add names to whitelist then sync to backend.
   * The overlay in `processes` updates immediately via the useMemo above.
   */
  const addToWhitelistFn = useCallback((names: string[]) => {
    setWhitelist((wl) => Array.from(new Set([...wl, ...names])));
    addToWhitelist(names)
      .then(setWhitelist)   // reconcile with server's canonical list
      .catch(() => {
        // Rollback on failure
        setWhitelist((wl) => wl.filter((n) => !names.includes(n)));
      });
  }, []);

  /**
   * Optimistically remove a name from whitelist then sync to backend.
   */
  const removeFromWhitelistFn = useCallback((name: string) => {
    setWhitelist((wl) => wl.filter((n) => n !== name));
    removeFromWhitelist(name)
      .then(setWhitelist)   // reconcile with server's canonical list
      .catch(() => {
        // Rollback on failure
        setWhitelist((wl) => Array.from(new Set([...wl, name])));
      });
  }, []);

  return {
    snapshot,
    processes,
    whitelist,
    metrics,
    isRefreshing,
    error,
    refresh: doRefresh,
    addToWhitelistFn,
    removeFromWhitelistFn,
  };
}
