import { createContext, useContext, useEffect, useState, useCallback } from "react";
import { api, getToken, setToken } from "../api/client";

const PERMISSIONS = {
  view_dashboard: ["Super Admin", "Administrator", "Office Staff", "Store Keeper", "Printing Staff", "Department Staff"],
  manage_inventory: ["Super Admin", "Administrator", "Store Keeper"],
  view_inventory: ["Super Admin", "Administrator", "Office Staff", "Store Keeper", "Printing Staff", "Department Staff"],
  issue_items: ["Super Admin", "Administrator", "Store Keeper", "Office Staff"],
  return_items: ["Super Admin", "Administrator", "Store Keeper", "Office Staff"],
  manage_printing: ["Super Admin", "Administrator", "Printing Staff"],
  manage_teachers: ["Super Admin", "Administrator", "Office Staff"],
  manage_documents: ["Super Admin", "Administrator", "Office Staff", "Department Staff"],
  manage_suppliers: ["Super Admin", "Administrator", "Store Keeper"],
  manage_purchases: ["Super Admin", "Administrator", "Store Keeper"],
  view_reports: ["Super Admin", "Administrator", "Office Staff", "Store Keeper"],
  manage_users: ["Super Admin", "Administrator"],
  manage_settings: ["Super Admin", "Administrator"],
};

export function hasPermission(role, key) {
  return (PERMISSIONS[key] || []).includes(role);
}

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!getToken()) {
      setLoading(false);
      return;
    }
    api
      .get("/auth/me")
      .then(setUser)
      .catch(() => setToken(null))
      .finally(() => setLoading(false));
  }, []);

  const login = useCallback(async (username, password) => {
    const data = await api.post("/auth/login", { username, password });
    setToken(data.token);
    setUser(data.user);
    return data.user;
  }, []);

  const logout = useCallback(() => {
    setToken(null);
    setUser(null);
  }, []);

  const refreshMe = useCallback(async () => {
    const me = await api.get("/auth/me");
    setUser(me);
    return me;
  }, []);

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, refreshMe }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
