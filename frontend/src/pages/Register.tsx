import { FormEvent, useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { Plane, UserPlus } from "lucide-react";

import { useAuth } from "../context/AuthContext";

export default function Register() {
  const { register, token } = useAuth();
  const navigate = useNavigate();
  const [name, setName] = useState("Demo Traveler");
  const [email, setEmail] = useState("demo@example.com");
  const [password, setPassword] = useState("StrongPass123");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  if (token) {
    return <Navigate to="/" replace />;
  }

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setError("");
    setLoading(true);
    try {
      await register(name, email, password);
      navigate("/", { replace: true });
    } catch {
      setError("Registration failed. Use a different email or stronger password.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-zinc-100 px-4">
      <div className="grid w-full max-w-5xl overflow-hidden rounded-lg bg-white shadow-panel md:grid-cols-[0.95fr_1.05fr]">
        <div className="hidden bg-zinc-950 p-8 text-white md:flex md:flex-col md:justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-amber-500 text-zinc-950">
              <Plane className="h-5 w-5" aria-hidden="true" />
            </div>
            <span className="font-semibold">AI Travel Planner</span>
          </div>
          <div className="space-y-3">
            <p className="text-3xl font-semibold leading-tight">Create trips with AI support from day one.</p>
            <p className="text-sm text-zinc-300">Register once, then build itineraries, compare destinations, and manage budgets.</p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5 p-6 md:p-10">
          <div>
            <h1 className="text-2xl font-semibold text-zinc-950">Register</h1>
            <p className="mt-1 text-sm text-zinc-600">Create your travel planning account.</p>
          </div>

          {error && <div className="rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</div>}

          <label className="block space-y-2">
            <span className="label">Name</span>
            <input className="field" value={name} onChange={(event) => setName(event.target.value)} required minLength={2} />
          </label>

          <label className="block space-y-2">
            <span className="label">Email</span>
            <input className="field" type="email" value={email} onChange={(event) => setEmail(event.target.value)} required />
          </label>

          <label className="block space-y-2">
            <span className="label">Password</span>
            <input className="field" type="password" value={password} onChange={(event) => setPassword(event.target.value)} required minLength={8} />
          </label>

          <button type="submit" className="primary-button w-full" disabled={loading}>
            <UserPlus className="h-4 w-4" aria-hidden="true" />
            {loading ? "Creating account" : "Create account"}
          </button>

          <p className="text-center text-sm text-zinc-600">
            Already registered?{" "}
            <Link className="font-semibold text-teal-700 hover:text-teal-800" to="/login">
              Sign in
            </Link>
          </p>
        </form>
      </div>
    </div>
  );
}
