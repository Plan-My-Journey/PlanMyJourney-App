import { FormEvent, useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { GitCompare, Sparkles } from "lucide-react";

import { api } from "../api/client";
import PageHeader from "../components/PageHeader";
import { DestinationComparison as DestinationComparisonType } from "../types";

function ComparisonBlock({ title, values }: { title: string; values: Record<string, string> }) {
  return (
    <section className="rounded-lg border border-zinc-200 bg-white p-4">
      <h2 className="mb-3 text-base font-semibold text-zinc-950">{title}</h2>
      <div className="space-y-3">
        {Object.entries(values).map(([key, value]) => (
          <div key={key} className="rounded-lg bg-zinc-100 p-3">
            <p className="text-sm font-semibold text-zinc-950">{key}</p>
            <p className="mt-1 text-sm leading-6 text-zinc-700">{value}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

export default function DestinationComparison() {
  const [destinationA, setDestinationA] = useState("Kyoto");
  const [destinationB, setDestinationB] = useState("Seoul");
  const [comparison, setComparison] = useState<DestinationComparisonType | null>(null);

  const mutation = useMutation({
    mutationFn: async () =>
      (
        await api.post<DestinationComparisonType>("/ai/compare", {
          destination_a: destinationA,
          destination_b: destinationB
        })
      ).data,
    onSuccess: setComparison
  });

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    mutation.mutate();
  };

  return (
    <div>
      <PageHeader title="Destination Comparison" description="Compare destinations across costs, weather, activities, and final fit." />

      <form onSubmit={handleSubmit} className="mb-5 grid gap-3 rounded-lg border border-zinc-200 bg-white p-4 md:grid-cols-[1fr_1fr_auto] md:items-end">
        <label className="block space-y-2">
          <span className="label">Destination A</span>
          <input className="field" value={destinationA} onChange={(event) => setDestinationA(event.target.value)} required />
        </label>
        <label className="block space-y-2">
          <span className="label">Destination B</span>
          <input className="field" value={destinationB} onChange={(event) => setDestinationB(event.target.value)} required />
        </label>
        <button type="submit" className="primary-button" disabled={mutation.isPending}>
          <GitCompare className="h-4 w-4" aria-hidden="true" />
          {mutation.isPending ? "Comparing" : "Compare"}
        </button>
      </form>

      {mutation.isError && <div className="mb-4 rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">Comparison failed.</div>}

      {comparison ? (
        <div className="space-y-5">
          <div className="rounded-lg border border-teal-200 bg-teal-50 p-4">
            <div className="mb-2 flex items-center gap-2 text-teal-800">
              <Sparkles className="h-4 w-4" aria-hidden="true" />
              <h2 className="font-semibold">Best Choice</h2>
            </div>
            <p className="text-sm leading-6 text-teal-900">{comparison.best_choice}</p>
          </div>

          <div className="grid gap-5 lg:grid-cols-3">
            <ComparisonBlock title="Cost" values={comparison.cost_comparison} />
            <ComparisonBlock title="Weather" values={comparison.weather_comparison} />
            <ComparisonBlock title="Activities" values={comparison.activity_comparison} />
          </div>
        </div>
      ) : (
        <div className="rounded-lg border border-dashed border-zinc-300 bg-white p-8 text-center text-sm text-zinc-600">Run a comparison to see AI recommendations.</div>
      )}
    </div>
  );
}
