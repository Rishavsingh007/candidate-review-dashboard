import { useEffect } from "react";
import { useAuth } from "./hooks/useAuth";
import AppRoutes from "./routes/AppRoutes";

export default function App() {
  const { user, logout, initialize } = useAuth();

  useEffect(() => {
    initialize();
  }, [initialize]);

  return (
    <div className="app-shell">
      {user && (
        <header className="app-header">
          <div className="app-header__brand">TechKraft Review</div>
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
