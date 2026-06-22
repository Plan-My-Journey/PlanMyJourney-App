import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { CalendarDays, CloudSun, Hotel, PlusCircle, WalletCards } from "lucide-react";

import { api, formatCurrency, formatDate } from "../api/client";
import EmptyState from "../components/EmptyState";
import PageHeader from "../components/PageHeader";
import { BudgetSummary, HotelResponse, Trip, WeatherResponse } from "../types";

function StatCard({ label, value, tone, icon: Icon }: { label: string; value: string; tone: string; icon: typeof WalletCards }) {
  return (
    <div className="rounded-lg border border-zinc-200 bg-white p-4">
      <div className="flex items-center justify-between gap-3">
        <p className="text-sm text-zinc-600">{label}</p>
        <div className={`flex h-9 w-9 items-center justify-center rounded-lg ${tone}`}>
          <Icon className="h-4 w-4" aria-hidden="true" />
        </div>
      </div>
      <p className="mt-3 text-2xl font-semibold text-zinc-950">{value}</p>
    </div>
  );
}

export default function Dashboard() {
  const tripsQuery = useQuery({
    queryKey: ["trips"],
    queryFn: async () => (await api.get<Trip[]>("/trips")).data
  });

  const budgetQuery = useQuery({
    queryKey: ["budget-summary"],
    queryFn: async () => (await api.get<BudgetSummary>("/trips/budget-summary")).data
  });

  const trips = tripsQuery.data ?? [];
  const primaryCity = trips[0]?.destination;

  const weatherQuery = useQuery({
    queryKey: ["weather", primaryCity],
    queryFn: async () => (await api.get<WeatherResponse>(`/weather/${primaryCity}`)).data,
    enabled: Boolean(primaryCity)
  });

  const hotelsQuery = useQuery({
    queryKey: ["hotels", primaryCity],
    queryFn: async () => (await api.get<HotelResponse>(`/hotels/${primaryCity}`)).data,
    enabled: Boolean(primaryCity)
  });

  const upcomingTrips = trips.filter((trip) => trip.status !== "completed").slice(0, 3);
  const recentTrips = trips.slice(0, 5);

  return (
    <div>
      <PageHeader
        title="Dashboard"
        description="Track planned travel, budget exposure, weather, hotels, and recent trip activity."
        actions={
          <Link to="/create-trip" className="primary-button">
            <PlusCircle className="h-4 w-4" aria-hidden="true" />
            New Trip
          </Link>
        }
      />

      <div className="grid gap-4 md:grid-cols-3">
        <StatCard label="Total Trip Budget" value={formatCurrency(budgetQuery.data?.total_budget)} tone="bg-teal-50 text-teal-700" icon={WalletCards} />
        <StatCard label="Spent" value={formatCurrency(budgetQuery.data?.total_spent)} tone="bg-rose-50 text-rose-700" icon={WalletCards} />
        <StatCard label="Trips Planned" value={String(trips.length)} tone="bg-amber-50 text-amber-700" icon={CalendarDays} />
      </div>

      <div className="mt-5 grid gap-5 xl:grid-cols-[1.3fr_0.7fr]">
        <section className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-semibold text-zinc-950">Upcoming Trips</h2>
            <Link to="/history" className="text-sm font-semibold text-teal-700 hover:text-teal-800">
              View all
            </Link>
          </div>
          {upcomingTrips.length === 0 ? (
            <EmptyState title="No upcoming trips yet">
              <Link to="/create-trip" className="font-semibold text-teal-700">
                Create your first trip
              </Link>
            </EmptyState>
          ) : (
            <div className="grid gap-3 md:grid-cols-2">
              {upcomingTrips.map((trip) => (
                <article key={trip.id} className="rounded-lg border border-zinc-200 bg-white p-4">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <h3 className="font-semibold text-zinc-950">{trip.destination}</h3>
                      <p className="mt-1 text-sm text-zinc-600">
                        {trip.days} days · {formatCurrency(trip.budget)}
                      </p>
                    </div>
                    <span className="rounded-lg bg-teal-50 px-2 py-1 text-xs font-semibold text-teal-700">{trip.status}</span>
                  </div>
                  <div className="mt-3 flex flex-wrap gap-2">
                    {trip.interests.map((interest) => (
                      <span key={interest} className="rounded-lg bg-zinc-100 px-2 py-1 text-xs text-zinc-700">
                        {interest}
                      </span>
                    ))}
                  </div>
                </article>
              ))}
            </div>
          )}

          <div>
            <h2 className="mb-3 text-base font-semibold text-zinc-950">Recent Trips</h2>
            <div className="overflow-hidden rounded-lg border border-zinc-200 bg-white">
              {recentTrips.length === 0 ? (
                <div className="p-4 text-sm text-zinc-600">No trip history found.</div>
              ) : (
                recentTrips.map((trip) => (
                  <div key={trip.id} className="flex flex-col gap-2 border-b border-zinc-100 p-4 last:border-0 md:flex-row md:items-center md:justify-between">
                    <div>
                      <p className="font-medium text-zinc-950">{trip.destination}</p>
                      <p className="text-sm text-zinc-600">{formatDate(trip.created_at)}</p>
                    </div>
                    <p className="text-sm font-semibold text-zinc-900">{formatCurrency(trip.budget)}</p>
                  </div>
                ))
              )}
            </div>
          </div>
        </section>

        <aside className="space-y-5">
          <section className="rounded-lg border border-zinc-200 bg-white p-4">
            <div className="mb-3 flex items-center gap-2">
              <CloudSun className="h-4 w-4 text-amber-600" aria-hidden="true" />
              <h2 className="text-base font-semibold text-zinc-950">Weather Widget</h2>
            </div>
            {weatherQuery.data ? (
              <div>
                <p className="text-sm text-zinc-600">{weatherQuery.data.city}</p>
                <p className="mt-2 text-3xl font-semibold text-zinc-950">{Math.round(weatherQuery.data.temperature_c)}°C</p>
                <p className="mt-1 text-sm text-zinc-600">
                  {weatherQuery.data.condition} · Humidity {weatherQuery.data.humidity}%
                </p>
              </div>
            ) : (
              <p className="text-sm text-zinc-600">Create a trip to see destination weather.</p>
            )}
          </section>

          <section className="rounded-lg border border-zinc-200 bg-white p-4">
            <div className="mb-3 flex items-center gap-2">
              <Hotel className="h-4 w-4 text-teal-700" aria-hidden="true" />
              <h2 className="text-base font-semibold text-zinc-950">Hotel Recommendations</h2>
            </div>
            <div className="space-y-3">
              {(hotelsQuery.data?.hotels ?? []).slice(0, 3).map((hotel) => (
                <div key={hotel.name} className="border-b border-zinc-100 pb-3 last:border-0 last:pb-0">
                  <p className="text-sm font-semibold text-zinc-950">{hotel.name}</p>
                  <p className="mt-1 text-xs text-zinc-600">{hotel.address}</p>
                  <p className="mt-1 text-xs text-amber-700">{hotel.rating ? `${hotel.rating.toFixed(1)} rating` : "Rating unavailable"}</p>
                </div>
              ))}
              {!hotelsQuery.data && <p className="text-sm text-zinc-600">Hotel matches appear after a trip is available.</p>}
            </div>
          </section>
        </aside>
      </div>
    </div>
  );
}
