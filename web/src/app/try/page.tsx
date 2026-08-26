import { TryPlayground } from "@/components/TryPlayground";

export default function TryPage() {
  return (
    <main className="page">
      <h1 className="page-title">Try SafeAdapt</h1>
      <p className="page-lead">
        Run a short interactive experiment against the public API. Mock is
        default; DeepSeek is capped for cost and latency.
      </p>
      <TryPlayground />
    </main>
  );
}
