import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  type ReactNode,
} from "react";
import { useNavigate } from "react-router-dom";
import * as api from "@/lib/api";
import type { Organization, User, LoginRequest, RegisterRequest } from "@/types";

interface AuthContextType {
  user: User | null;
  organization: Organization | null;
  isLoading: boolean;
  login: (data: LoginRequest) => Promise<void>;
  register: (data: RegisterRequest) => Promise<void>;
  logout: () => Promise<void>;
  refreshAuth: () => Promise<boolean>;
  updateOrganization: (org: Organization) => void;
}

const AuthContext = createContext<AuthContextType | null>(null);

function storeAuth(response: api.AuthResponse) {
  localStorage.setItem("access_token", response.access_token);
  localStorage.setItem("refresh_token", response.refresh_token);
  localStorage.setItem("user", JSON.stringify(response.user));
  localStorage.setItem("organization", JSON.stringify(response.organization));
}

function clearAuth() {
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
  localStorage.removeItem("user");
  localStorage.removeItem("organization");
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [organization, setOrganization] = useState<Organization | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    const storedUser = localStorage.getItem("user");
    const storedOrg = localStorage.getItem("organization");
    const token = localStorage.getItem("access_token");
    if (storedUser && storedOrg && token) {
      try {
        setUser(JSON.parse(storedUser));
        setOrganization(JSON.parse(storedOrg));
      } catch {
        clearAuth();
      }
    }
    setIsLoading(false);
  }, []);

  const refreshAuth = useCallback(async (): Promise<boolean> => {
    const refreshToken = localStorage.getItem("refresh_token");
    if (!refreshToken) return false;
    try {
      const response = await api.refresh(refreshToken);
      localStorage.setItem("access_token", response.access_token);
      localStorage.setItem("refresh_token", response.refresh_token);
      return true;
    } catch {
      clearAuth();
      setUser(null);
      setOrganization(null);
      return false;
    }
  }, []);

  const login = useCallback(
    async (data: LoginRequest) => {
      const response = await api.login(data);
      storeAuth(response);
      setUser(response.user);
      setOrganization(response.organization);
      navigate("/app/dashboard");
    },
    [navigate]
  );

  const register = useCallback(
    async (data: RegisterRequest) => {
      const response = await api.register(data);
      storeAuth(response);
      setUser(response.user);
      setOrganization(response.organization);
      navigate("/app/dashboard");
    },
    [navigate]
  );

  const logout = useCallback(async () => {
    try {
      await api.authLogout();
    } catch {
      // ignore logout errors
    }
    clearAuth();
    setUser(null);
    setOrganization(null);
    navigate("/login");
  }, [navigate]);

  const updateOrganization = useCallback(
    (org: Organization) => {
      setOrganization(org);
      localStorage.setItem("organization", JSON.stringify(org));
    },
    []
  );

  return (
    <AuthContext.Provider
      value={{ user, organization, isLoading, login, register, logout, refreshAuth, updateOrganization }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
