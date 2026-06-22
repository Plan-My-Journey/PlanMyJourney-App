import { FormEvent, useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { LogIn, Plane } from "lucide-react";

import { useAuth } from "../context/AuthContext";

export default function Login() {
  const { login, loginWithCognito, token, cognitoEnabled } = useAuth();
  const navigate = useNavigate();
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
      await login(email, password);
      navigate("/", { replace: true });
    } catch {
      setError("Login failed. Check your email and password.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-zinc-100 px-4">
      <div className="grid w-full max-w-5xl overflow-hidden rounded-lg bg-white shadow-panel md:grid-cols-[0.95fr_1.05fr]">
        <div className="hidden bg-zinc-950 p-8 text-white md:flex md:flex-col md:justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-teal-600">
              <Plane className="h-5 w-5" aria-hidden="true" />
            </div>
            <span className="font-semibold">AI Travel Planner</span>
          </div>
          <div className="space-y-3">
            <p className="text-3xl font-semibold leading-tight">Plan smarter routes, budgets, and travel days.</p>
            <p className="text-sm text-zinc-300">Trips, AI itineraries, expenses, weather, hotels, and packing live in one workspace.</p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5 p-6 md:p-10">
          <div>
            <h1 className="text-2xl font-semibold text-zinc-950">Login</h1>
            <p className="mt-1 text-sm text-zinc-600">Access your travel dashboard.</p>
          </div>

          {error && <div className="rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</div>}

          <label className="block space-y-2">
            <span className="label">Email</span>
            <input className="field" type="email" value={email} onChange={(event) => setEmail(event.target.value)} required />
          </label>

          <label className="block space-y-2">
            <span className="label">Password</span>
            <input className="field" type="password" value={password} onChange={(event) => setPassword(event.target.value)} required minLength={8} />
          </label>

          <button type="submit" className="primary-button w-full" disabled={loading}>
            <LogIn className="h-4 w-4" aria-hidden="true" />
            {loading ? "Signing in" : "Sign in"}
          </button>

          {cognitoEnabled ? (
            <button
              type="button"
              onClick={() => loginWithCognito()}
              className="w-full rounded-lg border border-zinc-300 bg-white px-4 py-2.5 text-sm font-semibold text-zinc-800 hover:bg-zinc-50"
            >
              Sign in with Amazon Cognito
            </button>
          ) : null}

          <p className="text-center text-sm text-zinc-600">
            New traveler?{" "}
            <Link className="font-semibold text-teal-700 hover:text-teal-800" to="/register">
              Create an account
            </Link>
          </p>
        </form>
      </div>
    </div>
  );
}
