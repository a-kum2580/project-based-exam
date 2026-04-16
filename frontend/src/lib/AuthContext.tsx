"use client";

import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from "react";
import { authAPI, setTokens, loadTokens, clearTokens } from "@/lib/api";
import type { User } from "@/types/movie";

const LOCAL_ACTIVITY_LOG_KEY = "cq_activity_log_days";

interface AuthContextType {
  user: User | null;
  loading: boolean;
  isAuthenticated: boolean;
  login: (username: string, password: string) => Promise<void>;
  register: (username: string, email: string, password: string) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  loading: true,
  isAuthenticated: false,
  login: async () => {},
  register: async () => {},
  logout: () => {},
  refreshUser: async () => {},
});

export function useAuth() {
  return useContext(AuthContext);
}

function toTitleCaseUsername(value: string) {
  return value
    .split(/([_\-\s]+)/)
    .map((part) => {
      if (/^[_\-\s]+$/.test(part) || !part) return part;
      return part.charAt(0).toUpperCase() + part.slice(1).toLowerCase();
    })
    .join("");
}

function normalizeUserProfile(user: User): User {
  return {
    ...user,
    username: toTitleCaseUsername(user.username || ""),
  };
}

function formatLocalDate(date: Date): string {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, "0");
  const d = String(date.getDate()).padStart(2, "0");
  return `${y}-${m}-${d}`;
}

function logLocalActivityDay(): void {
  if (typeof window === "undefined") return;

  const today = formatLocalDate(new Date());

  try {
    const raw = localStorage.getItem(LOCAL_ACTIVITY_LOG_KEY);
    const parsed = raw ? JSON.parse(raw) : [];
    const days = Array.isArray(parsed) ? parsed.filter((v) => typeof v === "string") : [];

    if (days.includes(today)) return;

    days.push(today);
    days.sort();
    localStorage.setItem(LOCAL_ACTIVITY_LOG_KEY, JSON.stringify(days));
  } catch {
    localStorage.setItem(LOCAL_ACTIVITY_LOG_KEY, JSON.stringify([today]));
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const refreshUser = useCallback(async () => {
    try {
      loadTokens();
      const profile = await authAPI.getProfile();
      setUser(normalizeUserProfile(profile));
      logLocalActivityDay();
    } catch {
      setUser(null);
    }
  }, []);

  useEffect(() => {
    loadTokens();
    refreshUser().finally(() => setLoading(false));
  }, [refreshUser]);

  const login = useCallback(async (username: string, password: string) => {
    await authAPI.login(username, password);
    await refreshUser();
  }, [refreshUser]);

  const register = useCallback(async (username: string, email: string, password: string) => {
    await authAPI.register(username, email, password);
    await authAPI.login(username, password);
    await refreshUser();
  }, [refreshUser]);

  const logout = useCallback(() => {
    clearTokens();
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        isAuthenticated: !!user,
        login,
        register,
        logout,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}
