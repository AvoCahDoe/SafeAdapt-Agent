"use client";

import { useEffect, useMemo, useState } from "react";
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

const ENV_HELP: Record<Environment, string> = {
  filesystem: "Agent reads/writes files under safety constraints.",
  database: "Agent queries a simulated database with access rules.",
  research_assistant: "Agent answers research tasks; may see injected docs.",
};

type Preset = {
  id: string;
  title: string;
  blurb: string;
  provider: Provider;
  environment: Environment;
  condition: Condition;
  interactions: number;
  seed: number;
  monitor: boolean;
  intervene: boolean;
};

const PRESETS: Preset[] = [
  {
    id: "quick-c1",
    title: "Baseline (C1)",
    blurb: "No memory, no monitoring — see the control case.",
    provider: "mock",
    environment: "filesystem",
    condition: "C1",
    interactions: 10,
    seed: 42,
    monitor: false,
    intervene: false,
  },
  {
    id: "quick-c5",
    title: "SafeAdapt (C5)",
    blurb: "Full stack: detect drift and intervene.",
    provider: "mock",
    environment: "filesystem",
    condition: "C5",
    interactions: 10,
    seed: 42,
    monitor: true,
    intervene: true,
  },
];

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
  const [phase, setPhase] = useState<"idle" | "queued" | "running" | "done">(
    "idle"
  );
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<RunResponse | null>(null);
  const [activePreset, setActivePreset] = useState<string>("quick-c5");
  const [showAdvanced, setShowAdvanced] = useState(false);

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
    if (provider === "mock") return "Usually a few seconds";
    return "Often 30–90s (API cold start + LLM calls)";
  }, [provider]);

  function applyPreset(p: Preset) {
    setActivePreset(p.id);
    setProvider(p.provider);
    setEnvironment(p.environment);
    setCondition(p.condition);
    setInteractions(p.interactions);
    setSeed(p.seed);
    setMonitor(p.monitor);
    setIntervene(p.intervene);
    setError(null);
  }

  async function runExperiment() {
    setBusy(true);
    setError(null);
    setResult(null);
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

      setPhase(run.status === "completed" ? "done" : "running");
      const deadline = Date.now() + (provider === "deepseek" ? 180_000 : 90_000);
      while (
        (run.status === "queued" || run.status === "running") &&
        Date.now() < deadline
      ) {
        setPhase(run.status === "queued" ? "queued" : "running");
        await new Promise((r) => setTimeout(r, 1500));
        run = await getRun(run.run_id);
      }
      setResult(run);
      setPhase("done");
      if (run.status === "failed") {
        setError(run.error || "Run failed");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
      setPhase("idle");
    } finally {
      setBusy(false);
    }
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    await runExperiment();
  }

  const summary = result?.summary;
  const plots = result?.plots || {};
  const plotEntries = Object.entries(plots).slice(0, 4);

  return (
    <div className="try-layout">
      <div className="try-controls">
        <section className="try-step">
          <h2 className="try-step-title">
            <span className="step-num">1</span> Pick a quick start
          </h2>
          <p className="muted try-step-help">
            Best for a portfolio demo: run mock C1, then C5, and compare.
          </p>
          <div className="preset-row">
            {PRESETS.map((p) => (
              <button
                key={p.id}
                type="button"
                className={`preset-card ${activePreset === p.id ? "active" : ""}`}
                onClick={() => applyPreset(p)}
                disabled={busy}
              >
                <strong>{p.title}</strong>
                <span>{p.blurb}</span>
              </button>
            ))}
          </div>
        </section>

        <form className="try-form" onSubmit={onSubmit}>
          <section className="try-step">
            <h2 className="try-step-title">
              <span className="step-num">2</span> Confirm settings
            </h2>

            <div className="choice-row">
              <button
                type="button"
                className={`choice-pill ${provider === "mock" ? "active" : ""}`}
                onClick={() => {
                  setProvider("mock");
                  setActivePreset("");
                }}
                disabled={busy}
              >
                Mock · fast
              </button>
              <button
                type="button"
                className={`choice-pill ${provider === "deepseek" ? "active" : ""}`}
                onClick={() => {
                  setProvider("deepseek");
                  setActivePreset("");
                }}
                disabled={busy || !caps?.deepseek_available}
                title={
                  caps?.deepseek_available
                    ? "Live DeepSeek LLM (slower)"
                    : "DeepSeek unavailable on API"
                }
              >
                DeepSeek · live LLM
              </button>
            </div>
            <p className="form-hint">{estimate}</p>

            <fieldset className="radio-row">
              <legend>What to compare</legend>
              <label className={`choice-block ${condition === "C1" ? "on" : ""}`}>
                <input
                  type="radio"
                  name="condition"
                  checked={condition === "C1"}
                  onChange={() => {
                    setCondition("C1");
                    setActivePreset("");
                  }}
                />
                <span>
                  <strong>C1 — Baseline</strong>
                  <em>Stateless agent, no drift monitor</em>
                </span>
              </label>
              <label className={`choice-block ${condition === "C5" ? "on" : ""}`}>
                <input
                  type="radio"
                  name="condition"
                  checked={condition === "C5"}
                  onChange={() => {
                    setCondition("C5");
                    setActivePreset("");
                  }}
                />
                <span>
                  <strong>C5 — SafeAdapt</strong>
                  <em>Monitor drift + intervene when needed</em>
                </span>
              </label>
            </fieldset>

            <label>
              How many interactions?{" "}
              <strong className="accent-text">{safeInteractions}</strong>
              <input
                type="range"
                min={3}
                max={maxIx}
                value={safeInteractions}
                onChange={(e) => {
                  setInteractions(Number(e.target.value));
                  setActivePreset("");
                }}
              />
              <span className="range-ends">
                <span>3</span>
                <span>max {maxIx}</span>
              </span>
            </label>

            <button
              type="button"
              className="linkish"
              onClick={() => setShowAdvanced((v) => !v)}
            >
              {showAdvanced ? "Hide advanced" : "Show advanced"}
            </button>

            {showAdvanced && (
              <div className="advanced-block">
                <label>
                  Environment
                  <select
                    value={environment}
                    onChange={(e) => {
                      setEnvironment(e.target.value as Environment);
                      setActivePreset("");
                    }}
                  >
                    {(caps?.environments || Object.keys(ENV_HELP)).map((env) => (
                      <option key={env} value={env}>
                        {env.replace(/_/g, " ")}
                      </option>
                    ))}
                  </select>
                  <span className="form-hint">{ENV_HELP[environment]}</span>
                </label>
                <label>
                  Random seed
                  <input
                    type="number"
                    value={seed}
                    onChange={(e) => {
                      setSeed(Number(e.target.value));
                      setActivePreset("");
                    }}
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
                      Enable drift monitoring
                    </label>
                    <label>
                      <input
                        type="checkbox"
                        checked={intervene}
                        onChange={(e) => setIntervene(e.target.checked)}
                      />
                      Enable interventions
                    </label>
                  </div>
                )}
              </div>
            )}
          </section>

          <section className="try-step">
            <h2 className="try-step-title">
              <span className="step-num">3</span> Run
            </h2>
            <button type="submit" className="btn primary try-run" disabled={busy}>
              {busy ? "Running experiment…" : "Run experiment"}
            </button>
            {busy && (
              <p className="pulse">
                {phase === "queued"
                  ? "Queued on the API…"
                  : "Running interactions…"}
              </p>
            )}
            {capsError && (
              <p className="form-hint warn">
                API unreachable right now ({capsError}). The free API may be
                waking from sleep — wait ~30s and try again.
              </p>
            )}
            {error && <p className="form-hint warn">{error}</p>}
          </section>
        </form>
      </div>

      <div className="try-output" aria-live="polite">
        <h2 className="try-output-title">Results</h2>
        {!result && !busy && (
          <div className="try-empty">
            <p>
              Nothing yet. Start with <strong>SafeAdapt (C5)</strong>, then run{" "}
              <strong>Baseline (C1)</strong> with the same seed to compare.
            </p>
            <ul className="try-tips">
              <li>Mock = free &amp; instant (best for demos)</li>
              <li>DeepSeek = real LLM, capped &amp; slower</li>
              <li>Watch alignment, violations, and interventions below</li>
            </ul>
          </div>
        )}
        {busy && (
          <div className="try-empty">
            <p className="pulse">Experiment in progress…</p>
            <p className="muted">{estimate}</p>
          </div>
        )}
        {summary && (
          <>
            <p className="try-result-banner">
              Finished <code>{condition}</code> · {provider} · {safeInteractions}{" "}
              interactions · seed {seed}
            </p>
            <div className="metrics-grid">
              <Metric
                label="Mean alignment"
                value={fmt(summary.mean_alignment)}
                hint="Higher is better"
              />
              <Metric
                label="Violation rate"
                value={fmt(summary.violation_rate)}
                hint="Lower is better"
              />
              <Metric
                label="Drift detections"
                value={String(summary.drift_detections ?? 0)}
                hint="C5 monitor alerts"
              />
              <Metric
                label="Interventions"
                value={String(summary.intervention_count ?? 0)}
                hint="Only C5 acts"
              />
              <Metric
                label="Tasks completed"
                value={String(summary.tasks_completed ?? 0)}
                hint="Useful work done"
              />
              <Metric
                label="Status"
                value={result?.status ?? "—"}
                hint="API job state"
              />
            </div>
            {plotEntries.length > 0 && (
              <div className="plot-grid">
                {plotEntries.map(([name, b64]) => (
                  // eslint-disable-next-line @next/next/no-img-element
                  <figure key={name}>
                    <img src={plotSrc(b64)} alt={name} />
                    <figcaption>
                      {name
                        .replace(/^\d+_/, "")
                        .replace(".png", "")
                        .replace(/_/g, " ")}
                    </figcaption>
                  </figure>
                ))}
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
