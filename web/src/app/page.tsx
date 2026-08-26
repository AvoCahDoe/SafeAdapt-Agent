import Link from "next/link";

export default function HomePage() {
  return (
    <main className="hero">
      <div className="hero-bg" aria-hidden />
      <div className="hero-grid" aria-hidden />
      <div className="hero-content">
        <h1 className="brand-hero">SafeAdapt</h1>
        <p className="hero-line">
          Measure how agent alignment drifts across long interaction sequences.
        </p>
        <p className="hero-sub">
          Research prototype with mock and live LLM runs, drift monitors, and
          interventions.
        </p>
        <div className="cta-row">
          <Link className="btn primary" href="/results">
            Explore results
          </Link>
          <Link className="btn" href="/try">
            Try it
          </Link>
        </div>
      </div>
    </main>
  );
}
