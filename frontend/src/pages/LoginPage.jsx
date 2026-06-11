import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { formatAxiosError } from "../utils/errors";

export default function LoginPage() {
  const navigate = useNavigate();
  const { login, register } = useAuth();
  const [mode, setMode] = useState("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError("");
    setSubmitting(true);

    try {
      if (mode === "login") {
        await login(email, password);
      } else {
        await register(email, password);
      }
      navigate("/candidates");
    } catch (err) {
      setError(formatAxiosError(err, "Authentication failed"));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="auth-page">
      <form className="card auth-card" onSubmit={handleSubmit}>
        <h1>Candidate Review Dashboard</h1>
        <p className="muted">Sign in to score candidates and review AI summaries.</p>

        <label>
          Email
          <input
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            required
          />
        </label>

        <label>
          Password
          <input
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            minLength={8}
            required
          />
        </label>

        {error && <p className="error-text">{error}</p>}

        <button type="submit" className="btn btn-primary" disabled={submitting}>
          {submitting ? "Please wait..." : mode === "login" ? "Sign in" : "Create account"}
        </button>

        <button
          type="button"
          className="link-button"
          onClick={() => setMode(mode === "login" ? "register" : "login")}
        >
          {mode === "login"
            ? "Need an account? Register as reviewer"
            : "Already have an account? Sign in"}
        </button>

        <div className="demo-credentials">
          <p className="muted">Demo accounts:</p>
          <p>Admin: admin@tech.com / adminpass123</p>
          <p>Reviewer: reviewer1@tech.com / reviewerpass123</p>
        </div>
      </form>
    </div>
  );
}
