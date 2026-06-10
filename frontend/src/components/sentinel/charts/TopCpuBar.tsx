import { Bar, BarChart, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { ProcessRow } from "@/lib/api";
import { PanelHeader } from "../PanelHeader";
import { BarChart3 } from "lucide-react";

const COLOR = {
  normal:      "#79c0ff",
  anomaly:     "#f85149",
  whitelisted: "#e3b341",
};

export function TopCpuBar({ processes }: { processes: ProcessRow[] }) {
  const data = [...processes]
    .sort((a, b) => b.cpu_percent - a.cpu_percent)
    .slice(0, 10)
    .map((p) => ({
      label: `${p.process_name} (${p.pid})`,
      cpu: p.cpu_percent,
      status: p.status,
    }))
    .reverse();

  return (
    <div className="flex h-full flex-col rounded-lg border border-border bg-card p-5">
      <PanelHeader title="Top 10 Processes by CPU" subtitle="Current snapshot" icon={BarChart3} />
      <div className="flex-1">
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={data} layout="vertical" margin={{ left: 10, right: 16, top: 4, bottom: 4 }}>
            <XAxis
              type="number"
              stroke="#8b949e"
              tick={{ fontSize: 10, fill: "#8b949e" }}
              axisLine={{ stroke: "#21262d" }}
              tickLine={{ stroke: "#21262d" }}
              unit="%"
            />
            <YAxis
              type="category"
              dataKey="label"
              stroke="#8b949e"
              tick={{ fontSize: 10, fill: "#8b949e", fontFamily: "JetBrains Mono" }}
              axisLine={{ stroke: "#21262d" }}
              tickLine={{ stroke: "#21262d" }}
              width={150}
            />
            <Tooltip
              cursor={{ fill: "rgba(121,192,255,0.08)" }}
              contentStyle={{
                background: "#161b22",
                border: "1px solid #21262d",
                borderRadius: 6,
                fontSize: 12,
                color: "#e6edf3",
              }}
              formatter={(v) => [`${Number(v).toFixed(1)}%`, "CPU"]}
            />
            <Bar dataKey="cpu" radius={[0, 4, 4, 0]}>
              {data.map((d, i) => (
                <Cell key={i} fill={COLOR[d.status as keyof typeof COLOR]} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
