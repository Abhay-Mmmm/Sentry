import { Button } from "@/components/ui/button";
import { Trash2, ShieldCheck } from "lucide-react";

export function WhitelistTable({
  whitelist,
  onRemove,
}: {
  whitelist: string[];
  onRemove: (name: string) => void;
}) {
  if (whitelist.length === 0) {
    return (
      <div className="rounded-md border border-dashed border-border bg-card/30 p-8 text-center">
        <ShieldCheck className="mx-auto mb-2 h-6 w-6 text-muted-foreground" />
        <p className="text-sm text-muted-foreground">No processes whitelisted yet.</p>
        <p className="mt-1 text-xs text-muted-foreground">
          Select rows in the Flagged Anomalies tab and choose "Ignore Selected".
        </p>
      </div>
    );
  }
  return (
    <div className="overflow-x-auto rounded-md border border-border">
      <table className="w-full text-sm">
        <thead className="bg-secondary/50 text-[11px] uppercase tracking-wider text-muted-foreground">
          <tr>
            <th className="px-3 py-2 text-left">Process</th>
            <th className="px-3 py-2 text-right">Actions</th>
          </tr>
        </thead>
        <tbody>
          {whitelist.map((name, i) => (
            <tr
              key={name}
              className={i % 2 === 1 ? "border-t border-border bg-card/40" : "border-t border-border"}
            >
              <td className="px-3 py-2">
                <span className="font-mono-tabular text-foreground">{name}</span>
              </td>
              <td className="px-3 py-2 text-right">
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => onRemove(name)}
                  className="gap-1.5 text-muted-foreground hover:bg-status-anomaly/10 hover:text-status-anomaly"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                  Remove
                </Button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
