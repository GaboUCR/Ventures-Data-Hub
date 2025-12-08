// src/context/AuthContext.tsx
"use client";

import React, {
  createContext,
  useContext,
  useEffect,
  useState,
  ReactNode,
} from "react";
import type { AuthResponse, LoginPayload, SignupPayload } from "@/lib/auth-client";
import { login as apiLogin, signup as apiSignup } from "@/lib/auth-client";

const STORAGE_KEY = "ace_auth_v1";

type AuthState = {
  token: string | null;
  user: {
    id: string;
    fullName: string | null;
    companyId: string | null;
    globalRole: string;
  } | null;
};

type AuthContextValue = {
  token: string | null;
  user: AuthState["user"];
  isLoading: boolean;
  signup: (payload: SignupPayload) => Promise<void>;
  login: (payload: LoginPayload) => Promise<void>;
  logout: () => void;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthState>({
    token: null,
    user: null,
  });
  const [isLoading, setIsLoading] = useState(true);

  // Load from localStorage on mount
  useEffect(() => {
    if (typeof window === "undefined") return;

    try {
      const raw = window.localStorage.getItem(STORAGE_KEY);
      if (raw) {
        const parsed = JSON.parse(raw) as {
          token: string;
          user: AuthState["user"];
        };
        setState(parsed);
      }
    } catch {
      // ignore
    } finally {
      setIsLoading(false);
    }
  }, []);

  function persist(next: AuthState) {
    setState(next);
    if (typeof window !== "undefined") {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
    }
  }

  async function handleSignup(payload: SignupPayload) {
    const res: AuthResponse = await apiSignup(payload);
    const next: AuthState = {
      token: res.access_token,
      user: {
        id: res.user_id,
        fullName: res.full_name ?? null,
        companyId: res.company_id ?? null,
        globalRole: res.global_role,
      },
    };
    persist(next);
  }

  async function handleLogin(payload: LoginPayload) {
    const res: AuthResponse = await apiLogin(payload);
    const next: AuthState = {
      token: res.access_token,
      user: {
        id: res.user_id,
        fullName: res.full_name ?? null,
        companyId: res.company_id ?? null,
        globalRole: res.global_role,
      },
    };
    persist(next);
  }

  function logout() {
    const next: AuthState = { token: null, user: null };
    setState(next);
    if (typeof window !== "undefined") {
      window.localStorage.removeItem(STORAGE_KEY);
    }
  }

  return (
    <AuthContext.Provider
      value={{
        token: state.token,
        user: state.user,
        isLoading,
        signup: handleSignup,
        login: handleLogin,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return ctx;
}
