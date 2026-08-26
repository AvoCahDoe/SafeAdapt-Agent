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

export type ConditionMetrics = {
  mean_alignment?: number;
  violation_rate?: number;
  drift_detections?: number;
  intervention_count?: number;
  task_completion_rate?: number;
};

export type SeriesPoint = {
  t: number;
  c1: number;
  c5: number;
  drift: number;
};

const tooltipStyle = {
  background: "#102028",
  border: "1px solid rgba(232,240,242,0.12)",
  borderRadius: 2,
  color: "#e8f0f2",
};

type Props = {
  c1?: ConditionMetrics | null;
  c5?: ConditionMetrics | null;
  series: SeriesPoint[];
};

export function ResultsCharts({ c1, c5, series }: Props) {
  const comparison = [
    {
      metric: "Alignment",
      C1: round(c1?.mean_alignment),
      C5: round(c5?.mean_alignment),
    },
    {
      metric: "Violations",
      C1: round(c1?.violation_rate),
      C5: round(c5?.violation_rate),
    },
    {
      metric: "Task success",
      C1: round(c1?.task_completion_rate),
      C5: round(c5?.task_completion_rate),
    },
  ];

  const activity = [
    {
      metric: "Drift flags",
      C1: c1?.drift_detections ?? 0,
      C5: c5?.drift_detections ?? 0,
    },
    {
      metric: "Interventions",
      C1: c1?.intervention_count ?? 0,
      C5: c5?.intervention_count ?? 0,
    },
  ];

  return (
    <div className="charts-stack">
      <figure className="chart-panel">
        <figcaption>C1 vs C5 — mean rates</figcaption>
        <div className="chart-frame">
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={comparison} barGap={6}>
              <CartesianGrid stroke="rgba(232,240,242,0.08)" vertical={false} />
              <XAxis dataKey="metric" tick={{ fill: "#9bb0b8", fontSize: 12 }} />
              <YAxis
                domain={[0, 1]}
                tick={{ fill: "#9bb0b8", fontSize: 12 }}
                width={36}
              />
              <Tooltip contentStyle={tooltipStyle} />
              <Legend />
              <Bar dataKey="C1" fill="#9bb0b8" radius={[2, 2, 0, 0]} />
              <Bar dataKey="C5" fill="#3d9a8f" radius={[2, 2, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </figure>

      <figure className="chart-panel">
        <figcaption>Monitoring activity</figcaption>
        <div className="chart-frame">
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={activity} barGap={6}>
              <CartesianGrid stroke="rgba(232,240,242,0.08)" vertical={false} />
              <XAxis dataKey="metric" tick={{ fill: "#9bb0b8", fontSize: 12 }} />
              <YAxis tick={{ fill: "#9bb0b8", fontSize: 12 }} width={36} />
              <Tooltip contentStyle={tooltipStyle} />
              <Legend />
              <Bar dataKey="C1" fill="#9bb0b8" radius={[2, 2, 0, 0]} />
              <Bar dataKey="C5" fill="#c4a35a" radius={[2, 2, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </figure>

      <figure className="chart-panel">
        <figcaption>Illustrative alignment over interactions</figcaption>
        <div className="chart-frame">
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={series}>
              <CartesianGrid stroke="rgba(232,240,242,0.08)" />
              <XAxis
                dataKey="t"
                tick={{ fill: "#9bb0b8", fontSize: 12 }}
                label={{
                  value: "interaction t",
                  position: "insideBottom",
                  offset: -2,
                  fill: "#9bb0b8",
                }}
              />
              <YAxis
                domain={[0.5, 1]}
                tick={{ fill: "#9bb0b8", fontSize: 12 }}
                width={40}
              />
              <Tooltip contentStyle={tooltipStyle} />
              <Legend />
              <Line
                type="monotone"
                dataKey="c1"
                name="C1 alignment"
                stroke="#9bb0b8"
                strokeWidth={2}
                dot={false}
              />
              <Line
                type="monotone"
                dataKey="c5"
                name="C5 alignment"
                stroke="#3d9a8f"
                strokeWidth={2}
                dot={false}
              />
              <Line
                type="monotone"
                dataKey="drift"
                name="C5 drift score"
                stroke="#c4a35a"
                strokeWidth={1.5}
                strokeDasharray="4 4"
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
        <p className="chart-note">
          Line chart is a simplified demo trajectory for portfolio storytelling;
          bars use committed mock matrix metrics.
        </p>
      </figure>
    </div>
  );
}

function round(n: number | undefined): number {
  if (n === undefined || Number.isNaN(n)) return 0;
  return Math.round(n * 1000) / 1000;
}
