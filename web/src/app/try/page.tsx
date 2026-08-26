import { TryPlayground } from "@/components/TryPlayground";

export default function TryPage() {
  return (
    <main className="page results-page">
      <p className="eyebrow">Interactive demo</p>
      <h1 className="page-title">Try it</h1>
      <p className="page-lead">
        Run a short experiment in three steps. Start with mock SafeAdapt (C5),
        then compare to the baseline (C1).
      </p>
      <TryPlayground />
    </main>
  );
}
