import { FormEvent, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Sparkles } from "lucide-react";

import { api } from "../api/client";
import DestinationAutocomplete from "../components/DestinationAutocomplete";
import PageHeader from "../components/PageHeader";
import { ItineraryResponse } from "../types";

export default function CreateTrip() {
  const queryClient = useQueryClient();
  const [destination, setDestination] = useState("Kyoto");
  const [budget, setBudget] = useState("2200");
  const [days, setDays] = useState("5");
  const [interests, setInterests] = useState("temples, food, gardens");
  const [itinerary, setItinerary] = useState<ItineraryResponse | null>(null);

  const mutation = useMutation({
    mutationFn: async () => {
      const interestList = interests
        .split(",")
        .map((interest) => interest.trim())
        .filter(Boolean);
      const payload = {
        destination,
        budget: Number(budget),
        days: Number(days),
        interests: interestList,
        status: "planned"
      };
      await api.post("/trips", payload);
      const { data } = await api.post<ItineraryResponse>("/ai/itinerary", payload);
      return data;
    },
    onSuccess: (data) => {
      setItinerary(data);
      queryClient.invalidateQueries({ queryKey: ["trips"] });
      queryClient.invalidateQueries({ queryKey: ["budget-summary"] });
    }
  });

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    mutation.mutate();
  };

  return (
    <div>
      <PageHeader title="Create Trip" description="Generate an AI itinerary and save the trip to your travel history." />

      <div className="grid gap-5 xl:grid-cols-[0.8fr_1.2fr]">
        <form onSubmit={handleSubmit} className="space-y-4 rounded-lg border border-zinc-200 bg-white p-4">
          <label className="block space-y-2">
            <span className="label">Destination</span>
            <DestinationAutocomplete value={destination} onChange={setDestination} placeholder="Start typing a city..." required />
          </label>

          <div className="grid gap-4 sm:grid-cols-2">
            <label className="block space-y-2">
              <span className="label">Budget</span>
              <input className="field" type="number" min="0" value={budget} onChange={(event) => setBudget(event.target.value)} required />
            </label>

            <label className="block space-y-2">
              <span className="label">Days</span>
              <input className="field" type="number" min="1" max="60" value={days} onChange={(event) => setDays(event.target.value)} required />
            </label>
          </div>

          <label className="block space-y-2">
            <span className="label">Interests</span>
            <textarea className="field min-h-28" value={interests} onChange={(event) => setInterests(event.target.value)} />
          </label>

          {mutation.isError && <div className="rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">Could not generate this trip.</div>}

          <button type="submit" className="primary-button w-full" disabled={mutation.isPending}>
            <Sparkles className="h-4 w-4" aria-hidden="true" />
            {mutation.isPending ? "Generating" : "Generate AI Trip"}
          </button>
        </form>

        <section className="rounded-lg border border-zinc-200 bg-white p-4">
          {itinerary ? (
            <div className="space-y-5">
              <div>
                <h2 className="text-lg font-semibold text-zinc-950">Summary</h2>
                <p className="mt-2 text-sm leading-6 text-zinc-700">{itinerary.trip_summary}</p>
              </div>

              <div>
                <h2 className="mb-3 text-lg font-semibold text-zinc-950">Day Wise Plan</h2>
                <div className="space-y-3">
                  {itinerary.day_wise_plan.map((day) => (
                    <article key={day.day} className="rounded-lg border border-zinc-200 p-3">
                      <h3 className="font-semibold text-zinc-950">
                        Day {day.day}: {day.title}
                      </h3>
                      <div className="mt-2 grid gap-2 text-sm text-zinc-700 md:grid-cols-3">
                        <p>
                          <span className="font-semibold text-zinc-900">Morning:</span> {day.morning}
                        </p>
                        <p>
                          <span className="font-semibold text-zinc-900">Afternoon:</span> {day.afternoon}
                        </p>
                        <p>
                          <span className="font-semibold text-zinc-900">Evening:</span> {day.evening}
                        </p>
                      </div>
                    </article>
                  ))}
                </div>
              </div>

              <div className="grid gap-4 md:grid-cols-2">
                <div>
                  <h2 className="mb-2 text-lg font-semibold text-zinc-950">Budget Breakdown</h2>
                  <div className="space-y-2 text-sm">
                    {Object.entries(itinerary.estimated_budget_breakdown).map(([key, value]) => (
                      <div key={key} className="flex justify-between gap-3 border-b border-zinc-100 py-2">
                        <span className="capitalize text-zinc-600">{key.replace(/_/g, " ")}</span>
                        <span className="font-semibold text-zinc-950">{value}</span>
                      </div>
                    ))}
                  </div>
                </div>

                <div>
                  <h2 className="mb-2 text-lg font-semibold text-zinc-950">Travel Tips</h2>
                  <ul className="space-y-2 text-sm text-zinc-700">
                    {itinerary.travel_tips.map((tip) => (
                      <li key={tip} className="rounded-lg bg-zinc-100 px-3 py-2">
                        {tip}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          ) : (
            <div className="flex min-h-80 items-center justify-center rounded-lg border border-dashed border-zinc-300 text-sm text-zinc-600">
              Your generated itinerary will appear here.
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
