import { TryPlayground } from "@/components/TryPlayground";

export default function TryPage() {
  return (
    <main className="page results-page">
      <p className="eyebrow">Interactive</p>
      <h1 className="page-title">Try it</h1>
      <p className="page-lead">
        Configure and run a short experiment. Results include metrics and plots
        with a short note on what each figure shows.
      </p>
      <TryPlayground />
    </main>
  );
}
