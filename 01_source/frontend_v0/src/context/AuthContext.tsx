
import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { fetchPublicMe, fetchPublicRoles, loginPublicUser, registerPublicUser } from "../services/authApi";

const STORAGE_KEY = "ellan_public_auth_token";

type UnknownRecord = Record<string, unknown>;

interface AuthRole {
  role?: string;
  [key: string]: unknown;
}

interface AuthApiResponse {
  access_token?: string | null;
  user?: UnknownRecord | null;
  roles?: AuthRole[];
}

export interface AuthContextValue {
  token: string | null;
  user: UnknownRecord | null;
  loading: boolean;
  isAuthenticated: boolean;
  roles: AuthRole[];
  hasRole: (roleName: string) => boolean;
  login: (payload: unknown) => Promise<AuthApiResponse>;
  register: (payload: unknown) => Promise<AuthApiResponse>;
  refreshUser: () => Promise<UnknownRecord | null>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

function asRecord(value: unknown): UnknownRecord {
  return value && typeof value === "object" ? (value as UnknownRecord) : {};
}

function asAuthApiResponse(value: unknown): AuthApiResponse {
  const data = asRecord(value);
  return {
    access_token: typeof data.access_token === "string" ? data.access_token : null,
    user: data.user && typeof data.user === "object" ? (data.user as UnknownRecord) : null,
    roles: Array.isArray(data.roles) ? (data.roles as AuthRole[]) : [],
  };
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem(STORAGE_KEY) || null);
  const [user, setUser] = useState<UnknownRecord | null>(null);
  const [roles, setRoles] = useState<AuthRole[]>([]);
  const [loading, setLoading] = useState<boolean>(() => Boolean(localStorage.getItem(STORAGE_KEY)));

  useEffect(() => {
    let active = true;

    async function bootstrap() {
      if (!token) {
        if (!active) return;
        setUser(null);
        setLoading(false);
        return;
      }

      if (active) setLoading(true);

      try {
        const data = asAuthApiResponse(await fetchPublicMe(token));
        const rolesData = asAuthApiResponse(await fetchPublicRoles(token).catch(() => ({ roles: [] })));

        if (!active) return;
        setUser(data.user || null);
        setRoles(Array.isArray(rolesData.roles) ? rolesData.roles : []);
      } catch (error) {
        if (!active) return;
        console.error("Sessão inválida:", error);
        localStorage.removeItem(STORAGE_KEY);
        setToken(null);
        setUser(null);
        setRoles([]);
      } finally {
        if (active) setLoading(false);
      }
    }

    void bootstrap();
    return () => {
      active = false;
    };
  }, [token]);

  async function login(payload: unknown): Promise<AuthApiResponse> {
    setLoading(true);
    try {
      const data = asAuthApiResponse(await loginPublicUser(payload));
      const nextToken = data.access_token || null;
      const nextUser = data.user || null;
      if (!nextToken) throw new Error("Token de autenticação não retornado no login.");

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

  async function register(payload: unknown): Promise<AuthApiResponse> {
    setLoading(true);
    try {
      const data = asAuthApiResponse(await registerPublicUser(payload));
      const nextToken = data.access_token || null;
      const nextUser = data.user || null;
      if (!nextToken) throw new Error("Token de autenticação não retornado no cadastro.");

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

  async function refreshUser(): Promise<UnknownRecord | null> {
    if (!token) return null;
    const [meResult, rolesResult] = await Promise.all([
      fetchPublicMe(token),
      fetchPublicRoles(token).catch(() => ({ roles: [] })),
    ]);
    const data = asAuthApiResponse(meResult);
    const rolesData = asAuthApiResponse(rolesResult);
    setUser(data.user || null);
    setRoles(Array.isArray(rolesData.roles) ? rolesData.roles : []);
    return data.user || null;
  }

  function hasRole(roleName: string): boolean {
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
  const value = useMemo<AuthContextValue>(
    () => ({ token, user, loading, isAuthenticated, roles, hasRole, login, register, refreshUser, logout }),
    [token, user, loading, isAuthenticated, roles]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth deve ser usado dentro de AuthProvider");
  return context;
}


