export type Provider = "mock" | "deepseek";
export type Environment = "filesystem" | "database" | "research_assistant";
export type Condition = "C1" | "C5";

export type Capabilities = {
  providers: Provider[];
  environments: Environment[];
  conditions: Condition[];
  max_interactions: Record<string, number>;
  rate_limit_per_hour: number;
  deepseek_available: boolean;
};

export type RunRequest = {
  provider: Provider;
  environment: Environment;
  condition: Condition;
  interactions: number;
  seed: number;
  enable_monitoring: boolean;
  enable_intervention: boolean;
};

export type RunSummary = {
  interactions?: number;
  violations?: number;
  successful_actions?: number;
  rejected_actions?: number;
  tasks_completed?: number;
  drift_detections?: number;
  intervention_count?: number;
  mean_alignment?: number;
  violation_rate?: number;
  task_completion_rate?: number;
  [key: string]: unknown;
};

export type RunResponse = {
  run_id: string;
  status: "queued" | "running" | "completed" | "failed";
  request?: RunRequest;
  summary?: RunSummary | null;
  plots?: Record<string, string>;
  error?: string | null;
  created_at?: string;
  finished_at?: string;
};

export function apiBase(): string {
  const url = process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "");
  if (!url) {
    return "";
  }
  return url;
}

export async function fetchCapabilities(): Promise<Capabilities> {
  const base = apiBase();
  if (!base) {
    throw new Error("NEXT_PUBLIC_API_URL is not set");
  }
  const res = await fetch(`${base}/v1/capabilities`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Capabilities failed: ${res.status}`);
  return res.json();
}

export async function startRun(body: RunRequest): Promise<RunResponse> {
  const base = apiBase();
  if (!base) throw new Error("NEXT_PUBLIC_API_URL is not set");
  const res = await fetch(`${base}/v1/runs`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(detail || `Run failed: ${res.status}`);
  }
  return res.json();
}

export async function getRun(runId: string): Promise<RunResponse> {
  const base = apiBase();
  if (!base) throw new Error("NEXT_PUBLIC_API_URL is not set");
  const res = await fetch(`${base}/v1/runs/${runId}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Status failed: ${res.status}`);
  return res.json();
}

export function plotSrc(b64: string): string {
  return `data:image/png;base64,${b64}`;
}
