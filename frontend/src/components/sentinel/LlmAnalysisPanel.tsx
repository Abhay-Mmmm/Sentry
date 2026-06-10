import { useState } from "react";
import { Brain, Loader2, Sparkles, Terminal } from "lucide-react";
import { Button } from "@/components/ui/button";
import { PanelHeader } from "./PanelHeader";
import { fetchLlmAnalysis } from "@/lib/api";

export function LlmAnalysisPanel() {
  const [report, setReport] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const run = () => {
    setLoading(true);
    setReport(null);
    setError(null);
    fetchLlmAnalysis()
      .then(setReport)
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  };

  return (
    <div className="card-glow rounded-lg border border-border bg-card p-5">
      <PanelHeader
        title="LLM Threat Analysis"
        subtitle="Local Gemma 4B via Ollama · contextual reasoning on flagged anomalies"
        icon={Brain}
        right={
          <Button
            onClick={run}
            disabled={loading}
            className="gap-2 bg-primary text-primary-foreground hover:bg-primary/90"
          >
            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
            {loading ? "Analyzing… (may take ~60s)" : "Explain Anomalies"}
          </Button>
        }
      />
      <div className="relative min-h-[200px] rounded-md border border-border bg-background/60 p-4">
        <div className="mb-2 flex items-center gap-2 text-[10px] uppercase tracking-wider text-muted-foreground">
          <Terminal className="h-3 w-3" />
          sentinel://llm/analysis
        </div>
        {loading && (
          <div className="flex items-center gap-3 text-sm text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin text-primary" />
            Running Gemma 4B inference on current snapshot…
          </div>
        )}
        {error && !loading && (
          <p className="text-sm text-status-anomaly">{error}</p>
        )}
        {!loading && !report && !error && (
          <p className="text-sm text-muted-foreground">
            Click <span className="text-primary">Explain Anomalies</span> to generate a contextual security
            analysis of the current flagged processes using your local Ollama model.
          </p>
        )}
        {report && (
          <pre className="whitespace-pre-wrap font-mono-tabular text-xs leading-relaxed text-foreground">
            {report}
          </pre>
        )}
      </div>
    </div>
  );
}
