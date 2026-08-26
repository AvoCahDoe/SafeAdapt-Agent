export default function DocsPage() {
  return (
    <main className="page docs-prose">
      <h1 className="page-title">Docs</h1>
      <p className="page-lead">
        SafeAdapt studies whether alignment drifts as LLM agents interact over
        long horizons — and whether monitoring plus interventions can reduce
        that drift without collapsing task performance.
      </p>

      <h2>Research question</h2>
      <p>
        Do continually interacting agents with persistent memory exhibit
        measurable alignment drift under adversarial and workload pressure, and
        can SafeAdapt&apos;s detect–intervene loop recover alignment earlier
        than a stateless baseline?
      </p>

      <h2>Hypotheses (H1–H5)</h2>
      <ul>
        <li>
          <strong>H1</strong> — Persistent memory increases drift risk versus
          stateless baselines.
        </li>
        <li>
          <strong>H2</strong> — Adversarial pressure accelerates measurable
          drift.
        </li>
        <li>
          <strong>H3</strong> — Rolling / CUSUM / JSD detectors flag drift before
          severe violation spikes.
        </li>
        <li>
          <strong>H4</strong> — Interventions (goal revalidation, tool
          restriction, memory rollback) reduce post-detection violation rates.
        </li>
        <li>
          <strong>H5</strong> — Full SafeAdapt (C5) improves the
          safety–performance trade-off versus C1–C4.
        </li>
      </ul>

      <h2>Conditions</h2>
      <ul>
        <li>
          <code>C1</code> Stateless baseline
        </li>
        <li>
          <code>C2</code> Persistent memory
        </li>
        <li>
          <code>C3</code> Memory + adversarial pressure
        </li>
        <li>
          <code>C4</code> Memory + drift detection
        </li>
        <li>
          <code>C5</code> SafeAdapt (full)
        </li>
      </ul>

      <h2>Run locally (CLI)</h2>
      <pre>{`python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env

safeadapt run configs/experiments/filesystem_drift.yaml
safeadapt matrix configs/experiments/matrix_dev.yaml
safeadapt run configs/experiments/filesystem_deepseek.yaml`}</pre>

      <h2>Source</h2>
      <p>
        <a
          href="https://github.com/AvoCahDoe/SafeAdapt-Agent"
          target="_blank"
          rel="noreferrer"
        >
          github.com/AvoCahDoe/SafeAdapt-Agent
        </a>
      </p>
    </main>
  );
}
