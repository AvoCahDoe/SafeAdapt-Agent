import Link from "next/link";

export default function HomePage() {
  return (
    <main className="hero">
      <div className="hero-bg" aria-hidden />
      <div className="hero-grid" aria-hidden />
      <div className="hero-content">
        <h1 className="brand-hero">SafeAdapt</h1>
        <p className="hero-line">
          Detect and intervene when LLM agents drift off their goals.
        </p>
        <div className="cta-row">
          <Link className="btn primary" href="/results">
            See results
          </Link>
          <Link className="btn" href="/try">
            Try a run
          </Link>
          <Link className="btn" href="/docs">
            Docs
          </Link>
        </div>
      </div>
    </main>
  );
}
