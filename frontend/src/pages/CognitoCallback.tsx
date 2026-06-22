import { useEffect, useState } from "react";
import { Navigate, useSearchParams } from "react-router-dom";

import { useAuth } from "../context/AuthContext";

export default function CognitoCallback() {
  const { completeCognitoCallback, token } = useAuth();
  const [searchParams] = useSearchParams();
  const [error, setError] = useState("");

  useEffect(() => {
    const code = searchParams.get("code");
    if (!code) {
      setError("Missing authorization code.");
      return;
    }
    completeCognitoCallback(code).catch(() => setError("Cognito sign-in failed."));
  }, [completeCognitoCallback, searchParams]);

  if (token) {
    return <Navigate to="/" replace />;
  }

  if (error) {
    return <div className="flex min-h-screen items-center justify-center">{error}</div>;
  }

  return <div className="flex min-h-screen items-center justify-center">Completing sign-in...</div>;
}
