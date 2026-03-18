import React, { createContext, useContext, useEffect, useMemo, useState } from "react";
import { fetchPublicMe, loginPublicUser, registerPublicUser } from "../services/authApi";

const AuthContext = createContext(null);
const STORAGE_KEY = "ellan_public_auth_token";

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem(STORAGE_KEY));
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(Boolean(localStorage.getItem(STORAGE_KEY)));

  useEffect(() => {
    async function bootstrap() {
      if (!token) {
        setUser(null);
        setLoading(false);
        return;
      }

      try {
        const data = await fetchPublicMe(token);
        setUser(data.user || null);
      } catch (error) {
        console.error("Falha ao carregar sessão pública:", error);
        localStorage.removeItem(STORAGE_KEY);
        setToken(null);
        setUser(null);
      } finally {
        setLoading(false);
      }
    }

    bootstrap();
  }, [token]);

  async function login(payload) {
    const data = await loginPublicUser(payload);
    localStorage.setItem(STORAGE_KEY, data.access_token);
    setToken(data.access_token);
    setUser(data.user);
    return data;
  }

  async function register(payload) {
    const data = await registerPublicUser(payload);
    localStorage.setItem(STORAGE_KEY, data.access_token);
    setToken(data.access_token);
    setUser(data.user);
    return data;
  }

  function logout() {
    localStorage.removeItem(STORAGE_KEY);
    setToken(null);
    setUser(null);
  }

  const value = useMemo(
    () => ({
      token,
      user,
      loading,
      isAuthenticated: Boolean(token && user),
      login,
      register,
      logout,
    }),
    [token, user, loading]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth deve ser usado dentro de AuthProvider");
  }
  return context;
}