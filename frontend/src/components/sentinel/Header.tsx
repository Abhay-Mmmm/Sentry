import { Shield, RefreshCw, Activity } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface HeaderProps {
  onRefresh: () => void;
  isRefreshing: boolean;
  lastRefreshedAt: number | null;
}

export function Header({ onRefresh, isRefreshing, lastRefreshedAt }: HeaderProps) {
  const time = lastRefreshedAt
    ? new Date(lastRefreshedAt).toLocaleTimeString()
    : "—";
  return (
    <header className="border-b border-border bg-card/40 backdrop-blur-sm">
      <div className="mx-auto flex max-w-[1800px] flex-wrap items-center gap-6 px-6 py-4">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-md border border-primary/40 bg-primary/10 text-primary">
            <Shield className="h-5 w-5" />
          </div>
          <div>
            <h1 className="text-lg font-semibold tracking-tight text-foreground">Project Sentinel</h1>
            <p className="font-mono-tabular text-xs text-muted-foreground">
              Isolation Forest · Real-time process telemetry · Local LLM analysis
            </p>
          </div>
        </div>
        <nav className="hidden items-center gap-1 md:flex">
          <span className="flex cursor-default select-none items-center gap-2 rounded-md bg-primary/10 px-3 py-1.5 text-sm text-primary">
            <Activity className="h-4 w-4" />
            Dashboard
          </span>
        </nav>
        <div className="ml-auto flex items-center gap-3">
          <div className="hidden text-right md:block">
            <p className="text-[10px] uppercase tracking-wider text-muted-foreground">Last snapshot</p>
            <p className="font-mono-tabular text-xs text-foreground">{time}</p>
          </div>
          <Button
            onClick={onRefresh}
            disabled={isRefreshing}
            className="gap-2 bg-primary text-primary-foreground hover:bg-primary/90"
          >
            <RefreshCw className={cn("h-4 w-4", isRefreshing && "animate-spin")} />
            Refresh Snapshot
          </Button>
        </div>
      </div>
    </header>
  );
}
