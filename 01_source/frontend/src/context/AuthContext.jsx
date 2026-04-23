// 01_source/frontend/src/context/AuthContext.jsx
import React, { createContext, useContext, useEffect, useMemo, useState } from "react";
import { fetchPublicMe, fetchPublicRoles, loginPublicUser, registerPublicUser } from "../services/authApi";

const AuthContext = createContext(null);
const STORAGE_KEY = "ellan_public_auth_token";

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem(STORAGE_KEY) || null);
  const [user, setUser] = useState(null);
  const [roles, setRoles] = useState([]);
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
        const rolesData = await fetchPublicRoles(token).catch(() => ({ roles: [] }));

        if (!active) return;

        setUser(data?.user || null);
        setRoles(Array.isArray(rolesData?.roles) ? rolesData.roles : []);
      } catch (error) {
        if (!active) return;

        console.error("Sessão inválida:", error);
        localStorage.removeItem(STORAGE_KEY);
        setToken(null);
        setUser(null);
        setRoles([]);
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
      setRoles([]);

      return data;
    } catch (error) {
      localStorage.removeItem(STORAGE_KEY);
      setToken(null);
      setUser(null);
      setRoles([]);
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
      setRoles([]);

      return data;
    } catch (error) {
      localStorage.removeItem(STORAGE_KEY);
      setToken(null);
      setUser(null);
      setRoles([]);
      throw error;
    } finally {
      setLoading(false);
    }
  }

  async function refreshUser() {
    if (!token) return null;
    const [data, rolesData] = await Promise.all([
      fetchPublicMe(token),
      fetchPublicRoles(token).catch(() => ({ roles: [] })),
    ]);
    const nextUser = data?.user || null;
    setUser(nextUser);
    setRoles(Array.isArray(rolesData?.roles) ? rolesData.roles : []);
    return nextUser;
  }

  function hasRole(roleName) {
    const target = String(roleName || "").trim().toLowerCase();
    if (!target) return false;
    return roles.some((entry) => String(entry?.role || "").trim().toLowerCase() === target);
  }

  function logout() {
    localStorage.removeItem(STORAGE_KEY);
    setToken(null);
    setUser(null);
    setRoles([]);
    setLoading(false);
  }

  const isAuthenticated = Boolean(token && user);

  const value = useMemo(
    () => ({
      token,
      user,
      loading,
      isAuthenticated,
      roles,
      hasRole,
      login,
      register,
      refreshUser,
      logout,
    }),
    [token, user, loading, isAuthenticated, roles]
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