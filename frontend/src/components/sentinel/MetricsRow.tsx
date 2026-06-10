import { Cpu, AlertTriangle, Activity, ShieldCheck } from "lucide-react";
import { StatCard } from "./StatCard";
import type { SentinelView } from "@/hooks/useSentinelStore";

export function MetricsRow({ metrics }: { metrics: SentinelView["metrics"] }) {
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <StatCard
        label="Processes Monitored"
        value={metrics.total}
        icon={Cpu}
        delta={metrics.deltas.total}
        tone="default"
      />
      <StatCard
        label="Anomalies Detected"
        value={metrics.anomalies}
        icon={AlertTriangle}
        delta={metrics.deltas.anomalies}
        tone="anomaly"
      />
      <StatCard
        label="Anomaly Rate"
        value={`${metrics.anomalyRate.toFixed(1)}%`}
        icon={Activity}
        delta={+metrics.deltas.anomalyRate.toFixed(1)}
        tone={metrics.anomalyRate > 10 ? "anomaly" : "success"}
        threshold={metrics.anomalyRate > 10}
      />
      <StatCard
        label="Whitelisted"
        value={metrics.whitelisted}
        icon={ShieldCheck}
        delta={metrics.deltas.whitelisted}
        tone="whitelist"
      />
    </div>
  );
}
