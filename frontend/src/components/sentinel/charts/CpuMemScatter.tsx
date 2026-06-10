import {
  CartesianGrid,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
  ZAxis,
} from "recharts";
import type { ProcessRow } from "@/lib/api";
import { PanelHeader } from "../PanelHeader";
import { ScatterChart as ScatterIcon } from "lucide-react";

const COLOR = {
  normal:      "#3fb950",
  anomaly:     "#f85149",
  whitelisted: "#e3b341",
};

function toPoint(p: ProcessRow) {
  return {
    name: p.process_name,
    pid: p.pid,
    cpu: p.cpu_percent,
    mem: p.memory_mb,
    score: p.anomaly_score,
    status: p.status,
  };
}

type Point = ReturnType<typeof toPoint>;

export function CpuMemScatter({ processes }: { processes: ProcessRow[] }) {
  const series: Record<string, Point[]> = { normal: [], anomaly: [], whitelisted: [] };
  for (const p of processes) series[p.status].push(toPoint(p));

  return (
    <div className="flex h-full flex-col rounded-lg border border-border bg-card p-5">
      <PanelHeader title="CPU vs Memory" subtitle="Hover points for process detail" icon={ScatterIcon} />
      <div className="flex-1">
        <ResponsiveContainer width="100%" height={300}>
          <ScatterChart margin={{ left: 0, right: 16, top: 8, bottom: 4 }}>
            <CartesianGrid stroke="#21262d" strokeDasharray="3 3" />
            <XAxis
              type="number"
              dataKey="cpu"
              name="CPU"
              unit="%"
              stroke="#8b949e"
              tick={{ fontSize: 10, fill: "#8b949e" }}
              axisLine={{ stroke: "#21262d" }}
              tickLine={{ stroke: "#21262d" }}
            />
            <YAxis
              type="number"
              dataKey="mem"
              name="Memory"
              unit="MB"
              stroke="#8b949e"
              tick={{ fontSize: 10, fill: "#8b949e" }}
              axisLine={{ stroke: "#21262d" }}
              tickLine={{ stroke: "#21262d" }}
            />
            <ZAxis range={[40, 40]} />
            <Tooltip
              cursor={{ stroke: "#79c0ff", strokeDasharray: "3 3" }}
              content={({ active, payload }) => {
                if (!active || !payload?.length) return null;
                const p = payload[0].payload as Point;
                return (
                  <div className="rounded-md border border-border bg-card p-2 text-xs shadow-lg">
                    <p className="font-mono-tabular font-medium text-foreground">
                      {p.name} <span className="text-muted-foreground">({p.pid})</span>
                    </p>
                    <p className="text-muted-foreground">
                      CPU: <span className="font-mono-tabular text-foreground">{p.cpu.toFixed(1)}%</span>
                    </p>
                    <p className="text-muted-foreground">
                      Memory: <span className="font-mono-tabular text-foreground">{p.mem} MB</span>
                    </p>
                    <p className="text-muted-foreground">
                      Score: <span className="font-mono-tabular text-foreground">{p.score.toFixed(2)}</span>
                    </p>
                  </div>
                );
              }}
            />
            <Scatter data={series.normal}      fill={COLOR.normal}      fillOpacity={0.75} />
            <Scatter data={series.whitelisted} fill={COLOR.whitelisted} fillOpacity={0.85} />
            <Scatter data={series.anomaly}     fill={COLOR.anomaly}     fillOpacity={0.95} />
          </ScatterChart>
        </ResponsiveContainer>
      </div>
      <div className="mt-3 flex flex-wrap gap-3 text-xs">
        {(Object.keys(COLOR) as Array<keyof typeof COLOR>).map((k) => (
          <div key={k} className="flex items-center gap-1.5 text-muted-foreground">
            <span className="h-2 w-2 rounded-full" style={{ background: COLOR[k] }} />
            <span className="capitalize">{k}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
