import { readFile } from "fs/promises";
import path from "path";
import Link from "next/link";
import { Formula } from "@/components/Math";
import { ResultsCharts, type SeriesPoint } from "@/components/ResultsCharts";

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

type SeriesFile = {
  series: SeriesPoint[];
};

async function loadJson<T>(rel: string): Promise<T | null> {
  try {
    const p = path.join(process.cwd(), "public", "showcase", rel);
    return JSON.parse(await readFile(p, "utf8")) as T;
  } catch {
    return null;
  }
}

export default async function ResultsPage() {
  const metrics = await loadJson<Metrics>("metrics.json");
  const seriesFile = await loadJson<SeriesFile>("demo_series.json");
  const c1 = metrics?.conditions?.C1;
  const c5 = metrics?.conditions?.C5;
  const series = seriesFile?.series ?? [];

  return (
    <main className="page demo-page">
      <p className="eyebrow">Portfolio demo</p>
      <h1 className="page-title">Results</h1>
      <p className="page-lead">
        One comparison: a stateless baseline (<strong>C1</strong>) versus
        SafeAdapt with monitoring and interventions (<strong>C5</strong>).
      </p>

      <section className="section formula-strip">
        <h2>What we measure</h2>
        <p className="muted">
          Alignment is a weighted mix of goal, safety, preference, and
          constraint adherence. Drift combines behavioral change, alignment
          drop, and violation rise.
        </p>
        <Formula
          block
          tex="A_t = \frac{w_g G_t + w_s S_t + w_p P_t + w_c C_t}{w_g + w_s + w_p + w_c}"
        />
        <Formula
          block
          tex="D_t = \alpha\, d_{\mathrm{beh}} + \beta\, (1 - A_t) + \gamma\, \Delta v_t"
        />
        <p className="muted">
          Defaults:{" "}
          <Formula tex="\alpha=0.4,\;\beta=0.35,\;\gamma=0.25" />. Full write-up
          in <Link href="/docs">Docs</Link>.
        </p>
      </section>

      <section className="section">
        <h2>Demo charts</h2>
        <ResultsCharts c1={c1} c5={c5} series={series} />
      </section>

      <section className="section takeaway">
        <h2>Takeaway</h2>
        <p>
          C5 turns on drift flags and interventions (
          {fmtAvg(c5?.drift_detections)} detections,{" "}
          {fmtAvg(c5?.intervention_count)} interventions on average in the mock
          matrix). Explore the live runner on <Link href="/try">Try it</Link>,
          or read the method in <Link href="/docs">Docs</Link>.
        </p>
      </section>
    </main>
  );
}

function fmtAvg(n: number | undefined): string {
  if (n === undefined || Number.isNaN(n)) return "—";
  return String(Math.round(n * 10) / 10);
}
