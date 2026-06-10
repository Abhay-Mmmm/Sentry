import type { ProcessStatus } from "@/lib/api";
import { cn } from "@/lib/utils";

const STYLES: Record<ProcessStatus, string> = {
  normal:      "bg-status-normal/10 text-status-normal border-status-normal/30",
  anomaly:     "bg-status-anomaly/10 text-status-anomaly border-status-anomaly/40",
  whitelisted: "bg-status-whitelisted/10 text-status-whitelisted border-status-whitelisted/40",
};

const LABELS: Record<ProcessStatus, string> = {
  normal:      "Normal",
  anomaly:     "Anomaly",
  whitelisted: "Whitelisted",
};

export function StatusBadge({ status }: { status: ProcessStatus }) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-md border px-2 py-0.5 text-xs font-medium uppercase tracking-wider",
        STYLES[status],
      )}
    >
      <span
        className={cn(
          "h-1.5 w-1.5 rounded-full",
          status === "normal"      && "bg-status-normal",
          status === "anomaly"     && "bg-status-anomaly",
          status === "whitelisted" && "bg-status-whitelisted",
        )}
      />
      {LABELS[status]}
    </span>
  );
}
