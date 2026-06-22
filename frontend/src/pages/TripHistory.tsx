import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Trash2 } from "lucide-react";

import { api, formatCurrency, formatDate } from "../api/client";
import EmptyState from "../components/EmptyState";
import PageHeader from "../components/PageHeader";
import { Trip } from "../types";

const statuses = ["planned", "active", "completed", "cancelled"];

export default function TripHistory() {
  const queryClient = useQueryClient();
  const tripsQuery = useQuery({
    queryKey: ["trip-history"],
    queryFn: async () => (await api.get<Trip[]>("/trip-history")).data
  });

  const updateStatus = useMutation({
    mutationFn: async ({ id, status }: { id: string; status: string }) => (await api.put<Trip>(`/trips/${id}`, { status })).data,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["trip-history"] });
      queryClient.invalidateQueries({ queryKey: ["trips"] });
      queryClient.invalidateQueries({ queryKey: ["budget-summary"] });
    }
  });

  const deleteTrip = useMutation({
    mutationFn: async (id: string) => api.delete(`/trips/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["trip-history"] });
      queryClient.invalidateQueries({ queryKey: ["trips"] });
      queryClient.invalidateQueries({ queryKey: ["budget-summary"] });
    }
  });

  const trips = tripsQuery.data ?? [];

  return (
    <div>
      <PageHeader title="Trip History" description="Review trips, update status, and remove trips that no longer belong in your plan." />

      {trips.length === 0 ? (
        <EmptyState title="No trips found">Create a trip to start building travel history.</EmptyState>
      ) : (
        <div className="overflow-hidden rounded-lg border border-zinc-200 bg-white">
          {trips.map((trip) => (
            <article key={trip.id} className="grid gap-4 border-b border-zinc-100 p-4 last:border-0 lg:grid-cols-[1fr_180px_150px_48px] lg:items-center">
              <div>
                <h2 className="font-semibold text-zinc-950">{trip.destination}</h2>
                <p className="mt-1 text-sm text-zinc-600">
                  {trip.days} days · {formatCurrency(trip.budget)} · Created {formatDate(trip.created_at)}
                </p>
                <div className="mt-3 flex flex-wrap gap-2">
                  {trip.interests.map((interest) => (
                    <span key={interest} className="rounded-lg bg-zinc-100 px-2 py-1 text-xs text-zinc-700">
                      {interest}
                    </span>
                  ))}
                </div>
              </div>

              <select
                className="field"
                value={trip.status}
                onChange={(event) => updateStatus.mutate({ id: trip.id, status: event.target.value })}
              >
                {statuses.map((status) => (
                  <option key={status} value={status}>
                    {status}
                  </option>
                ))}
              </select>

              <div className="text-sm text-zinc-600">
                <span className="font-semibold text-zinc-950">{formatCurrency(trip.budget)}</span>
              </div>

              <button type="button" className="danger-button h-10 w-10 p-0" aria-label={`Delete ${trip.destination}`} onClick={() => deleteTrip.mutate(trip.id)}>
                <Trash2 className="h-4 w-4" aria-hidden="true" />
              </button>
            </article>
          ))}
        </div>
      )}
    </div>
  );
}
