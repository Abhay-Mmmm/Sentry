import type { LucideIcon } from "lucide-react";
import { ArrowDownRight, ArrowUpRight, Minus } from "lucide-react";
import { cn } from "@/lib/utils";

interface StatCardProps {
  label: string;
  value: string | number;
  icon: LucideIcon;
  delta?: number;
  tone?: "default" | "anomaly" | "whitelist" | "success";
  threshold?: boolean;
  hint?: string;
}

const TONE: Record<NonNullable<StatCardProps["tone"]>, string> = {
  default:   "text-primary border-primary/30 bg-primary/10",
  anomaly:   "text-status-anomaly border-status-anomaly/40 bg-status-anomaly/10",
  whitelist: "text-status-whitelisted border-status-whitelisted/40 bg-status-whitelisted/10",
  success:   "text-status-normal border-status-normal/40 bg-status-normal/10",
};

export function StatCard({
  label,
  value,
  icon: Icon,
  delta,
  tone = "default",
  threshold,
  hint,
}: StatCardProps) {
  const deltaSign = delta === undefined ? 0 : Math.sign(delta);
  const DeltaIcon = deltaSign === 0 ? Minus : deltaSign > 0 ? ArrowUpRight : ArrowDownRight;
  const deltaText =
    delta === undefined
      ? ""
      : deltaSign === 0
        ? "no change"
        : `${delta > 0 ? "+" : ""}${Number.isInteger(delta) ? delta : delta.toFixed(1)}`;

  return (
    <div
      className={cn(
        "card-glow group relative overflow-hidden rounded-lg border border-border bg-card p-5",
        threshold && "pulse-anomaly border-status-anomaly/60",
      )}
    >
      <div className="flex items-start justify-between">
        <div>
          <p className="text-[11px] font-medium uppercase tracking-[0.14em] text-muted-foreground">
            {label}
          </p>
          <p className="mt-2 font-mono-tabular text-3xl font-semibold text-foreground">{value}</p>
        </div>
        <div className={cn("flex h-9 w-9 items-center justify-center rounded-md border", TONE[tone])}>
          <Icon className="h-4 w-4" />
        </div>
      </div>
      <div className="mt-3 flex items-center justify-between text-xs">
        {delta !== undefined ? (
          <span
            className={cn(
              "inline-flex items-center gap-1 font-mono-tabular",
              deltaSign === 0 && "text-muted-foreground",
              deltaSign > 0 && (tone === "anomaly" ? "text-status-anomaly" : "text-status-normal"),
              deltaSign < 0 && (tone === "anomaly" ? "text-status-normal" : "text-muted-foreground"),
            )}
          >
            <DeltaIcon className="h-3 w-3" />
            {deltaText}
          </span>
        ) : (
          <span className="text-muted-foreground">{hint}</span>
        )}
        {threshold && (
          <span className="rounded border border-status-anomaly/50 bg-status-anomaly/10 px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wider text-status-anomaly">
            Threshold
          </span>
        )}
      </div>
    </div>
  );
}
