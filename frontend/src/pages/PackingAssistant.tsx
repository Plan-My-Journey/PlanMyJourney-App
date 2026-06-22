import { FormEvent, useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { Check, Luggage } from "lucide-react";

import { api } from "../api/client";
import PageHeader from "../components/PageHeader";
import { PackingResponse } from "../types";

export default function PackingAssistant() {
  const [destination, setDestination] = useState("Kyoto");
  const [travelMonth, setTravelMonth] = useState("April");
  const [packing, setPacking] = useState<PackingResponse | null>(null);
  const [checked, setChecked] = useState<Record<string, boolean>>({});

  const mutation = useMutation({
    mutationFn: async () =>
      (
        await api.post<PackingResponse>("/ai/packing-list", {
          destination,
          travel_month: travelMonth
        })
      ).data,
    onSuccess: (data) => {
      setPacking(data);
      setChecked({});
    }
  });

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    mutation.mutate();
  };

  const toggleItem = (key: string) => {
    setChecked((current) => ({ ...current, [key]: !current[key] }));
  };

  return (
    <div>
      <PageHeader title="Packing Assistant" description="Build a month-aware packing checklist for your destination." />

      <form onSubmit={handleSubmit} className="mb-5 grid gap-3 rounded-lg border border-zinc-200 bg-white p-4 md:grid-cols-[1fr_240px_auto] md:items-end">
        <label className="block space-y-2">
          <span className="label">Destination</span>
          <input className="field" value={destination} onChange={(event) => setDestination(event.target.value)} required />
        </label>
        <label className="block space-y-2">
          <span className="label">Month</span>
          <input className="field" value={travelMonth} onChange={(event) => setTravelMonth(event.target.value)} required />
        </label>
        <button type="submit" className="primary-button" disabled={mutation.isPending}>
          <Luggage className="h-4 w-4" aria-hidden="true" />
          {mutation.isPending ? "Building" : "Build List"}
        </button>
      </form>

      {mutation.isError && <div className="mb-4 rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">Packing list failed.</div>}

      {packing ? (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {packing.packing_list.map((group) => (
            <section key={group.category} className="rounded-lg border border-zinc-200 bg-white p-4">
              <h2 className="mb-3 font-semibold text-zinc-950">{group.category}</h2>
              <div className="space-y-2">
                {group.items.map((item) => {
                  const key = `${group.category}:${item}`;
                  return (
                    <label key={key} className="flex cursor-pointer items-center gap-3 rounded-lg border border-zinc-200 px-3 py-2 text-sm text-zinc-700">
                      <input type="checkbox" className="h-4 w-4 rounded border-zinc-300 text-teal-700 focus:ring-teal-600" checked={Boolean(checked[key])} onChange={() => toggleItem(key)} />
                      <span className={checked[key] ? "text-zinc-400 line-through" : ""}>{item}</span>
                      {checked[key] && <Check className="ml-auto h-4 w-4 text-teal-700" aria-hidden="true" />}
                    </label>
                  );
                })}
              </div>
            </section>
          ))}
        </div>
      ) : (
        <div className="rounded-lg border border-dashed border-zinc-300 bg-white p-8 text-center text-sm text-zinc-600">Your checklist will appear here.</div>
      )}
    </div>
  );
}
