import { readFile } from "fs/promises";
import path from "path";

type Metrics = {
  conditions?: Record<
    string,
    {
      mean_alignment?: number;
      violation_rate?: number;
      drift_detections?: number;
      intervention_count?: number;
      task_completion_rate?: number;
    }
  >;
  headline?: string;
};

async function loadMetrics(): Promise<Metrics | null> {
  try {
    const p = path.join(process.cwd(), "public", "showcase", "metrics.json");
    const raw = await readFile(p, "utf8");
    return JSON.parse(raw) as Metrics;
  } catch {
    return null;
  }
}

const PLOTS = [
  {
    src: "/showcase/08_condition_comparison.png",
    caption: "Condition comparison (C1 vs C5)",
  },
  { src: "/showcase/01_alignment.png", caption: "Alignment over interactions" },
  { src: "/showcase/03_drift.png", caption: "Drift signal" },
  {
    src: "/showcase/04_drift_interventions.png",
    caption: "Drift and interventions",
  },
];

export default async function ResultsPage() {
  const metrics = await loadMetrics();
  const c1 = metrics?.conditions?.C1;
  const c5 = metrics?.conditions?.C5;

  return (
    <main className="page">
      <h1 className="page-title">Results showcase</h1>
      <p className="page-lead">
        {metrics?.headline ||
          "Pre-baked mock matrix sample: C1 (stateless baseline) versus C5 (SafeAdapt full stack)."}
      </p>

      {(c1 || c5) && (
        <section className="section">
          <h2>Key metrics</h2>
          <div className="metrics-grid">
            <div className="metric">
              <span className="metric-label">C1 mean alignment</span>
              <span className="metric-value">{fmt(c1?.mean_alignment)}</span>
            </div>
            <div className="metric">
              <span className="metric-label">C5 mean alignment</span>
              <span className="metric-value">{fmt(c5?.mean_alignment)}</span>
            </div>
            <div className="metric">
              <span className="metric-label">C1 violation rate</span>
              <span className="metric-value">{fmt(c1?.violation_rate)}</span>
            </div>
            <div className="metric">
              <span className="metric-label">C5 violation rate</span>
              <span className="metric-value">{fmt(c5?.violation_rate)}</span>
            </div>
            <div className="metric">
              <span className="metric-label">C5 interventions</span>
              <span className="metric-value">
                {c5?.intervention_count ?? "—"}
              </span>
            </div>
            <div className="metric">
              <span className="metric-label">C5 drift detections</span>
              <span className="metric-value">
                {c5?.drift_detections ?? "—"}
              </span>
            </div>
          </div>
        </section>
      )}

      <section className="section">
        <h2>Plots</h2>
        <div className="plot-grid">
          {PLOTS.map((p) => (
            <figure key={p.src}>
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={p.src} alt={p.caption} />
              <figcaption>{p.caption}</figcaption>
            </figure>
          ))}
        </div>
      </section>
    </main>
  );
}

function fmt(n: number | undefined): string {
  if (n === undefined || Number.isNaN(n)) return "—";
  return n.toFixed(3);
}
