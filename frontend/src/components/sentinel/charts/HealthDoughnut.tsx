import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import type { TooltipProps } from "recharts";
import type { ProcessRow } from "@/lib/api";
import { PanelHeader } from "../PanelHeader";
import { PieChart as PieIcon } from "lucide-react";

const COLORS = {
  normal:      "#3fb950",
  anomaly:     "#f85149",
  whitelisted: "#e3b341",
};

// ── Custom tooltip — positioned by Recharts near cursor, fully outside ring ──
function CustomTooltip({ active, payload }: TooltipProps<number, string>) {
  if (!active || !payload?.length) return null;
  const { name, value, payload: inner } = payload[0] as {
    name: string;
    value: number;
    payload: { pct: string; color: string };
  };
  return (
    <div
      style={{
        background: "#0d1117",
        border: `1px solid ${inner.color}55`,
        borderRadius: 8,
        padding: "8px 12px",
        pointerEvents: "none",
        boxShadow: `0 4px 24px ${inner.color}22`,
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 4 }}>
        <span style={{ display: "inline-block", width: 8, height: 8, borderRadius: "50%", background: inner.color }} />
        <span style={{ color: "#ffffff", fontSize: 12, fontWeight: 600 }}>{name}</span>
      </div>
      <div style={{ color: "#e6edf3", fontSize: 13, fontWeight: 700, fontFamily: "JetBrains Mono, monospace" }}>
        {value} <span style={{ color: "#8b949e", fontSize: 11, fontWeight: 400 }}>({inner.pct}%)</span>
      </div>
    </div>
  );
}

export function HealthDoughnut({ processes }: { processes: ProcessRow[] }) {
  const total = processes.length;
  const raw = [
    { name: "Normal",      value: processes.filter((p) => p.status === "normal").length,      key: "normal" },
    { name: "Anomaly",     value: processes.filter((p) => p.status === "anomaly").length,     key: "anomaly" },
    { name: "Whitelisted", value: processes.filter((p) => p.status === "whitelisted").length, key: "whitelisted" },
  ];

  // Attach pre-computed pct + color so the custom tooltip can read them from payload
  const data = raw.map((d) => ({
    ...d,
    color: COLORS[d.key as keyof typeof COLORS],
    pct: total > 0 ? ((d.value / total) * 100).toFixed(1) : "0.0",
  }));

  return (
    <div className="flex h-full flex-col rounded-lg border border-border bg-card p-5">
      <PanelHeader title="Process Health Overview" subtitle="Distribution by status" icon={PieIcon} />

      {/*
        The doughnut + centre total live entirely inside the SVG via Recharts' <Label>.
        No absolutely-positioned HTML overlay → nothing can overlap the ring.
      */}
      <ResponsiveContainer width="100%" height={230}>
        <PieChart>
          <Pie
            data={data}
            dataKey="value"
            nameKey="name"
            cx="50%"
            cy="50%"
            innerRadius={62}
            outerRadius={96}
            paddingAngle={3}
            stroke="#0d1117"
            strokeWidth={2}
            label={false}
            labelLine={false}
          >
            {data.map((d) => (
              <Cell key={d.key} fill={d.color} />
            ))}

            {/* SVG label rendered inside the hole — guaranteed never to touch the ring */}
          </Pie>

          {/* Tooltip appears near cursor; allowEscapeViewBox keeps it from being clipped */}
          <Tooltip
            content={<CustomTooltip />}
            allowEscapeViewBox={{ x: true, y: true }}
            offset={16}
          />
        </PieChart>
      </ResponsiveContainer>

      {/* Centre total — plain flex, sits below the chart, no overlap possible */}
      <div className="mb-1 -mt-2 flex flex-col items-center">
        <span className="font-mono-tabular text-2xl font-semibold text-foreground">{total}</span>
        <span className="text-[10px] uppercase tracking-wider text-muted-foreground">Total</span>
      </div>

      {/* Legend */}
      <div className="mt-3 space-y-2">
        {data.map((d) => (
          <div key={d.key} className="flex items-center gap-2 text-xs">
            <span className="h-2.5 w-2.5 shrink-0 rounded-sm" style={{ background: d.color }} />
            <span className="flex-1 text-muted-foreground">{d.name}</span>
            <div className="h-1 w-20 overflow-hidden rounded-full bg-secondary">
              <div
                className="h-full rounded-full transition-all duration-500"
                style={{ width: `${d.pct}%`, background: d.color }}
              />
            </div>
            <span className="w-20 text-right font-mono-tabular text-foreground">
              {d.value} <span className="text-muted-foreground">({d.pct}%)</span>
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
