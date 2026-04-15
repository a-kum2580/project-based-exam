"use client";

import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from "react";
import { authAPI, setTokens, loadTokens, clearTokens } from "@/lib/api";
import type { User } from "@/types/movie";

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

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const refreshUser = useCallback(async () => {
    try {
      loadTokens();
      const profile = await authAPI.getProfile();
      setUser(normalizeUserProfile(profile));
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
