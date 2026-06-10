import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Header } from "@/components/sentinel/Header";
import { MetricsRow } from "@/components/sentinel/MetricsRow";
import { HealthDoughnut } from "@/components/sentinel/charts/HealthDoughnut";
import { TopCpuBar } from "@/components/sentinel/charts/TopCpuBar";
import { CpuMemScatter } from "@/components/sentinel/charts/CpuMemScatter";
import { AnomaliesTable } from "@/components/sentinel/tables/AnomaliesTable";
import { AllProcessesTable } from "@/components/sentinel/tables/AllProcessesTable";
import { WhitelistTable } from "@/components/sentinel/tables/WhitelistTable";
import { LlmAnalysisPanel } from "@/components/sentinel/LlmAnalysisPanel";
import { useSentinelStore } from "@/hooks/useSentinelStore";
import { Loader2, AlertTriangle } from "lucide-react";

export default function App() {
  const store = useSentinelStore();

  return (
    <div className="min-h-screen bg-background text-foreground">
      <Header
        onRefresh={store.refresh}
        isRefreshing={store.isRefreshing}
        lastRefreshedAt={store.snapshot?.generatedAt ?? null}
      />

      {/* Loading state — first load */}
      {store.isRefreshing && !store.snapshot && (
        <div className="flex min-h-[60vh] flex-col items-center justify-center gap-4 text-muted-foreground">
          <Loader2 className="h-10 w-10 animate-spin text-primary" />
          <p className="text-sm">📡 Taking live process snapshot (1 s) …</p>
        </div>
      )}

      {/* Error state */}
      {store.error && !store.isRefreshing && !store.snapshot && (
        <div className="flex min-h-[60vh] flex-col items-center justify-center gap-3 text-status-anomaly">
          <AlertTriangle className="h-10 w-10" />
          <p className="max-w-md text-center text-sm">{store.error}</p>
          <button
            onClick={store.refresh}
            className="mt-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
          >
            Retry
          </button>
        </div>
      )}

      {/* Main dashboard */}
      {store.snapshot && (
        <main className="mx-auto max-w-[1800px] animate-fade-in space-y-6 px-6 py-6">
          <MetricsRow metrics={store.metrics} />

          <section className="grid grid-cols-1 gap-4 lg:grid-cols-3">
            <HealthDoughnut processes={store.processes} />
            <TopCpuBar     processes={store.processes} />
            <CpuMemScatter processes={store.processes} />
          </section>

          <section className="card-glow rounded-lg border border-border bg-card p-5">
            <Tabs defaultValue="anomalies">
              <TabsList className="bg-secondary/60">
                <TabsTrigger
                  value="anomalies"
                  className="data-[state=active]:bg-card data-[state=active]:text-primary"
                >
                  Flagged Anomalies
                  <span className="ml-2 rounded bg-status-anomaly/10 px-1.5 py-0.5 font-mono-tabular text-[10px] text-status-anomaly">
                    {store.metrics.anomalies}
                  </span>
                </TabsTrigger>
                <TabsTrigger
                  value="all"
                  className="data-[state=active]:bg-card data-[state=active]:text-primary"
                >
                  All Processes
                  <span className="ml-2 rounded bg-secondary px-1.5 py-0.5 font-mono-tabular text-[10px] text-muted-foreground">
                    {store.metrics.total}
                  </span>
                </TabsTrigger>
                <TabsTrigger
                  value="whitelist"
                  className="data-[state=active]:bg-card data-[state=active]:text-primary"
                >
                  Whitelist
                  <span className="ml-2 rounded bg-status-whitelisted/10 px-1.5 py-0.5 font-mono-tabular text-[10px] text-status-whitelisted">
                    {store.whitelist.length}
                  </span>
                </TabsTrigger>
              </TabsList>
              <TabsContent value="anomalies" className="mt-4">
                <AnomaliesTable
                  processes={store.processes}
                  onWhitelist={store.addToWhitelistFn}
                />
              </TabsContent>
              <TabsContent value="all" className="mt-4">
                <AllProcessesTable processes={store.processes} />
              </TabsContent>
              <TabsContent value="whitelist" className="mt-4">
                <WhitelistTable
                  whitelist={store.whitelist}
                  onRemove={store.removeFromWhitelistFn}
                />
              </TabsContent>
            </Tabs>
          </section>

          <LlmAnalysisPanel />

          <footer className="border-t border-border pb-2 pt-4 text-center text-[11px] uppercase tracking-wider text-muted-foreground">
            Project Sentinel · Isolation Forest · Live process telemetry
          </footer>
        </main>
      )}
    </div>
  );
}
