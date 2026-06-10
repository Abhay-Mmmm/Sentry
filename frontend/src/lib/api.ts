// api.ts — typed client for the FastAPI backend

export type ProcessStatus = "normal" | "anomaly" | "whitelisted";

export interface ProcessRow {
  process_name: string;
  pid: number;
  cpu_percent: number;
  memory_mb: number;
  net_bytes_sent: number;
  disk_read_ops: number;
  anomaly_score: number; // normalised 0–1 (1 = most anomalous)
  status: ProcessStatus;
}

export interface TelemetrySnapshot {
  generatedAt: number; // epoch ms
  processes: ProcessRow[];
}

// Snake_case response from FastAPI → camelCase
interface ApiSnapshotResponse {
  generated_at: number;
  processes: ProcessRow[];
}

export async function fetchSnapshot(): Promise<TelemetrySnapshot> {
  const res = await fetch("/api/snapshot");
  if (!res.ok) {
    const msg = await res.text().catch(() => res.statusText);
    throw new Error(`Snapshot failed: ${msg}`);
  }
  const data: ApiSnapshotResponse = await res.json();
  return { generatedAt: data.generated_at, processes: data.processes };
}

export async function fetchWhitelist(): Promise<string[]> {
  const res = await fetch("/api/whitelist");
  if (!res.ok) throw new Error("Whitelist fetch failed");
  const data: { names: string[] } = await res.json();
  return data.names;
}

export async function addToWhitelist(names: string[]): Promise<string[]> {
  const res = await fetch("/api/whitelist/add", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ names }),
  });
  if (!res.ok) throw new Error("Whitelist add failed");
  const data: { names: string[] } = await res.json();
  return data.names;
}

export async function removeFromWhitelist(name: string): Promise<string[]> {
  const res = await fetch("/api/whitelist/remove", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name }),
  });
  if (!res.ok) throw new Error("Whitelist remove failed");
  const data: { names: string[] } = await res.json();
  return data.names;
}

export async function fetchLlmAnalysis(): Promise<string> {
  const res = await fetch("/api/llm", { method: "POST" });
  if (!res.ok) throw new Error("LLM request failed");
  const data: { report: string } = await res.json();
  return data.report;
}

export function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
  return `${(bytes / 1024 / 1024 / 1024).toFixed(2)} GB`;
}
