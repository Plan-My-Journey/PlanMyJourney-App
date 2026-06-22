import { FormEvent, useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ReceiptText, Save } from "lucide-react";

import { api, formatCurrency, formatDate } from "../api/client";
import EmptyState from "../components/EmptyState";
import PageHeader from "../components/PageHeader";
import { Expense, Trip } from "../types";

export default function ExpenseTracker() {
  const queryClient = useQueryClient();
  const [selectedTripId, setSelectedTripId] = useState("");
  const [category, setCategory] = useState("food");
  const [amount, setAmount] = useState("45");
  const [description, setDescription] = useState("Dinner");

  const tripsQuery = useQuery({
    queryKey: ["trips"],
    queryFn: async () => (await api.get<Trip[]>("/trips")).data
  });

  const trips = tripsQuery.data ?? [];

  useEffect(() => {
    if (!selectedTripId && trips.length > 0) {
      setSelectedTripId(trips[0].id);
    }
  }, [selectedTripId, trips]);

  const expensesQuery = useQuery({
    queryKey: ["expenses", selectedTripId],
    queryFn: async () => (await api.get<Expense[]>(`/expenses/${selectedTripId}`)).data,
    enabled: Boolean(selectedTripId)
  });

  const createExpense = useMutation({
    mutationFn: async () =>
      (
        await api.post<Expense>("/expenses", {
          trip_id: selectedTripId,
          category,
          amount: Number(amount),
          description
        })
      ).data,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["expenses", selectedTripId] });
      queryClient.invalidateQueries({ queryKey: ["budget-summary"] });
      setAmount("");
      setDescription("");
    }
  });

  const expenses = expensesQuery.data ?? [];
  const selectedTrip = trips.find((trip) => trip.id === selectedTripId);
  const totalSpent = useMemo(() => expenses.reduce((sum, expense) => sum + Number(expense.amount), 0), [expenses]);

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    if (selectedTripId) {
      createExpense.mutate();
    }
  };

  return (
    <div>
      <PageHeader title="Expense Tracker" description="Log trip spending by category and compare it against your planned budget." />

      {trips.length === 0 ? (
        <EmptyState title="No trips available">Create a trip before adding expenses.</EmptyState>
      ) : (
        <div className="grid gap-5 xl:grid-cols-[0.75fr_1.25fr]">
          <form onSubmit={handleSubmit} className="space-y-4 rounded-lg border border-zinc-200 bg-white p-4">
            <label className="block space-y-2">
              <span className="label">Trip</span>
              <select className="field" value={selectedTripId} onChange={(event) => setSelectedTripId(event.target.value)}>
                {trips.map((trip) => (
                  <option key={trip.id} value={trip.id}>
                    {trip.destination}
                  </option>
                ))}
              </select>
            </label>

            <label className="block space-y-2">
              <span className="label">Category</span>
              <select className="field" value={category} onChange={(event) => setCategory(event.target.value)}>
                <option value="hotel">Hotel</option>
                <option value="food">Food</option>
                <option value="transport">Transport</option>
                <option value="activities">Activities</option>
                <option value="shopping">Shopping</option>
                <option value="other">Other</option>
              </select>
            </label>

            <label className="block space-y-2">
              <span className="label">Amount</span>
              <input className="field" type="number" min="0.01" step="0.01" value={amount} onChange={(event) => setAmount(event.target.value)} required />
            </label>

            <label className="block space-y-2">
              <span className="label">Description</span>
              <textarea className="field min-h-24" value={description} onChange={(event) => setDescription(event.target.value)} />
            </label>

            {createExpense.isError && <div className="rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">Could not save expense.</div>}

            <button type="submit" className="primary-button w-full" disabled={createExpense.isPending || !selectedTripId}>
              <Save className="h-4 w-4" aria-hidden="true" />
              {createExpense.isPending ? "Saving" : "Save Expense"}
            </button>
          </form>

          <section className="rounded-lg border border-zinc-200 bg-white p-4">
            <div className="mb-4 flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
              <div>
                <h2 className="text-lg font-semibold text-zinc-950">{selectedTrip?.destination ?? "Trip"} Expenses</h2>
                <p className="text-sm text-zinc-600">Trip budget {formatCurrency(selectedTrip?.budget)}</p>
              </div>
              <div className="rounded-lg bg-teal-50 px-3 py-2 text-sm font-semibold text-teal-700">Spent {formatCurrency(totalSpent)}</div>
            </div>

            {expenses.length === 0 ? (
              <EmptyState title="No expenses logged" />
            ) : (
              <div className="space-y-2">
                {expenses.map((expense) => (
                  <div key={expense.id} className="grid gap-3 rounded-lg border border-zinc-200 p-3 md:grid-cols-[40px_1fr_auto] md:items-center">
                    <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-amber-50 text-amber-700">
                      <ReceiptText className="h-4 w-4" aria-hidden="true" />
                    </div>
                    <div>
                      <p className="font-semibold capitalize text-zinc-950">{expense.category}</p>
                      <p className="text-sm text-zinc-600">
                        {expense.description || "No description"} · {formatDate(expense.created_at)}
                      </p>
                    </div>
                    <p className="font-semibold text-zinc-950">{formatCurrency(expense.amount)}</p>
                  </div>
                ))}
              </div>
            )}
          </section>
        </div>
      )}
    </div>
  );
}
