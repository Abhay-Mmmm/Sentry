import { useMemo, useState } from "react";
import { ArrowDown, ArrowUp, ArrowUpDown } from "lucide-react";
import { formatBytes, type ProcessRow } from "@/lib/api";
import { StatusBadge } from "../StatusBadge";
import { cn } from "@/lib/utils";

type SortKey = keyof Pick<
  ProcessRow,
  "process_name" | "pid" | "cpu_percent" | "memory_mb" | "net_bytes_sent" | "disk_read_ops" | "anomaly_score"
>;

const COLUMNS: { key: SortKey; label: string; align?: "right" }[] = [
  { key: "process_name", label: "Process" },
  { key: "pid",          label: "PID",      align: "right" },
  { key: "cpu_percent",  label: "CPU %",    align: "right" },
  { key: "memory_mb",    label: "Memory",   align: "right" },
  { key: "net_bytes_sent", label: "Network",  align: "right" },
  { key: "disk_read_ops",  label: "Disk I/O", align: "right" },
  { key: "anomaly_score",  label: "Score",    align: "right" },
];

export function AllProcessesTable({ processes }: { processes: ProcessRow[] }) {
  const [sortKey, setSortKey] = useState<SortKey>("anomaly_score");
  const [dir, setDir] = useState<"asc" | "desc">("desc");

  const sorted = useMemo(() => {
    const arr = [...processes];
    arr.sort((a, b) => {
      const av = a[sortKey];
      const bv = b[sortKey];
      if (typeof av === "number" && typeof bv === "number") return dir === "asc" ? av - bv : bv - av;
      return dir === "asc"
        ? String(av).localeCompare(String(bv))
        : String(bv).localeCompare(String(av));
    });
    return arr;
  }, [processes, sortKey, dir]);

  const onSort = (k: SortKey) => {
    if (k === sortKey) setDir((d) => (d === "asc" ? "desc" : "asc"));
    else {
      setSortKey(k);
      setDir("desc");
    }
  };

  return (
    <div className="overflow-x-auto rounded-md border border-border">
      <table className="w-full min-w-[900px] text-sm">
        <thead className="bg-secondary/50 text-[11px] uppercase tracking-wider text-muted-foreground">
          <tr>
            {COLUMNS.map((c) => (
              <th
                key={c.key}
                className={cn("px-3 py-2 select-none", c.align === "right" ? "text-right" : "text-left")}
              >
                <button
                  type="button"
                  onClick={() => onSort(c.key)}
                  className="inline-flex items-center gap-1 hover:text-foreground"
                >
                  {c.label}
                  {sortKey === c.key ? (
                    dir === "asc" ? (
                      <ArrowUp className="h-3 w-3" />
                    ) : (
                      <ArrowDown className="h-3 w-3" />
                    )
                  ) : (
                    <ArrowUpDown className="h-3 w-3 opacity-50" />
                  )}
                </button>
              </th>
            ))}
            <th className="px-3 py-2 text-right">Status</th>
          </tr>
        </thead>
        <tbody>
          {sorted.map((p, i) => (
            <tr
              key={`${p.process_name}-${p.pid}`}
              className={cn(
                "border-t border-border transition-colors hover:bg-secondary/40",
                i % 2 === 1 && "bg-card/40",
              )}
            >
              <td className="px-3 py-2 font-mono-tabular text-foreground">{p.process_name}</td>
              <td className="px-3 py-2 text-right font-mono-tabular text-muted-foreground">{p.pid}</td>
              <td className="px-3 py-2 text-right font-mono-tabular text-foreground">{p.cpu_percent.toFixed(1)}</td>
              <td className="px-3 py-2 text-right font-mono-tabular text-foreground">{p.memory_mb} MB</td>
              <td className="px-3 py-2 text-right font-mono-tabular text-muted-foreground">{formatBytes(p.net_bytes_sent)}</td>
              <td className="px-3 py-2 text-right font-mono-tabular text-muted-foreground">{p.disk_read_ops}</td>
              <td className="px-3 py-2 text-right font-mono-tabular text-foreground">{p.anomaly_score.toFixed(2)}</td>
              <td className="px-3 py-2 text-right">
                <StatusBadge status={p.status} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
