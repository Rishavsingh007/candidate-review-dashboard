import { createContext, useCallback, useContext, useMemo, useState } from "react";
import { fetchCurrentUser, login as loginRequest, register as registerRequest } from "../api/auth";
import { TOKEN_KEY } from "../utils/constants";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem(TOKEN_KEY));
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(Boolean(localStorage.getItem(TOKEN_KEY)));

  const loadUser = useCallback(async (accessToken) => {
    localStorage.setItem(TOKEN_KEY, accessToken);
    setToken(accessToken);
    const profile = await fetchCurrentUser();
    setUser(profile);
    return profile;
  }, []);

  const login = useCallback(
    async (email, password) => {
      const { access_token } = await loginRequest(email, password);
      return loadUser(access_token);
    },
    [loadUser],
  );

  const register = useCallback(async (email, password) => {
    await registerRequest(email, password);
    return login(email, password);
  }, [login]);

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY);
    setToken(null);
    setUser(null);
  }, []);

  const initialize = useCallback(async () => {
    if (!token) {
      setLoading(false);
      return;
    }
    try {
      await loadUser(token);
    } catch {
      logout();
    } finally {
      setLoading(false);
    }
  }, [token, loadUser, logout]);

  const value = useMemo(
    () => ({
      token,
      user,
      loading,
      isAuthenticated: Boolean(token && user),
      isAdmin: user?.role === "admin",
      login,
      register,
      logout,
      initialize,
      setUser,
    }),
    [token, user, loading, login, register, logout, initialize],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuthContext() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuthContext must be used within AuthProvider");
  }
  return context;
}
