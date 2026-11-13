import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Orbit, UserPlus } from "lucide-react";

import useAuthStore from "../../stores/authStore";

function RegisterPage() {
  const [formData, setFormData] = useState({
    full_name: "",
    username: "",
    email: "",
    password: "",
  });

  const [successMessage, setSuccessMessage] = useState("");

  const navigate = useNavigate();

  const register = useAuthStore((state) => state.register);
  const isLoading = useAuthStore((state) => state.isLoading);
  const error = useAuthStore((state) => state.error);
  const clearError = useAuthStore((state) => state.clearError);

  const handleChange = (event) => {
    const { name, value } = event.target;

    setFormData((previous) => ({
      ...previous,
      [name]: value,
    }));

    clearError();
    setSuccessMessage("");
  };

  const handleSubmit = async (event) => {
    event.preventDefault();

    try {
      await register(formData);

      setSuccessMessage(
        "Account created successfully. You can now sign in."
      );

      setTimeout(() => {
        navigate("/login", { replace: true });
      }, 1200);
    } catch {
      // The authentication store maintains the API error message.
    }
  };

  return (
    <main className="auth-page">
      <section className="auth-card auth-register-card">
        <div className="auth-brand-icon">
          <Orbit size={32} />
        </div>

        <div className="auth-brand-name">
          ASTRA<span>-PULSE</span>
        </div>

        <div className="auth-heading">
          <div className="auth-eyebrow">
            <UserPlus size={14} />
            ASTRONAUT ACCOUNT REGISTRATION
          </div>

          <h1>Create account</h1>

          <p>Register your account to access the research platform.</p>
        </div>

        {error && (
          <div className="auth-error" role="alert">
            {error}
          </div>
        )}

        {successMessage && (
          <div className="auth-success" role="status">
            {successMessage}
          </div>
        )}

        <form onSubmit={handleSubmit} className="auth-form">
          <label htmlFor="register-full-name">Full name</label>

          <input
            id="register-full-name"
            name="full_name"
            type="text"
            placeholder="Enter your full name"
            value={formData.full_name}
            onChange={handleChange}
            autoComplete="name"
            required
          />

          <label htmlFor="register-username">Username</label>

          <input
            id="register-username"
            name="username"
            type="text"
            placeholder="Choose a username"
            value={formData.username}
            onChange={handleChange}
            autoComplete="username"
            required
          />

          <label htmlFor="register-email">Email address</label>

          <input
            id="register-email"
            name="email"
            type="email"
            placeholder="Enter your email"
            value={formData.email}
            onChange={handleChange}
            autoComplete="email"
            required
          />

          <label htmlFor="register-password">Password</label>

          <input
            id="register-password"
            name="password"
            type="password"
            placeholder="Create a password (minimum 8 characters)"
            value={formData.password}
            onChange={handleChange}
            autoComplete="new-password"
            minLength={8}
            required
          />

          <button
            className="auth-submit-button"
            type="submit"
            disabled={isLoading}
          >
            {isLoading ? "Creating account..." : "Create astronaut account"}
          </button>
        </form>

        <div className="auth-role-note">
          New public accounts receive the Astronaut role automatically.
        </div>

        <div className="auth-switch">
          Already registered? <Link to="/login">Sign in</Link>
        </div>

        <div className="auth-disclaimer">
          Software research prototype · Synthetic demonstration environment
        </div>
      </section>
    </main>
  );
}

export default RegisterPage;
