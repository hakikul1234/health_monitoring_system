import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { Activity, LockKeyhole, Orbit, User } from "lucide-react";

import useAuthStore from "../../stores/authStore";

function LoginPage() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  const navigate = useNavigate();
  const location = useLocation();

  const login = useAuthStore((state) => state.login);
  const isLoading = useAuthStore((state) => state.isLoading);
  const error = useAuthStore((state) => state.error);
  const clearError = useAuthStore((state) => state.clearError);

  const handleSubmit = async (event) => {
    event.preventDefault();

    try {
      await login({ username, password });

      const destination = location.state?.from?.pathname || "/";

      navigate(destination, { replace: true });
    } catch {
      // The authentication store maintains the API error message.
    }
  };

  return (
    <main className="auth-page">
      <section className="auth-card">
        <div className="auth-brand-icon">
          <Orbit size={32} />
        </div>

        <div className="auth-brand-name">
          ASTRA<span>-PULSE</span>
        </div>

        <div className="auth-heading">
          <div className="auth-eyebrow">
            <Activity size={14} />
            MISSION CONTROL ACCESS
          </div>

          <h1>Welcome back</h1>

          <p>Sign in to access the astronaut health intelligence platform.</p>
        </div>

        {error && (
          <div className="auth-error" role="alert">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="auth-form">
          <label htmlFor="login-username">Username</label>

          <div className="auth-input-wrapper">
            <User size={17} />

            <input
              id="login-username"
              type="text"
              placeholder="Enter your username"
              value={username}
              onChange={(event) => {
                setUsername(event.target.value);
                clearError();
              }}
              autoComplete="username"
              required
            />
          </div>

          <label htmlFor="login-password">Password</label>

          <div className="auth-input-wrapper">
            <LockKeyhole size={17} />

            <input
              id="login-password"
              type="password"
              placeholder="Enter your password"
              value={password}
              onChange={(event) => {
                setPassword(event.target.value);
                clearError();
              }}
              autoComplete="current-password"
              required
            />
          </div>

          <button
            className="auth-submit-button"
            type="submit"
            disabled={isLoading}
          >
            {isLoading ? "Authenticating..." : "Sign in to ASTRA-PULSE"}
          </button>
        </form>

        <div className="auth-switch">
          New astronaut account? <Link to="/register">Create account</Link>
        </div>

        <div className="auth-disclaimer">
          Software research prototype · Synthetic demonstration environment
        </div>
      </section>
    </main>
  );
}

export default LoginPage;
