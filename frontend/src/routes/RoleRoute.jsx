import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";

export default function RoleRoute({ allowedRole = "admin" }) {
  const { user, loading } = useAuth();

  if (loading) {
    return <div className="page-message">Loading session...</div>;
  }

  if (user?.role !== allowedRole) {
    return <Navigate to="/candidates" replace />;
  }

  return <Outlet />;
}
