import { Link } from "react-router-dom";
import { ShieldAlert } from "lucide-react";

function UnauthorizedPage() {
  return (
    <main className="auth-page">
      <section className="auth-card">
        <div className="auth-brand-icon">
          <ShieldAlert size={32} />
        </div>

        <div className="auth-brand-name">
          ASTRA<span>-PULSE</span>
        </div>

        <div className="auth-heading">
          <h1>Access restricted</h1>

          <p>
            Your current account role does not have permission
            to access this section.
          </p>
        </div>

        <Link
          to="/"
          className="auth-submit-button"
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            textDecoration: "none",
          }}
        >
          Return to dashboard
        </Link>

        <div className="auth-disclaimer">
          Access is controlled by account permissions.
        </div>
      </section>
    </main>
  );
}

export default UnauthorizedPage;
