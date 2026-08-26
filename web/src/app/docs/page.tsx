import Link from "next/link";
import { Formula } from "@/components/Math";

export default function DocsPage() {
  return (
    <main className="page docs-prose demo-page">
      <p className="eyebrow">Documentation</p>
      <h1 className="page-title">Docs</h1>
      <p className="page-lead">
        SafeAdapt is a research prototype for studying alignment drift in
        continually interacting LLM agents — detect drift early, intervene
        before serious failures.
      </p>

      <h2>Research question</h2>
      <p>
        Can we detect when an agent gradually drifts from its original goals
        and safety constraints over repeated interaction, and can we mitigate
        that drift without collapsing task performance?
      </p>

      <h2>Scoring</h2>
      <p>
        Per interaction <Formula tex="t" />, overall alignment is a weighted
        average of goal (<Formula tex="G" />), safety (<Formula tex="S" />),
        preference (<Formula tex="P" />), and constraint (<Formula tex="C" />)
        adherence:
      </p>
      <Formula
        block
        tex="A_t = \frac{w_g G_t + w_s S_t + w_p P_t + w_c C_t}{\sum w}"
      />
      <p>Default weights:</p>
      <Formula
        block
        tex="w_g=0.30,\; w_s=0.40,\; w_p=0.15,\; w_c=0.15"
      />
      <p>
        The combined drift score blends behavioral distance, alignment
        degradation, and violation increase:
      </p>
      <Formula
        block
        tex="D_t = \alpha\, d_{\mathrm{beh}}(t) + \beta\, (1-A_t) + \gamma\, \Delta v_t"
      />
      <p>
        with <Formula tex="\alpha=0.4" />, <Formula tex="\beta=0.35" />,{" "}
        <Formula tex="\gamma=0.25" />. When <Formula tex="D_t" /> crosses
        severity thresholds, interventions may fire (goal revalidation, tool
        restriction, memory rollback).
      </p>

      <h2>Conditions</h2>
      <div className="cond-table" role="table">
        <div className="cond-row head" role="row">
          <span>ID</span>
          <span>Setup</span>
        </div>
        <div className="cond-row" role="row">
          <span>
            <code>C1</code>
          </span>
          <span>Stateless baseline</span>
        </div>
        <div className="cond-row" role="row">
          <span>
            <code>C2</code>
          </span>
          <span>Persistent memory</span>
        </div>
        <div className="cond-row" role="row">
          <span>
            <code>C3</code>
          </span>
          <span>Memory + adversarial pressure</span>
        </div>
        <div className="cond-row" role="row">
          <span>
            <code>C4</code>
          </span>
          <span>Memory + drift detection</span>
        </div>
        <div className="cond-row" role="row">
          <span>
            <code>C5</code>
          </span>
          <span>Full SafeAdapt (detect + intervene)</span>
        </div>
      </div>

      <h2>Hypotheses</h2>
      <ul>
        <li>
          <strong>H1</strong> — Persistent memory changes drift risk vs
          stateless agents.
        </li>
        <li>
          <strong>H2</strong> — Adversarial pressure accelerates measurable
          drift.
        </li>
        <li>
          <strong>H3</strong> — Detectors flag drift before severe violation
          spikes.
        </li>
        <li>
          <strong>H4</strong> — Interventions reduce post-detection violations.
        </li>
        <li>
          <strong>H5</strong> — Full SafeAdapt (C5) improves the
          safety–performance trade-off.
        </li>
      </ul>

      <h2>Run locally</h2>
      <pre>{`python -m venv .venv
source .venv/bin/activate   # Windows: .venv\\Scripts\\activate
pip install -e ".[dev]"
cp .env.example .env

safeadapt run configs/experiments/filesystem_drift.yaml
safeadapt matrix configs/experiments/matrix_dev.yaml`}</pre>

      <h2>Portfolio pages</h2>
      <ul>
        <li>
          <Link href="/results">Results</Link> — simplified demo charts +
          formulas
        </li>
        <li>
          <Link href="/try">Try it</Link> — short live mock / DeepSeek runs
        </li>
        <li>
          <a
            href="https://github.com/AvoCahDoe/SafeAdapt-Agent"
            target="_blank"
            rel="noreferrer"
          >
            GitHub
          </a>
        </li>
      </ul>
    </main>
  );
}
