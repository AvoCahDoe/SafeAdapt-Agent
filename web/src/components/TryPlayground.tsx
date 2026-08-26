"use client";

import { useEffect, useState } from "react";
import {
  Capabilities,
  Condition,
  Environment,
  Provider,
  RunResponse,
  fetchCapabilities,
  getRun,
  plotSrc,
  startRun,
} from "@/lib/api";

const ENV_LABELS: Record<Environment, string> = {
  filesystem: "Filesystem",
  database: "Database",
  research_assistant: "Research assistant",
};

export function TryPlayground() {
  const [caps, setCaps] = useState<Capabilities | null>(null);
  const [capsError, setCapsError] = useState<string | null>(null);
  const [provider, setProvider] = useState<Provider>("mock");
  const [environment, setEnvironment] = useState<Environment>("filesystem");
  const [condition, setCondition] = useState<Condition>("C5");
  const [interactions, setInteractions] = useState(10);
  const [seed, setSeed] = useState(42);
  const [monitor, setMonitor] = useState(true);
  const [intervene, setIntervene] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<RunResponse | null>(null);

  useEffect(() => {
    fetchCapabilities()
      .then((c) => {
        setCaps(c);
        if (!c.providers.includes("deepseek")) {
          setProvider("mock");
        }
      })
      .catch((e: Error) => setCapsError(e.message));
  }, []);

  const maxIx =
    caps?.max_interactions?.[provider] ?? (provider === "deepseek" ? 8 : 30);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    setResult(null);
    try {
      let run = await startRun({
        provider,
        environment,
        condition,
        interactions: Math.min(interactions, maxIx),
        seed,
        enable_monitoring: condition === "C5" ? monitor : false,
        enable_intervention: condition === "C5" ? intervene : false,
      });

      const deadline = Date.now() + (provider === "deepseek" ? 180_000 : 90_000);
      while (
        (run.status === "queued" || run.status === "running") &&
        Date.now() < deadline
      ) {
        await new Promise((r) => setTimeout(r, 1500));
        run = await getRun(run.run_id);
      }
      setResult(run);
      if (run.status === "failed") {
        setError(run.error || "Run failed");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  const summary = result?.summary;
  const plots = result?.plots || {};

  return (
    <div className="try-layout">
      <form className="try-form" onSubmit={onSubmit}>
        <label>
          Provider
          <select
            value={provider}
            onChange={(e) => setProvider(e.target.value as Provider)}
          >
            <option value="mock">Mock (instant)</option>
            {caps?.deepseek_available !== false && (
              <option value="deepseek" disabled={!caps?.deepseek_available}>
                DeepSeek
              </option>
            )}
          </select>
        </label>

        <label>
          Environment
          <select
            value={environment}
            onChange={(e) => setEnvironment(e.target.value as Environment)}
          >
            {(caps?.environments || Object.keys(ENV_LABELS)).map((env) => (
              <option key={env} value={env}>
                {ENV_LABELS[env as Environment] || env}
              </option>
            ))}
          </select>
        </label>

        <fieldset className="radio-row">
          <legend>Condition</legend>
          <label>
            <input
              type="radio"
              name="condition"
              checked={condition === "C1"}
              onChange={() => setCondition("C1")}
            />
            C1 — Stateless baseline
          </label>
          <label>
            <input
              type="radio"
              name="condition"
              checked={condition === "C5"}
              onChange={() => setCondition("C5")}
            />
            C5 — SafeAdapt (full)
          </label>
        </fieldset>

        <label>
          Interactions ({interactions} / max {maxIx})
          <input
            type="range"
            min={1}
            max={maxIx}
            value={Math.min(interactions, maxIx)}
            onChange={(e) => setInteractions(Number(e.target.value))}
          />
        </label>

        <label>
          Seed
          <input
            type="number"
            value={seed}
            onChange={(e) => setSeed(Number(e.target.value))}
          />
        </label>

        {condition === "C5" && (
          <div className="toggle-row">
            <label>
              <input
                type="checkbox"
                checked={monitor}
                onChange={(e) => setMonitor(e.target.checked)}
              />
              Drift monitoring
            </label>
            <label>
              <input
                type="checkbox"
                checked={intervene}
                onChange={(e) => setIntervene(e.target.checked)}
              />
              Interventions
            </label>
          </div>
        )}

        <button type="submit" className="btn primary" disabled={busy}>
          {busy ? "Running…" : "Run experiment"}
        </button>

        {capsError && (
          <p className="form-hint warn">
            API unreachable ({capsError}). Set NEXT_PUBLIC_API_URL to your Render
            service.
          </p>
        )}
        {error && <p className="form-hint warn">{error}</p>}
      </form>

      <div className="try-output" aria-live="polite">
        {!result && !busy && (
          <p className="muted">
            Submit a short run. Mock finishes in seconds; DeepSeek is capped at{" "}
            {caps?.max_interactions?.deepseek ?? 8} interactions.
          </p>
        )}
        {busy && <p className="pulse">Experiment in progress…</p>}
        {summary && (
          <div className="metrics-grid">
            <Metric label="Mean alignment" value={fmt(summary.mean_alignment)} />
            <Metric
              label="Violation rate"
              value={fmt(summary.violation_rate)}
            />
            <Metric
              label="Drift detections"
              value={String(summary.drift_detections ?? 0)}
            />
            <Metric
              label="Interventions"
              value={String(summary.intervention_count ?? 0)}
            />
            <Metric
              label="Tasks completed"
              value={String(summary.tasks_completed ?? 0)}
            />
            <Metric
              label="Status"
              value={result?.status ?? "—"}
            />
          </div>
        )}
        {Object.keys(plots).length > 0 && (
          <div className="plot-grid">
            {Object.entries(plots)
              .slice(0, 4)
              .map(([name, b64]) => (
                // eslint-disable-next-line @next/next/no-img-element
                <figure key={name}>
                  <img src={plotSrc(b64)} alt={name} />
                  <figcaption>{name.replace(/^\d+_/, "").replace(".png", "")}</figcaption>
                </figure>
              ))}
          </div>
        )}
      </div>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="metric">
      <span className="metric-label">{label}</span>
      <span className="metric-value">{value}</span>
    </div>
  );
}

function fmt(n: number | undefined): string {
  if (n === undefined || Number.isNaN(n)) return "—";
  return n.toFixed(3);
}
