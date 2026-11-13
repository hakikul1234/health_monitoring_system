import { Orbit } from "lucide-react";

function LoadingScreen() {
  return (
    <div className="auth-loading-screen">
      <div className="auth-loading-content">
        <div className="auth-loading-logo">
          <Orbit size={38} />
        </div>

        <h1>ASTRA<span>-PULSE</span></h1>

        <div className="auth-loading-spinner" />

        <p>Verifying mission session...</p>

        <small>SPACE HEALTH INTELLIGENCE PLATFORM</small>
      </div>
    </div>
  );
}

export default LoadingScreen;
