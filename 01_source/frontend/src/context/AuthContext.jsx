// 01_source/frontend/src/context/AuthContext.jsx
import React, { createContext, useContext, useEffect, useMemo, useState } from "react";
import { fetchPublicMe, loginPublicUser, registerPublicUser } from "../services/authApi";

const AuthContext = createContext(null);
const STORAGE_KEY = "ellan_public_auth_token";

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem(STORAGE_KEY) || null);
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(() => Boolean(localStorage.getItem(STORAGE_KEY)));

  useEffect(() => {
    let active = true;

    async function bootstrap() {
      if (!token) {
        if (!active) return;
        setUser(null);
        setLoading(false);
        return;
      }

      if (active) {
        setLoading(true);
      }

      try {
        const data = await fetchPublicMe(token);

        if (!active) return;

        setUser(data?.user || null);
      } catch (error) {
        if (!active) return;

        console.error("Sessão inválida:", error);
        localStorage.removeItem(STORAGE_KEY);
        setToken(null);
        setUser(null);
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    bootstrap();

    return () => {
      active = false;
    };
  }, [token]);

  async function login(payload) {
    setLoading(true);

    try {
      const data = await loginPublicUser(payload);
      const nextToken = data?.access_token || null;
      const nextUser = data?.user || null;

      if (!nextToken) {
        throw new Error("Token de autenticação não retornado no login.");
      }

      localStorage.setItem(STORAGE_KEY, nextToken);
      setToken(nextToken);
      setUser(nextUser);

      return data;
    } catch (error) {
      localStorage.removeItem(STORAGE_KEY);
      setToken(null);
      setUser(null);
      throw error;
    } finally {
      setLoading(false);
    }
  }

  async function register(payload) {
    setLoading(true);

    try {
      const data = await registerPublicUser(payload);
      const nextToken = data?.access_token || null;
      const nextUser = data?.user || null;

      if (!nextToken) {
        throw new Error("Token de autenticação não retornado no cadastro.");
      }

      localStorage.setItem(STORAGE_KEY, nextToken);
      setToken(nextToken);
      setUser(nextUser);

      return data;
    } catch (error) {
      localStorage.removeItem(STORAGE_KEY);
      setToken(null);
      setUser(null);
      throw error;
    } finally {
      setLoading(false);
    }
  }

  function logout() {
    localStorage.removeItem(STORAGE_KEY);
    setToken(null);
    setUser(null);
    setLoading(false);
  }

  const isAuthenticated = Boolean(token && user);

  const value = useMemo(
    () => ({
      token,
      user,
      loading,
      isAuthenticated,
      login,
      register,
      logout,
    }),
    [token, user, loading, isAuthenticated]
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