import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
} from "react";
import api from "../api/client";
import type { User } from "../types";

interface AuthContextType {
  user: User | null;
  accessToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (
    email: string,
    username: string,
    password: string,
    adminKey?: string
  ) => Promise<User>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | null>(null);

function getCookie(name: string): string | undefined {
  const match = document.cookie.match(new RegExp(`(^| )${name}=([^;]+)`));
  return match?.[2];
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const accessTokenRef = useRef<string | null>(null);
  const refreshPromise = useRef<Promise<string | null> | null>(null);

  // Keep ref in sync
  accessTokenRef.current = accessToken;

  const refreshTokens = useCallback(async (): Promise<string | null> => {
    if (refreshPromise.current) return refreshPromise.current;

    refreshPromise.current = (async () => {
      try {
        const csrfToken = getCookie("csrf_token");
        const res = await api.post(
          "/api/auth/refresh",
          {},
          {
            headers: {
              "X-CSRF-Protection": "1",
              ...(csrfToken ? { "X-CSRF-Token": csrfToken } : {}),
            },
          }
        );
        setUser(res.data.user);
        setAccessToken(res.data.access_token);
        return res.data.access_token;
      } catch {
        setUser(null);
        setAccessToken(null);
        return null;
      } finally {
        refreshPromise.current = null;
      }
    })();

    return refreshPromise.current;
  }, []);

  // Try to restore session on mount
  useEffect(() => {
    refreshTokens().finally(() => setIsLoading(false));
  }, [refreshTokens]);

  // Axios response interceptor — auto-refresh on 401
  useEffect(() => {
    const interceptor = api.interceptors.response.use(
      (response) => response,
      async (error) => {
        const original = error.config;
        if (error.response?.status === 401 && !original._retry) {
          original._retry = true;
          const newToken = await refreshTokens();
          if (newToken) {
            original.headers.Authorization = `Bearer ${newToken}`;
            return api(original);
          }
        }
        return Promise.reject(error);
      }
    );
    return () => api.interceptors.response.eject(interceptor);
  }, [refreshTokens]);

  // Axios request interceptor — inject Bearer token
  useEffect(() => {
    const interceptor = api.interceptors.request.use((config) => {
      if (accessTokenRef.current) {
        config.headers.Authorization = `Bearer ${accessTokenRef.current}`;
      }
      return config;
    });
    return () => api.interceptors.request.eject(interceptor);
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const res = await api.post("/api/auth/login", { email, password });
    setAccessToken(res.data.access_token);
    setUser(res.data.user);
  }, []);

  const register = useCallback(
    async (email: string, username: string, password: string, adminKey?: string) => {
      const res = await api.post("/api/auth/register", {
        email,
        username,
        password,
        admin_key: adminKey,
      });
      return res.data as User;
    },
    []
  );

  const logout = useCallback(async () => {
    try {
      await api.post("/api/auth/logout");
    } catch {
      // Clear local state regardless
    }
    setUser(null);
    setAccessToken(null);
  }, []);

  return (
    <AuthContext.Provider
      value={{
        user,
        accessToken,
        isAuthenticated: !!user,
        isLoading,
        login,
        register,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
