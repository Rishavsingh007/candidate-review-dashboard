import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { setUnauthorizedHandler } from "./api/client";
import { useAuth } from "./hooks/useAuth";
import AppRoutes from "./routes/AppRoutes";

export default function App() {
  const navigate = useNavigate();
  const { user, logout, initialize } = useAuth();

  useEffect(() => {
    initialize();
  }, [initialize]);

  useEffect(() => {
    setUnauthorizedHandler(() => {
      logout();
      navigate("/login", { replace: true });
    });
  }, [logout, navigate]);

  return (
    <div className="app-shell">
      {user && (
        <header className="app-header">
          <div className="app-header__brand">Candidate Review Dashboard</div>
          <div className="app-header__meta">
            <span>
              {user.email} ({user.role})
            </span>
            <button type="button" className="btn btn-secondary" onClick={logout}>
              Sign out
            </button>
          </div>
        </header>
      )}
      <main className="app-main">
        <AppRoutes />
      </main>
    </div>
  );
}
