import { FormEvent, useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Save, User } from "lucide-react";

import { api } from "../api/client";
import PageHeader from "../components/PageHeader";
import { useAuth } from "../context/AuthContext";
import { Preference, User as UserType } from "../types";

export default function UserProfile() {
  const queryClient = useQueryClient();
  const auth = useAuth();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [travelStyle, setTravelStyle] = useState("balanced");
  const [preferredBudget, setPreferredBudget] = useState("2500");
  const [interests, setInterests] = useState("food, history, nature");

  const profileQuery = useQuery({
    queryKey: ["profile"],
    queryFn: async () => (await api.get<UserType>("/users/profile")).data
  });

  const preferencesQuery = useQuery({
    queryKey: ["preferences"],
    queryFn: async () => (await api.get<Preference>("/users/preferences")).data
  });

  useEffect(() => {
    if (profileQuery.data) {
      setName(profileQuery.data.name);
      setEmail(profileQuery.data.email);
    }
  }, [profileQuery.data]);

  useEffect(() => {
    if (preferencesQuery.data) {
      setTravelStyle(preferencesQuery.data.travel_style);
      setPreferredBudget(String(preferencesQuery.data.preferred_budget));
      setInterests(preferencesQuery.data.interests.join(", "));
    }
  }, [preferencesQuery.data]);

  const updateProfile = useMutation({
    mutationFn: async () => (await api.put<UserType>("/users/profile", { name, email })).data,
    onSuccess: (data) => {
      auth.setUser(data);
      queryClient.invalidateQueries({ queryKey: ["profile"] });
    }
  });

  const updatePreferences = useMutation({
    mutationFn: async () =>
      (
        await api.put<Preference>("/users/preferences", {
          travel_style: travelStyle,
          preferred_budget: Number(preferredBudget),
          interests: interests
            .split(",")
            .map((interest) => interest.trim())
            .filter(Boolean)
        })
      ).data,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["preferences"] })
  });

  const handleProfileSubmit = (event: FormEvent) => {
    event.preventDefault();
    updateProfile.mutate();
  };

  const handlePreferenceSubmit = (event: FormEvent) => {
    event.preventDefault();
    updatePreferences.mutate();
  };

  return (
    <div>
      <PageHeader title="User Profile" description="Manage account details and travel preferences used across trip planning." />

      <div className="grid gap-5 xl:grid-cols-2">
        <form onSubmit={handleProfileSubmit} className="space-y-4 rounded-lg border border-zinc-200 bg-white p-4">
          <div className="flex items-center gap-2">
            <User className="h-4 w-4 text-teal-700" aria-hidden="true" />
            <h2 className="font-semibold text-zinc-950">Profile</h2>
          </div>

          <label className="block space-y-2">
            <span className="label">Name</span>
            <input className="field" value={name} onChange={(event) => setName(event.target.value)} required minLength={2} />
          </label>

          <label className="block space-y-2">
            <span className="label">Email</span>
            <input className="field" type="email" value={email} onChange={(event) => setEmail(event.target.value)} required />
          </label>

          {updateProfile.isError && <div className="rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">Profile update failed.</div>}
          {updateProfile.isSuccess && <div className="rounded-lg border border-teal-200 bg-teal-50 px-3 py-2 text-sm text-teal-800">Profile saved.</div>}

          <button type="submit" className="primary-button" disabled={updateProfile.isPending}>
            <Save className="h-4 w-4" aria-hidden="true" />
            {updateProfile.isPending ? "Saving" : "Save Profile"}
          </button>
        </form>

        <form onSubmit={handlePreferenceSubmit} className="space-y-4 rounded-lg border border-zinc-200 bg-white p-4">
          <h2 className="font-semibold text-zinc-950">Travel Preferences</h2>

          <label className="block space-y-2">
            <span className="label">Travel Style</span>
            <select className="field" value={travelStyle} onChange={(event) => setTravelStyle(event.target.value)}>
              <option value="budget">Budget</option>
              <option value="balanced">Balanced</option>
              <option value="comfort">Comfort</option>
              <option value="luxury">Luxury</option>
              <option value="adventure">Adventure</option>
            </select>
          </label>

          <label className="block space-y-2">
            <span className="label">Preferred Budget</span>
            <input className="field" type="number" min="0" value={preferredBudget} onChange={(event) => setPreferredBudget(event.target.value)} />
          </label>

          <label className="block space-y-2">
            <span className="label">Interests</span>
            <textarea className="field min-h-24" value={interests} onChange={(event) => setInterests(event.target.value)} />
          </label>

          {updatePreferences.isError && <div className="rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">Preference update failed.</div>}
          {updatePreferences.isSuccess && <div className="rounded-lg border border-teal-200 bg-teal-50 px-3 py-2 text-sm text-teal-800">Preferences saved.</div>}

          <button type="submit" className="primary-button" disabled={updatePreferences.isPending}>
            <Save className="h-4 w-4" aria-hidden="true" />
            {updatePreferences.isPending ? "Saving" : "Save Preferences"}
          </button>
        </form>
      </div>
    </div>
  );
}
