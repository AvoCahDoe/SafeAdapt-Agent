"use client";

import type { ReactNode } from "react";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
  ZAxis,
} from "recharts";

export type ConditionMetrics = {
  mean_alignment?: number;
  violation_rate?: number;
  drift_detections?: number;
  intervention_count?: number;
  task_completion_rate?: number;
  action_success_rate?: number;
  n_runs?: number;
  per_seed?: {
    mean_alignment?: number[];
    violation_rate?: number[];
    task_completion_rate?: number[];
  };
};

export type SeriesPoint = Record<string, number>;

export type TradeoffPoint = {
  condition: string;
  seed: number;
  alignment?: number;
  violations?: number;
  task_success?: number;
  detections?: number;
  interventions?: number;
};

const tooltipStyle = {
  background: "#102028",
  border: "1px solid rgba(232,240,242,0.12)",
  borderRadius: 2,
  color: "#e8f0f2",
};

const COLORS: Record<string, string> = {
  C1: "#9bb0b8",
  C2: "#7a9aa6",
  C3: "#d9785a",
  C4: "#c4a35a",
  C5: "#3d9a8f",
};

type Props = {
  conditions: Record<string, ConditionMetrics>;
  series: SeriesPoint[];
  tradeoff: TradeoffPoint[];
};

export function ResultsCharts({ conditions, series, tradeoff }: Props) {
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

  const seedBars = order.flatMap((id) => {
    const vals = conditions[id]?.per_seed?.mean_alignment ?? [];
    return vals.map((v, i) => ({
      label: `${id}·s${i + 1}`,
      condition: id,
      alignment: round(v),
    }));
  });

  return (
    <div className="charts-stack">
      <ChartBlock
        title="1. Condition overview"
        interpretation={
          <>
            Across C1–C5, adversarial pressure (C3) is the clearest drop in
            mean alignment and task success. Detection (C4) and full SafeAdapt
            (C5) activate monitoring signals that C1–C3 never produce.
          </>
        }
      >
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={overview} barGap={4}>
            <CartesianGrid stroke="rgba(232,240,242,0.08)" vertical={false} />
            <XAxis dataKey="condition" tick={{ fill: "#9bb0b8", fontSize: 12 }} />
            <YAxis
              domain={[0, 1]}
              tick={{ fill: "#9bb0b8", fontSize: 12 }}
              width={36}
            />
            <Tooltip contentStyle={tooltipStyle} />
            <Legend />
            <Bar dataKey="alignment" name="Mean alignment" fill="#3d9a8f" />
            <Bar dataKey="violations" name="Violation rate" fill="#d9785a" />
            <Bar dataKey="task" name="Task success" fill="#c4a35a" />
          </BarChart>
        </ResponsiveContainer>
      </ChartBlock>

      <ChartBlock
        title="2. Alignment over interactions"
        interpretation={
          <>
            Trajectories from a representative seed. C1 stays relatively
            smooth; C4/C5 show more movement once drift scoring turns on.
            Intervention in C5 does not instantly restore peak alignment in
            this short mock — it mainly reacts to rising <em>D<sub>t</sub></em>.
          </>
        }
      >
        <ResponsiveContainer width="100%" height={320}>
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
              stroke={COLORS.C1}
              strokeWidth={2}
              dot={false}
            />
            <Line
              type="monotone"
              dataKey="c4_alignment"
              name="C4"
              stroke={COLORS.C4}
              strokeWidth={2}
              dot={false}
            />
            <Line
              type="monotone"
              dataKey="c5_alignment"
              name="C5"
              stroke={COLORS.C5}
              strokeWidth={2}
              dot={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </ChartBlock>

      <ChartBlock
        title="3. Cumulative violation rate"
        interpretation={
          <>
            Running violation rate <em>v̄<sub>t</sub></em> climbs as the
            interaction horizon grows. C5 does not eliminate violations in this
            mock regime; the interesting signal is that drift/intervention
            counters rise in parallel (next charts).
          </>
        }
      >
        <ResponsiveContainer width="100%" height={300}>
          <AreaChart data={series}>
            <CartesianGrid stroke="rgba(232,240,242,0.08)" />
            <XAxis dataKey="t" tick={{ fill: "#9bb0b8", fontSize: 12 }} />
            <YAxis
              domain={[0, "auto"]}
              tick={{ fill: "#9bb0b8", fontSize: 12 }}
              width={40}
            />
            <Tooltip contentStyle={tooltipStyle} />
            <Legend />
            <Area
              type="monotone"
              dataKey="c1_violations"
              name="C1"
              stroke={COLORS.C1}
              fill={COLORS.C1}
              fillOpacity={0.15}
            />
            <Area
              type="monotone"
              dataKey="c5_violations"
              name="C5"
              stroke={COLORS.C5}
              fill={COLORS.C5}
              fillOpacity={0.2}
            />
          </AreaChart>
        </ResponsiveContainer>
      </ChartBlock>

      <ChartBlock
        title="4. Drift score Dₜ over time"
        interpretation={
          <>
            C1 has no monitor (score stays near zero). C4 and C5 share the same
            detector, so <em>D<sub>t</sub></em> rises together; C5 then spends
            that signal on interventions.
          </>
        }
      >
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={series}>
            <CartesianGrid stroke="rgba(232,240,242,0.08)" />
            <XAxis dataKey="t" tick={{ fill: "#9bb0b8", fontSize: 12 }} />
            <YAxis tick={{ fill: "#9bb0b8", fontSize: 12 }} width={40} />
            <Tooltip contentStyle={tooltipStyle} />
            <Legend />
            <Line
              type="monotone"
              dataKey="c1_drift"
              name="C1"
              stroke={COLORS.C1}
              strokeWidth={1.5}
              dot={false}
            />
            <Line
              type="monotone"
              dataKey="c4_drift"
              name="C4"
              stroke={COLORS.C4}
              strokeWidth={2}
              strokeDasharray="4 3"
              dot={false}
            />
            <Line
              type="monotone"
              dataKey="c5_drift"
              name="C5"
              stroke={COLORS.C5}
              strokeWidth={2}
              dot={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </ChartBlock>

      <ChartBlock
        title="5. Monitoring & intervention activity"
        interpretation={
          <>
            Only C4/C5 emit drift flags. Only C5 applies interventions (~26 per
            run on average). That is the operational difference of the full
            SafeAdapt loop in this demo.
          </>
        }
      >
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={monitoring} barGap={6}>
            <CartesianGrid stroke="rgba(232,240,242,0.08)" vertical={false} />
            <XAxis dataKey="condition" tick={{ fill: "#9bb0b8", fontSize: 12 }} />
            <YAxis tick={{ fill: "#9bb0b8", fontSize: 12 }} width={36} />
            <Tooltip contentStyle={tooltipStyle} />
            <Legend />
            <Bar dataKey="detections" name="Drift detections" fill="#c4a35a" />
            <Bar
              dataKey="interventions"
              name="Interventions"
              fill="#3d9a8f"
            />
          </BarChart>
        </ResponsiveContainer>
      </ChartBlock>

      <ChartBlock
        title="6. Cumulative interventions (C5)"
        interpretation={
          <>
            Interventions accumulate as severity thresholds are crossed. Early
            horizon is quiet; mid-run activity clusters where drift score is
            elevated.
          </>
        }
      >
        <ResponsiveContainer width="100%" height={260}>
          <AreaChart data={series}>
            <CartesianGrid stroke="rgba(232,240,242,0.08)" />
            <XAxis dataKey="t" tick={{ fill: "#9bb0b8", fontSize: 12 }} />
            <YAxis tick={{ fill: "#9bb0b8", fontSize: 12 }} width={40} />
            <Tooltip contentStyle={tooltipStyle} />
            <Area
              type="stepAfter"
              dataKey="c5_interventions"
              name="C5 interventions (cum.)"
              stroke="#3d9a8f"
              fill="#3d9a8f"
              fillOpacity={0.25}
            />
          </AreaChart>
        </ResponsiveContainer>
      </ChartBlock>

      <ChartBlock
        title="7. Safety–performance scatter (per seed)"
        interpretation={
          <>
            Each point is one seed. Ideal is high task success and low
            violations (upper-left). C3 shifts toward worse performance under
            adversarial pressure; C4/C5 sit between baseline and C3.
          </>
        }
      >
        <ResponsiveContainer width="100%" height={320}>
          <ScatterChart margin={{ top: 8, right: 8, bottom: 8, left: 8 }}>
            <CartesianGrid stroke="rgba(232,240,242,0.08)" />
            <XAxis
              type="number"
              dataKey="violations"
              name="violations"
              domain={[0, 0.5]}
              tick={{ fill: "#9bb0b8", fontSize: 12 }}
              label={{
                value: "violation rate",
                position: "insideBottom",
                offset: -2,
                fill: "#9bb0b8",
              }}
            />
            <YAxis
              type="number"
              dataKey="task_success"
              name="task"
              domain={[0.3, 0.8]}
              tick={{ fill: "#9bb0b8", fontSize: 12 }}
              label={{
                value: "task success",
                angle: -90,
                position: "insideLeft",
                fill: "#9bb0b8",
              }}
            />
            <ZAxis range={[60, 60]} />
            <Tooltip
              contentStyle={tooltipStyle}
              cursor={{ strokeDasharray: "3 3" }}
            />
            <Legend />
            {order.map((id) => (
              <Scatter
                key={id}
                name={id}
                data={tradeoff.filter((p) => p.condition === id)}
                fill={COLORS[id]}
              />
            ))}
          </ScatterChart>
        </ResponsiveContainer>
      </ChartBlock>

      <ChartBlock
        title="8. Seed-level mean alignment"
        interpretation={
          <>
            Bars show alignment for each seed (42–44). Variance is modest for
            C1/C2 and larger under C3–C5, which is expected when memory,
            adversaries, and interventions interact.
          </>
        }
      >
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={seedBars}>
            <CartesianGrid stroke="rgba(232,240,242,0.08)" vertical={false} />
            <XAxis
              dataKey="label"
              tick={{ fill: "#9bb0b8", fontSize: 10 }}
              interval={0}
              angle={-35}
              textAnchor="end"
              height={60}
            />
            <YAxis
              domain={[0.5, 0.85]}
              tick={{ fill: "#9bb0b8", fontSize: 12 }}
              width={40}
            />
            <Tooltip contentStyle={tooltipStyle} />
            <Bar dataKey="alignment" name="Mean alignment">
              {seedBars.map((row) => (
                <Cell key={row.label} fill={COLORS[row.condition] || "#3d9a8f"} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </ChartBlock>
    </div>
  );
}

function ChartBlock({
  title,
  interpretation,
  children,
}: {
  title: string;
  interpretation: ReactNode;
  children: React.ReactNode;
}) {
  return (
    <figure className="chart-panel">
      <figcaption>{title}</figcaption>
      <div className="chart-frame">{children}</div>
      <p className="interpretation">
        <span className="interpretation-label">Interpretation</span>
        {interpretation}
      </p>
    </figure>
  );
}

function round(n: number | undefined): number {
  if (n === undefined || Number.isNaN(n)) return 0;
  return Math.round(n * 1000) / 1000;
}
