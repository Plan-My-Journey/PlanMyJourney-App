import { createContext, ReactNode, useContext, useMemo, useState } from "react";

import { api, TOKEN_STORAGE_KEY, USER_STORAGE_KEY } from "../api/client";
import { buildAuthorizeUrl, buildLogoutUrl, exchangeCodeForTokens, isCognitoEnabled } from "../auth/cognito";
import { AuthResponse, User } from "../types";

interface AuthContextValue {
  token: string | null;
  user: User | null;
  login: (email: string, password: string) => Promise<void>;
  loginWithCognito: () => void;
  completeCognitoCallback: (code: string) => Promise<void>;
  register: (name: string, email: string, password: string) => Promise<void>;
  logout: () => void;
  setUser: (user: User) => void;
  cognitoEnabled: boolean;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

function readStoredUser(): User | null {
  const stored = localStorage.getItem(USER_STORAGE_KEY);
  if (!stored) {
    return null;
  }
  try {
    return JSON.parse(stored) as User;
  } catch {
    localStorage.removeItem(USER_STORAGE_KEY);
    return null;
  }
}

export function AuthProvider({ children }: { readonly children: ReactNode }) {
  const [token, setTokenState] = useState<string | null>(() => localStorage.getItem(TOKEN_STORAGE_KEY));
  const [user, setUserState] = useState<User | null>(() => readStoredUser());

  const isValidJwt = (token: string): boolean => /^[A-Za-z0-9\-_.]+$/.test(token);

  const persistAuth = (payload: AuthResponse) => {
    if (isValidJwt(payload.access_token)) {
      localStorage.setItem(TOKEN_STORAGE_KEY, payload.access_token);
    }
    const safeUser = {
      id: String(payload.user.id),
      name: String(payload.user.name),
      email: String(payload.user.email),
      created_at: String(payload.user.created_at),
    };
    localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(safeUser));
    setTokenState(payload.access_token);
    setUserState(payload.user);
  };

  const value = useMemo<AuthContextValue>(
    () => ({
      token,
      user,
      login: async (email: string, password: string) => {
        const { data } = await api.post<AuthResponse>("/auth/login", { email, password });
        persistAuth(data);
      },
      loginWithCognito: () => {
        globalThis.location.href = buildAuthorizeUrl(crypto.randomUUID());
      },
      completeCognitoCallback: async (code: string) => {
        const tokens = await exchangeCodeForTokens(code);
        const payload = JSON.parse(atob(tokens.id_token.split(".")[1])) as Record<string, string>;
        const user: User = {
          id: payload.sub,
          name: payload.name || payload.email || "Traveler",
          email: payload.email || "",
          created_at: new Date().toISOString(),
        };
        if (isValidJwt(tokens.access_token)) {
          localStorage.setItem(TOKEN_STORAGE_KEY, tokens.access_token);
        }
        const safeUser = { id: String(user.id), name: String(user.name), email: String(user.email), created_at: String(user.created_at) };
        localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(safeUser));
        setTokenState(tokens.access_token);
        setUserState(user);
      },
      register: async (name: string, email: string, password: string) => {
        const { data } = await api.post<AuthResponse>("/auth/register", { name, email, password });
        persistAuth(data);
      },
      logout: () => {
        localStorage.removeItem(TOKEN_STORAGE_KEY);
        localStorage.removeItem(USER_STORAGE_KEY);
        setTokenState(null);
        setUserState(null);
        if (isCognitoEnabled()) {
          globalThis.location.href = buildLogoutUrl();
        }
      },
      setUser: (nextUser: User) => {
        localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(nextUser));
        setUserState(nextUser);
      },
      cognitoEnabled: isCognitoEnabled()
    }),
    [token, user]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used inside AuthProvider");
  }
  return context;
}
