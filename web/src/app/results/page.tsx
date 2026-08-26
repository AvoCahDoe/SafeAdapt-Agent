import { readFile } from "fs/promises";
import path from "path";
import Link from "next/link";
import { Formula } from "@/components/Math";
import {
  ResultsCharts,
  type ConditionMetrics,
  type SeriesPoint,
  type TradeoffPoint,
} from "@/components/ResultsCharts";

type MetricsFile = {
  headline?: string;
  setup?: {
    environment?: string;
    interactions?: number;
    seeds?: number[];
    conditions?: string[];
    provider?: string;
  };
  conditions?: Record<string, ConditionMetrics>;
  deltas?: {
    alignment_c5_minus_c1?: number;
    violation_c5_minus_c1?: number;
    task_c5_minus_c1?: number;
    detections_c5?: number;
    interventions_c5?: number;
  };
};

type SeriesFile = {
  note?: string;
  series?: SeriesPoint[];
};

type TradeoffFile = {
  points?: TradeoffPoint[];
};

async function loadJson<T>(rel: string): Promise<T | null> {
  try {
    const p = path.join(process.cwd(), "public", "showcase", rel);
    return JSON.parse(await readFile(p, "utf8")) as T;
  } catch {
    return null;
  }
}

const CONDITION_BLURBS: Record<string, string> = {
  C1: "Stateless baseline",
  C2: "Persistent memory",
  C3: "Memory + adversarial pressure",
  C4: "Memory + drift detection",
  C5: "Full SafeAdapt (detect + intervene)",
};

export default async function ResultsPage() {
  const metrics = await loadJson<MetricsFile>("metrics.json");
  const seriesFile = await loadJson<SeriesFile>("demo_series.json");
  const tradeoffFile = await loadJson<TradeoffFile>("tradeoff.json");

  const conditions = metrics?.conditions ?? {};
  const setup = metrics?.setup;
  const deltas = metrics?.deltas;
  const series = seriesFile?.series ?? [];
  const tradeoff = tradeoffFile?.points ?? [];
  const order = (setup?.conditions ?? Object.keys(conditions)).filter(
    (c) => conditions[c]
  );

  return (
    <main className="page results-page">
      <header className="results-hero">
        <p className="eyebrow">Portfolio demo · mock matrix</p>
        <h1 className="page-title">Results</h1>
        <p className="page-lead">
          {metrics?.headline ||
            "Condition comparison for SafeAdapt on a filesystem agent environment."}
        </p>
        <nav className="toc" aria-label="On this page">
          <a href="#setup">Setup</a>
          <a href="#formulas">Formulas</a>
          <a href="#summary">Summary table</a>
          <a href="#charts">Charts</a>
          <a href="#findings">Findings</a>
        </nav>
      </header>

      <section id="setup" className="section">
        <h2>Experimental setup</h2>
        <div className="setup-grid">
          <div>
            <span className="metric-label">Provider</span>
            <span className="metric-value sm">{setup?.provider ?? "mock"}</span>
          </div>
          <div>
            <span className="metric-label">Environment</span>
            <span className="metric-value sm">
              {setup?.environment ?? "filesystem"}
            </span>
          </div>
          <div>
            <span className="metric-label">Interactions</span>
            <span className="metric-value sm">
              {setup?.interactions ?? "—"}
            </span>
          </div>
          <div>
            <span className="metric-label">Seeds</span>
            <span className="metric-value sm">
              {(setup?.seeds ?? []).join(", ") || "—"}
            </span>
          </div>
        </div>
        <div className="cond-table" role="table">
          <div className="cond-row head" role="row">
            <span>Condition</span>
            <span>Meaning</span>
          </div>
          {order.map((id) => (
            <div className="cond-row" role="row" key={id}>
              <span>
                <code>{id}</code>
              </span>
              <span>{CONDITION_BLURBS[id] ?? id}</span>
            </div>
          ))}
        </div>
      </section>

      <section id="formulas" className="section formula-strip">
        <h2>Metrics & formulas</h2>
        <p className="muted">
          Each interaction <Formula tex="t" /> produces adherence scores for
          goal, safety, preference, and constraints. Overall alignment is their
          weighted mean:
        </p>
        <Formula
          block
          tex="A_t = \frac{w_g G_t + w_s S_t + w_p P_t + w_c C_t}{w_g+w_s+w_p+w_c}"
        />
        <p className="muted">
          Defaults{" "}
          <Formula tex="(w_g,w_s,w_p,w_c)=(0.30,0.40,0.15,0.15)" />. Run-level
          mean alignment is
        </p>
        <Formula
          block
          tex="\bar{A} = \frac{1}{T}\sum_{t=1}^{T} A_t"
        />
        <p className="muted">
          Drift combines behavioral distance, alignment degradation, and
          violation increase:
        </p>
        <Formula
          block
          tex="D_t = \alpha\, d_{\mathrm{beh}}(t) + \beta\,(1-A_t) + \gamma\,\Delta v_t"
        />
        <p className="muted">
          with <Formula tex="\alpha=0.4,\;\beta=0.35,\;\gamma=0.25" />. When{" "}
          <Formula tex="D_t" /> crosses severity thresholds, C4 logs a
          detection and C5 may intervene. Violation rate for a run:
        </p>
        <Formula
          block
          tex="v = \frac{\#\{\text{interactions with objective violations}\}}{T}"
        />
        <p className="muted">
          See <Link href="/docs">Docs</Link> for hypotheses H1–H5 and CLI
          reproduction.
        </p>
      </section>

      <section id="summary" className="section">
        <h2>Summary table</h2>
        <div className="table-wrap">
          <table className="results-table">
            <thead>
              <tr>
                <th>Cond.</th>
                <th>
                  <Formula tex="\bar{A}" />
                </th>
                <th>
                  <Formula tex="v" />
                </th>
                <th>Task</th>
                <th>Detections</th>
                <th>Interventions</th>
              </tr>
            </thead>
            <tbody>
              {order.map((id) => {
                const m = conditions[id];
                return (
                  <tr key={id}>
                    <td>
                      <code>{id}</code>
                    </td>
                    <td>{fmt(m?.mean_alignment)}</td>
                    <td>{fmt(m?.violation_rate)}</td>
                    <td>{fmt(m?.task_completion_rate)}</td>
                    <td>{fmtCount(m?.drift_detections)}</td>
                    <td>{fmtCount(m?.intervention_count)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        {deltas && (
          <div className="delta-row">
            <div className="metric">
              <span className="metric-label">Δ alignment (C5−C1)</span>
              <span className="metric-value sm">
                {fmtSigned(deltas.alignment_c5_minus_c1)}
              </span>
            </div>
            <div className="metric">
              <span className="metric-label">Δ violations (C5−C1)</span>
              <span className="metric-value sm">
                {fmtSigned(deltas.violation_c5_minus_c1)}
              </span>
            </div>
            <div className="metric">
              <span className="metric-label">C5 detections / interventions</span>
              <span className="metric-value sm">
                {fmtCount(deltas.detections_c5)} /{" "}
                {fmtCount(deltas.interventions_c5)}
              </span>
            </div>
          </div>
        )}
      </section>

      <section id="charts" className="section">
        <h2>Charts & interpretation</h2>
        <p className="muted chart-intro">
          Interactive Recharts views from the committed mock matrix. Each block
          includes a short reading of what the figure shows.
        </p>
        <ResultsCharts
          conditions={conditions}
          series={series}
          tradeoff={tradeoff}
        />
      </section>

      <section id="findings" className="section findings">
        <h2>Findings (this demo)</h2>
        <ol className="findings-list">
          <li>
            <strong>Adversarial pressure bites.</strong> C3 shows the lowest{" "}
            <Formula tex="\bar{A}" /> and task success — consistent with H2 in
            this mock regime.
          </li>
          <li>
            <strong>Detection is visible.</strong> C4/C5 average ~26 drift
            flags per run; C1–C3 show zero. The monitor is doing measurable
            work.
          </li>
          <li>
            <strong>Intervention is exclusive to C5.</strong> Only the full
            stack applies goal revalidation / tool restriction / rollback (~26
            interventions per run).
          </li>
          <li>
            <strong>Short-horizon caveat.</strong> On this 40-step mock matrix,
            C5 does not beat C1 on mean alignment or violations yet — the demo
            highlights the <em>control loop lighting up</em>, not a final
            claim of superiority. Longer horizons and real LLMs are the next
            stress test (<Link href="/try">Try it</Link>).
          </li>
        </ol>
        <p className="muted">
          Reproduce locally via the CLI in <Link href="/docs">Docs</Link>, or
          regenerate assets with{" "}
          <code>PYTHONPATH=src python scripts/export_showcase.py</code>.
        </p>
      </section>
    </main>
  );
}

function fmt(n: number | undefined): string {
  if (n === undefined || Number.isNaN(n)) return "—";
  return n.toFixed(3);
}

function fmtCount(n: number | undefined): string {
  if (n === undefined || Number.isNaN(n)) return "—";
  return (Math.round(n * 10) / 10).toString();
}

function fmtSigned(n: number | undefined): string {
  if (n === undefined || Number.isNaN(n)) return "—";
  const v = Math.round(n * 1000) / 1000;
  return `${v >= 0 ? "+" : ""}${v.toFixed(3)}`;
}
