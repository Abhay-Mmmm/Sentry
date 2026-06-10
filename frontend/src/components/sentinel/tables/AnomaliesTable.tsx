import { useMemo, useState } from "react";
import { Checkbox } from "@/components/ui/checkbox";
import { Button } from "@/components/ui/button";
import { formatBytes, type ProcessRow } from "@/lib/api";
import { ShieldOff } from "lucide-react";
import { cn } from "@/lib/utils";

export function AnomaliesTable({
  processes,
  onWhitelist,
}: {
  processes: ProcessRow[];
  onWhitelist: (names: string[]) => void;
}) {
  const anomalies = useMemo(
    () =>
      processes
        .filter((p) => p.status === "anomaly")
        .sort((a, b) => b.anomaly_score - a.anomaly_score),
    [processes],
  );
  const [selected, setSelected] = useState<Set<string>>(new Set());

  const toggle = (name: string) => {
    setSelected((s) => {
      const next = new Set(s);
      if (next.has(name)) next.delete(name);
      else next.add(name);
      return next;
    });
  };

  const allSelected = anomalies.length > 0 && selected.size === anomalies.length;

  return (
    <div>
      <div className="mb-3 flex items-center justify-between">
        <p className="text-xs text-muted-foreground">
          {anomalies.length} anomalies flagged · {selected.size} selected
        </p>
        <Button
          size="sm"
          variant="outline"
          disabled={selected.size === 0}
          onClick={() => {
            onWhitelist(Array.from(selected));
            setSelected(new Set());
          }}
          className="gap-1.5 border-status-whitelisted/40 text-status-whitelisted hover:bg-status-whitelisted/10 hover:text-status-whitelisted"
        >
          <ShieldOff className="h-3.5 w-3.5" />
          Ignore Selected
        </Button>
      </div>
      <div className="overflow-x-auto rounded-md border border-border">
        <table className="w-full min-w-[860px] text-sm">
          <thead className="bg-secondary/50 text-[11px] uppercase tracking-wider text-muted-foreground">
            <tr>
              <th className="w-10 px-3 py-2 text-left">
                <Checkbox
                  checked={allSelected}
                  onCheckedChange={(c) =>
                    setSelected(c ? new Set(anomalies.map((a) => a.process_name)) : new Set())
                  }
                />
              </th>
              <th className="px-3 py-2 text-left">Process</th>
              <th className="px-3 py-2 text-right">PID</th>
              <th className="px-3 py-2 text-right">CPU %</th>
              <th className="px-3 py-2 text-right">Memory</th>
              <th className="px-3 py-2 text-right">Network</th>
              <th className="px-3 py-2 text-right">Disk I/O</th>
              <th className="px-3 py-2 text-right">Score</th>
            </tr>
          </thead>
          <tbody>
            {anomalies.length === 0 ? (
              <tr>
                <td colSpan={8} className="px-3 py-8 text-center text-sm text-muted-foreground">
                  🎉 No anomalies detected in current snapshot.
                </td>
              </tr>
            ) : (
              anomalies.map((p, i) => (
                <tr
                  key={`${p.process_name}-${p.pid}`}
                  className={cn(
                    "border-t border-border transition-colors hover:bg-secondary/40",
                    i % 2 === 1 && "bg-card/40",
                  )}
                >
                  <td className="px-3 py-2">
                    <Checkbox
                      checked={selected.has(p.process_name)}
                      onCheckedChange={() => toggle(p.process_name)}
                    />
                  </td>
                  <td className="px-3 py-2 font-mono-tabular text-foreground">{p.process_name}</td>
                  <td className="px-3 py-2 text-right font-mono-tabular text-muted-foreground">{p.pid}</td>
                  <td className="px-3 py-2 text-right font-mono-tabular text-foreground">{p.cpu_percent.toFixed(1)}</td>
                  <td className="px-3 py-2 text-right font-mono-tabular text-foreground">{p.memory_mb} MB</td>
                  <td className="px-3 py-2 text-right font-mono-tabular text-muted-foreground">{formatBytes(p.net_bytes_sent)}</td>
                  <td className="px-3 py-2 text-right font-mono-tabular text-muted-foreground">{p.disk_read_ops}</td>
                  <td className="px-3 py-2 text-right">
                    <span className="inline-block rounded border border-status-anomaly/40 bg-status-anomaly/10 px-2 py-0.5 font-mono-tabular text-xs text-status-anomaly">
                      {p.anomaly_score.toFixed(2)}
                    </span>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
