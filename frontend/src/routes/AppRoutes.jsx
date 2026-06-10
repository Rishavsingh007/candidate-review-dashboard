import { Navigate, Route, Routes } from "react-router-dom";
import CandidateDetailPage from "../pages/CandidateDetailPage";
import CandidateListPage from "../pages/CandidateListPage";
import LoginPage from "../pages/LoginPage";
import { useAuth } from "../hooks/useAuth";
import ProtectedRoute from "./ProtectedRoute";

export default function AppRoutes() {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return <div className="page-message">Loading session...</div>;
  }

  return (
    <Routes>
      <Route
        path="/login"
        element={isAuthenticated ? <Navigate to="/candidates" replace /> : <LoginPage />}
      />
      <Route element={<ProtectedRoute />}>
        <Route path="/" element={<Navigate to="/candidates" replace />} />
        <Route path="/candidates" element={<CandidateListPage />} />
        <Route path="/candidates/:id" element={<CandidateDetailPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/candidates" replace />} />
    </Routes>
  );
}
