"use client";

import { useEffect, useMemo, useState } from "react";
import {
  Capabilities,
  Condition,
  Environment,
  Provider,
  RunProgress,
  RunResponse,
  fetchCapabilities,
  getRun,
  plotSrc,
  startRun,
} from "@/lib/api";

const ENV_HELP: Record<Environment, string> = {
  filesystem: "Agent reads/writes files under safety constraints.",
  database: "Agent queries a simulated database with access rules.",
  research_assistant: "Agent answers research tasks; may see injected docs.",
};

const PLOT_INFO: Record<string, { title: string; meaning: string }> = {
  "01_alignment.png": {
    title: "Alignment over time",
    meaning:
      "Overall alignment Aₜ at each interaction. Higher means closer to goal, safety, preference, and constraint targets.",
  },
  "02_violations.png": {
    title: "Violations",
    meaning:
      "When objective constraint violations occur across the run. Spikes indicate safety/policy breaches.",
  },
  "03_drift.png": {
    title: "Drift score",
    meaning:
      "Combined drift Dₜ from behavior change, alignment drop, and violation rise. Used by the monitor.",
  },
  "04_drift_interventions.png": {
    title: "Drift & interventions",
    meaning:
      "Drift trajectory with intervention markers. Shows when SafeAdapt acted after a detection.",
  },
  "05_performance_vs_safety.png": {
    title: "Performance vs safety",
    meaning:
      "Trade-off view of task/useful work against safety-related outcomes for this run.",
  },
  "06_lead_time.png": {
    title: "Lead time",
    meaning:
      "How early drift signals appear relative to later failures or violations (when data allows).",
  },
  "07_action_distribution.png": {
    title: "Action distribution",
    meaning:
      "Which tools/actions the agent chose before vs after drift signals (when available).",
  },
  "08_condition_comparison.png": {
    title: "Condition comparison",
    meaning: "Aggregate comparison across experimental conditions.",
  },
  "09_intervention_recovery.png": {
    title: "Intervention recovery",
    meaning:
      "Alignment just before vs after interventions — whether the control loop recovers Aₜ.",
  },
};

export function TryPlayground() {
  const [caps, setCaps] = useState<Capabilities | null>(null);
  const [capsError, setCapsError] = useState<string | null>(null);
  const [provider, setProvider] = useState<Provider>("mock");
  const [environment, setEnvironment] = useState<Environment>("filesystem");
  const [condition, setCondition] = useState<Condition>("C5");
  const [interactions, setInteractions] = useState(12);
  const [seed, setSeed] = useState(42);
  const [monitor, setMonitor] = useState(true);
  const [intervene, setIntervene] = useState(true);
  const [busy, setBusy] = useState(false);
  const [phase, setPhase] = useState<"idle" | "queued" | "running" | "done">(
    "idle"
  );
  const [progress, setProgress] = useState<RunProgress | null>(null);
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
  const safeInteractions = Math.min(interactions, maxIx);

  const estimate = useMemo(() => {
    if (provider === "mock") {
      if (safeInteractions >= 20) return "Larger mock runs may take 10–40s";
      return "Mock runs usually finish in a few seconds";
    }
    return "Live LLM runs are slower (often 30–120s+)";
  }, [provider, safeInteractions]);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    setResult(null);
    setProgress({ current: 0, total: safeInteractions, pct: 0 });
    setPhase("queued");
    try {
      let run = await startRun({
        provider,
        environment,
        condition,
        interactions: safeInteractions,
        seed,
        enable_monitoring: condition === "C5" ? monitor : false,
        enable_intervention: condition === "C5" ? intervene : false,
      });

      if (run.progress) setProgress(run.progress);
      setPhase(run.status === "completed" ? "done" : "running");

      const deadline =
        Date.now() +
        (provider === "deepseek"
          ? 240_000
          : Math.max(90_000, safeInteractions * 2500));

      while (
        (run.status === "queued" || run.status === "running") &&
        Date.now() < deadline
      ) {
        setPhase(run.status === "queued" ? "queued" : "running");
        if (run.progress) setProgress(run.progress);
        await new Promise((r) => setTimeout(r, 800));
        run = await getRun(run.run_id);
      }

      if (run.progress) setProgress(run.progress);
      setResult(run);
      setPhase("done");
      if (run.status === "failed") {
        setError(run.error || "Run failed");
      } else if (run.status === "queued" || run.status === "running") {
        setError("Timed out waiting for the run to finish. Try fewer interactions.");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
      setPhase("idle");
    } finally {
      setBusy(false);
    }
  }

  const summary = result?.summary;
  const plots = result?.plots || {};
  const plotEntries = Object.entries(plots);
  const pct = progress?.pct ?? 0;
  const showDetailedProgress = busy || phase === "running" || phase === "queued";

  return (
    <div className="try-layout">
      <form className="try-form try-controls" onSubmit={onSubmit}>
        <section className="try-step">
          <h2 className="try-step-title">Configure</h2>
          <p className="muted try-step-help">
            Choose provider, condition, environment, and horizon. You control
            every setting.
          </p>

          <label>
            Provider
            <select
              value={provider}
              onChange={(e) => setProvider(e.target.value as Provider)}
              disabled={busy}
            >
              <option value="mock">Mock (deterministic, fast)</option>
              <option value="deepseek" disabled={!caps?.deepseek_available}>
                DeepSeek (live LLM)
              </option>
            </select>
            <span className="form-hint">{estimate}</span>
          </label>

          <label>
            Environment
            <select
              value={environment}
              onChange={(e) =>
                setEnvironment(e.target.value as Environment)
              }
              disabled={busy}
            >
              {(caps?.environments || Object.keys(ENV_HELP)).map((env) => (
                <option key={env} value={env}>
                  {env.replace(/_/g, " ")}
                </option>
              ))}
            </select>
            <span className="form-hint">{ENV_HELP[environment]}</span>
          </label>

          <fieldset className="radio-row">
            <legend>Condition</legend>
            <label className={`choice-block ${condition === "C1" ? "on" : ""}`}>
              <input
                type="radio"
                name="condition"
                checked={condition === "C1"}
                disabled={busy}
                onChange={() => setCondition("C1")}
              />
              <span>
                <strong>C1 — Baseline</strong>
                <em>Stateless agent, no drift monitor or interventions</em>
              </span>
            </label>
            <label className={`choice-block ${condition === "C5" ? "on" : ""}`}>
              <input
                type="radio"
                name="condition"
                checked={condition === "C5"}
                disabled={busy}
                onChange={() => setCondition("C5")}
              />
              <span>
                <strong>C5 — SafeAdapt</strong>
                <em>Persistent memory, drift detection, interventions</em>
              </span>
            </label>
          </fieldset>

          <label>
            Interactions:{" "}
            <strong className="accent-text">{safeInteractions}</strong>
            <input
              type="range"
              min={1}
              max={maxIx}
              value={safeInteractions}
              disabled={busy}
              onChange={(e) => setInteractions(Number(e.target.value))}
            />
            <span className="range-ends">
              <span>1</span>
              <span>max {maxIx}</span>
            </span>
            {safeInteractions >= 15 && (
              <span className="form-hint">
                Longer runs stream progress while the API works through each
                interaction.
              </span>
            )}
          </label>

          <label>
            Seed
            <input
              type="number"
              value={seed}
              disabled={busy}
              onChange={(e) => setSeed(Number(e.target.value))}
            />
            <span className="form-hint">
              Same seed + settings → reproducible mock behavior.
            </span>
          </label>

          {condition === "C5" && (
            <div className="toggle-row">
              <label>
                <input
                  type="checkbox"
                  checked={monitor}
                  disabled={busy}
                  onChange={(e) => setMonitor(e.target.checked)}
                />
                Drift monitoring
              </label>
              <label>
                <input
                  type="checkbox"
                  checked={intervene}
                  disabled={busy}
                  onChange={(e) => setIntervene(e.target.checked)}
                />
                Interventions
              </label>
            </div>
          )}
        </section>

        <section className="try-step">
          <h2 className="try-step-title">Run</h2>
          <button type="submit" className="btn primary try-run" disabled={busy}>
            {busy ? "Running…" : "Run experiment"}
          </button>

          {showDetailedProgress && (
            <div className="progress-block" aria-live="polite">
              <div className="progress-meta">
                <span>
                  {phase === "queued"
                    ? "Queued…"
                    : `Interaction ${progress?.current ?? 0} / ${progress?.total ?? safeInteractions}`}
                </span>
                <span>{pct.toFixed(0)}%</span>
              </div>
              <div
                className="progress-track"
                role="progressbar"
                aria-valuemin={0}
                aria-valuemax={100}
                aria-valuenow={pct}
              >
                <div
                  className="progress-fill"
                  style={{ width: `${Math.min(100, Math.max(2, pct))}%` }}
                />
              </div>
              <p className="form-hint">{estimate}</p>
            </div>
          )}

          {capsError && (
            <p className="form-hint warn">
              API unreachable ({capsError}). If the service was idle it may need
              ~30s to wake — retry shortly.
            </p>
          )}
          {error && <p className="form-hint warn">{error}</p>}
        </section>
      </form>

      <div className="try-output" aria-live="polite">
        <h2 className="try-output-title">Results</h2>
        {!result && !busy && (
          <div className="try-empty">
            <p>
              Configure a run on the left. Metrics and plots appear here when
              the experiment finishes.
            </p>
          </div>
        )}
        {busy && (
          <div className="try-empty">
            <p className="pulse">
              {phase === "queued"
                ? "Waiting for the API…"
                : `Working through interaction ${(progress?.current ?? 0) || 1} of ${progress?.total ?? safeInteractions}…`}
            </p>
            <div className="progress-block">
              <div className="progress-track">
                <div
                  className="progress-fill"
                  style={{ width: `${Math.min(100, Math.max(2, pct))}%` }}
                />
              </div>
            </div>
          </div>
        )}
        {summary && (
          <>
            <p className="try-result-banner">
              Finished <code>{condition}</code> · {provider} ·{" "}
              {safeInteractions} interactions · seed {seed}
            </p>
            <div className="metrics-grid">
              <Metric
                label="Mean alignment"
                value={fmt(summary.mean_alignment)}
                hint="Average Aₜ — higher is better"
              />
              <Metric
                label="Violation rate"
                value={fmt(summary.violation_rate)}
                hint="Share of steps with objective violations"
              />
              <Metric
                label="Drift detections"
                value={String(summary.drift_detections ?? 0)}
                hint="Times the monitor flagged drift"
              />
              <Metric
                label="Interventions"
                value={String(summary.intervention_count ?? 0)}
                hint="Control actions applied (C5)"
              />
              <Metric
                label="Tasks completed"
                value={String(summary.tasks_completed ?? 0)}
                hint="Successful workload steps"
              />
              <Metric
                label="Task completion rate"
                value={fmt(summary.task_completion_rate)}
                hint="Tasks completed / interactions"
              />
            </div>
            {plotEntries.length > 0 && (
              <div className="plot-grid try-plots">
                {plotEntries.map(([name, b64]) => {
                  const info = PLOT_INFO[name] ?? {
                    title: name.replace(/^\d+_/, "").replace(".png", "").replace(/_/g, " "),
                    meaning: "Generated plot from this run.",
                  };
                  return (
                    <figure key={name} className="plot-card">
                      {/* eslint-disable-next-line @next/next/no-img-element */}
                      <img src={plotSrc(b64)} alt={info.title} />
                      <figcaption>
                        <strong>{info.title}</strong>
                        <span>{info.meaning}</span>
                      </figcaption>
                    </figure>
                  );
                })}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}

function Metric({
  label,
  value,
  hint,
}: {
  label: string;
  value: string;
  hint?: string;
}) {
  return (
    <div className="metric">
      <span className="metric-label">{label}</span>
      <span className="metric-value">{value}</span>
      {hint && <span className="metric-hint">{hint}</span>}
    </div>
  );
}

function fmt(n: number | undefined): string {
  if (n === undefined || Number.isNaN(n)) return "—";
  return n.toFixed(3);
}
