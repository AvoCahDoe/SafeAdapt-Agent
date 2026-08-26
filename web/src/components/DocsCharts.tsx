"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { ConditionMetrics } from "@/components/ResultsCharts";

const tooltipStyle = {
  background: "#102028",
  border: "1px solid rgba(232,240,242,0.12)",
  borderRadius: 2,
  color: "#e8f0f2",
};

type SeriesPoint = Record<string, number>;

type Props = {
  conditions: Record<string, ConditionMetrics>;
  series: SeriesPoint[];
};

export function DocsCharts({ conditions, series }: Props) {
  const order = ["C1", "C2", "C3", "C4", "C5"].filter((c) => conditions[c]);
  const overview = order.map((id) => ({
    condition: id,
    alignment: round(conditions[id]?.mean_alignment),
    violations: round(conditions[id]?.violation_rate),
    task: round(conditions[id]?.task_completion_rate),
  }));
  const monitoring = order.map((id) => ({
    condition: id,
    detections: round(conditions[id]?.drift_detections),
    interventions: round(conditions[id]?.intervention_count),
  }));

  return (
    <div className="docs-charts">
      <figure className="chart-panel">
        <figcaption>Mean rates by condition</figcaption>
        <div className="chart-frame">
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={overview}>
              <CartesianGrid stroke="rgba(232,240,242,0.08)" vertical={false} />
              <XAxis dataKey="condition" tick={{ fill: "#9bb0b8", fontSize: 12 }} />
              <YAxis domain={[0, 1]} tick={{ fill: "#9bb0b8", fontSize: 12 }} width={36} />
              <Tooltip contentStyle={tooltipStyle} />
              <Legend />
              <Bar dataKey="alignment" name="Alignment" fill="#3d9a8f" />
              <Bar dataKey="violations" name="Violations" fill="#d9785a" />
              <Bar dataKey="task" name="Task success" fill="#c4a35a" />
            </BarChart>
          </ResponsiveContainer>
        </div>
        <p className="chart-note">
          C3 (adversarial) drops alignment and task success; C4/C5 add monitoring
          signals not present in C1–C3.
        </p>
      </figure>

      <figure className="chart-panel">
        <figcaption>Detection & intervention counts</figcaption>
        <div className="chart-frame">
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={monitoring}>
              <CartesianGrid stroke="rgba(232,240,242,0.08)" vertical={false} />
              <XAxis dataKey="condition" tick={{ fill: "#9bb0b8", fontSize: 12 }} />
              <YAxis tick={{ fill: "#9bb0b8", fontSize: 12 }} width={36} />
              <Tooltip contentStyle={tooltipStyle} />
              <Legend />
              <Bar dataKey="detections" name="Detections" fill="#c4a35a" />
              <Bar dataKey="interventions" name="Interventions" fill="#3d9a8f" />
            </BarChart>
          </ResponsiveContainer>
        </div>
        <p className="chart-note">
          Only C4/C5 emit drift flags; only C5 applies interventions — the
          control loop lighting up.
        </p>
      </figure>

      {series.length > 0 && (
        <figure className="chart-panel">
          <figcaption>Alignment trajectory (sample seed)</figcaption>
          <div className="chart-frame">
            <ResponsiveContainer width="100%" height={280}>
              <LineChart data={series}>
                <CartesianGrid stroke="rgba(232,240,242,0.08)" />
                <XAxis dataKey="t" tick={{ fill: "#9bb0b8", fontSize: 12 }} />
                <YAxis
                  domain={[0.4, 1]}
                  tick={{ fill: "#9bb0b8", fontSize: 12 }}
                  width={40}
                />
                <Tooltip contentStyle={tooltipStyle} />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="c1_alignment"
                  name="C1"
                  stroke="#9bb0b8"
                  strokeWidth={2}
                  dot={false}
                />
                <Line
                  type="monotone"
                  dataKey="c5_alignment"
                  name="C5"
                  stroke="#3d9a8f"
                  strokeWidth={2}
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
          <p className="chart-note">
            Short-horizon mock runs; see Results for the full chart suite and
            written findings.
          </p>
        </figure>
      )}
    </div>
  );
}

function round(n: number | undefined): number {
  if (n === undefined || Number.isNaN(n)) return 0;
  return Math.round(n * 1000) / 1000;
}
