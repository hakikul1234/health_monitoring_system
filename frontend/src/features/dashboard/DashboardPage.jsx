import { lazy, Suspense, useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";

import {
  AlertTriangle,
  Bell,
  ChevronDown,
  ChevronRight,
  Command,
  HeartPulse,
  Menu,
  Orbit,
  Signal,
  Sparkles,
  Users,
  X,
  LogOut,
  RefreshCw,
} from "lucide-react";

import "../../App.css";

import Sidebar from "../../components/layout/Sidebar";
import MetricCard from "./components/MetricCard";
const TelemetryChart = lazy(() => import("./components/TelemetryChart"));
import AlertPanel from "./components/AlertPanel";
import MissionPanel from "./components/CrewPanel";
import EnvironmentPanel from "./components/EnvironmentPanel";

import useAuthStore from "../../stores/authStore";
import useDashboardStore from "./dashboardStore";
const CrewHealthPage = lazy(() => import("../crew/CrewHealthPage"));
const MissionsPage = lazy(() => import("../missions/MissionsPage"));
const HealthAlertsPage = lazy(() => import("../alerts/HealthAlertsPage"));
const SimulatorPage = lazy(() => import("../simulator/SimulatorPage"));
const AIIntelligencePage = lazy(() => import("./AIIntelligencePage"));

function formatRole(role) {
  const roles = {
    ASTRONAUT: "Astronaut",
    MEDICAL_OFFICER: "Medical Officer",
    MISSION_CONTROL: "Mission Control",
    SYSTEM_ADMIN: "System Administrator",
  };

  return roles[role] || "Platform User";
}

function getInitials(name) {
  if (!name) return "AP";

  return name
    .trim()
    .split(/\s+/)
    .slice(0, 2)
    .map((part) => part[0])
    .join("")
    .toUpperCase();
}

function formatCount(value) {
  return String(value ?? 0).padStart(2, "0");
}

function formatTime(value) {
  if (!value) return "--:--";

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) return "--:--";

  return date.toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  });
}

function LazyPageFallback() {
  return (
    <div className="page-container dashboard-page">
      <div className="dashboard-state dashboard-loading">
        <RefreshCw size={22} />
        <strong>Loading workspace module...</strong>
        <span>Please wait while this section loads.</span>
      </div>
    </div>
  );
}
function DashboardPage() {
  const [activePage, setActivePage] = useState("Overview");
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [showNotice, setShowNotice] = useState(true);
  const [showProfileMenu, setShowProfileMenu] = useState(false);

  const navigate = useNavigate();

  const user = useAuthStore((state) => state.user);
  const logout = useAuthStore((state) => state.logout);

  const analytics = useDashboardStore((state) => state.analytics);
  const isLoading = useDashboardStore((state) => state.isLoading);
  const error = useDashboardStore((state) => state.error);
  const fetchAnalytics = useDashboardStore((state) => state.fetchAnalytics);
  const clearAnalytics = useDashboardStore((state) => state.clearAnalytics);

  useEffect(() => {
    fetchAnalytics().catch(() => {});
  }, [fetchAnalytics]);

  const crew = analytics?.crew || {};
  const missions = analytics?.missions || {};
  const health = analytics?.health || {};
  const alerts = analytics?.alerts || {};

  const readings = useMemo(() => {
    return (analytics?.latest_readings || [])
      .filter((reading) =>
        reading.is_synthetic === true &&
        reading.data_quality === "VALID"
      )
      .slice()
      .sort(
        (a, b) =>
          new Date(a.recorded_at).getTime() -
          new Date(b.recorded_at).getTime()
      )
      .map((reading) => ({
        time: formatTime(reading.recorded_at),
        heartRate: reading.heart_rate_bpm,
        oxygen: reading.spo2_percent,
      }));
  }, [analytics]);

  const criticalAlerts = analytics?.latest_critical_alerts || [];
  const missionSummary = analytics?.mission_summary || [];

  const handleLogout = () => {
    logout();
    clearAnalytics();
    navigate("/login", { replace: true });
  };

  const displayName = user?.full_name || user?.username || "Platform User";
  const displayRole = formatRole(user?.role);

  return (
    <div className="app-container">
      <Sidebar
        active={activePage}
        onNavigate={setActivePage}
        open={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        openAlerts={alerts.open || 0}
      />

      <main className="main-content">
        <header className="topbar">
          <div className="topbar-left">
            <button
              className="mobile-menu"
              onClick={() => setSidebarOpen(true)}
              aria-label="Open navigation"
            >
              <Menu size={21} />
            </button>

            <div className="breadcrumb">
              <span>Mission Control</span>
              <ChevronRight size={14} />
              <strong>{activePage}</strong>
            </div>
          </div>

          <div className="topbar-actions">
            <div className="connection-status">
              <span className="live-dot" />
              {analytics ? "API CONNECTED" : "CONNECTING"}
            </div>

            <button className="icon-button" aria-label="Notifications">
              <Bell size={18} />
              {alerts.open > 0 && <i />}
            </button>

            <div className="profile-menu-wrap">
              <button
                className="profile-menu"
                type="button"
                aria-label="Open account menu"
                aria-expanded={showProfileMenu}
                onClick={() => setShowProfileMenu((value) => !value)}
              >
                <div className="profile-avatar">
                  {getInitials(displayName)}
                </div>

                <div className="profile-details">
                  <strong>{displayName}</strong>
                  <span>{displayRole}</span>
                </div>

                <ChevronDown size={15} />
              </button>

              {showProfileMenu && (
                <div className="profile-dropdown">
                  <div className="profile-dropdown-user">
                    <strong>{displayName}</strong>
                    <span>{user?.email || user?.username || ""}</span>
                    <small>{displayRole}</small>
                  </div>

                  <button
                    className="profile-logout"
                    type="button"
                    onClick={handleLogout}
                  >
                    <LogOut size={16} />
                    Sign out
                  </button>
                </div>
              )}
            </div>
          </div>
        </header>

        {activePage === "Crew Health" ? (
          <Suspense fallback={<LazyPageFallback />}>
            <CrewHealthPage />
          </Suspense>
        ) : activePage === "Overview" ? (
          <div className="page-container dashboard-page">
          <section className="welcome-section">
            <div>
              <div className="eyebrow">
                <span className="eyebrow-line" />
                SPACE HEALTH INTELLIGENCE PLATFORM
              </div>

              <h1>
                Mission <span className="gradient-text">Overview</span>
              </h1>

              <p>
                Monitor simulated crew health, mission telemetry and
                explainable AI alerts from one workspace.
              </p>
            </div>

            <div className="mission-badge">
              <div className="mission-badge-icon">
                <Orbit size={20} />
              </div>

              <div>
                <span>ACTIVE MISSIONS</span>
                <strong>{formatCount(missions.active)}</strong>
              </div>

              <span className="mission-live-dot" />
            </div>
          </section>

          {showNotice && (
            <div className="demo-notice">
              <div className="notice-icon">
                <Sparkles size={17} />
              </div>

              <div>
                <strong>
                  Research prototype Â· Synthetic demonstration
                </strong>

                <p>
                  All health readings and alerts are synthetic.
                  Not for clinical or operational decisions.
                  Human review is required.
                </p>
              </div>

              <button
                onClick={() => setShowNotice(false)}
                aria-label="Dismiss notice"
              >
                <X size={17} />
              </button>
            </div>
          )}

          {error && (
            <div className="dashboard-state dashboard-state-error">
              <AlertTriangle size={21} />
              <strong>Dashboard data could not be loaded</strong>
              <span>{String(error)}</span>

              <button
                className="dashboard-retry"
                type="button"
                onClick={() => fetchAnalytics().catch(() => {})}
                disabled={isLoading}
              >
                <RefreshCw size={15} />
                Retry
              </button>
            </div>
          )}

          {isLoading && !analytics && (
            <div className="dashboard-state dashboard-loading">
              <RefreshCw size={22} />
              <strong>Loading mission analytics...</strong>
              <span>Connecting to the ASTRA-PULSE backend.</span>
            </div>
          )}

          <section className="metrics-grid">
            <MetricCard
              icon={Users}
              label="Crew profiles"
              value={formatCount(crew.total)}
              unit=" members"
              detail={`${crew.active || 0} active Â· ${crew.on_mission || 0} on mission`}
              status="demo"
              color="blue"
            />

            <MetricCard
              icon={Orbit}
              label="Active missions"
              value={formatCount(missions.active)}
              unit=" missions"
              detail={`${missions.total || 0} total mission records`}
              status="demo"
              color="violet"
            />

            <MetricCard
              icon={HeartPulse}
              label="Synthetic readings"
              value={formatCount(health.total)}
              unit=" readings"
              detail={`${health.valid || 0} valid Â· ${health.suspect || 0} suspect`}
              status="demo"
              color="cyan"
            />

            <MetricCard
              icon={AlertTriangle}
              label="Open health alerts"
              value={formatCount(alerts.open)}
              unit=" alerts"
              detail={`${alerts.critical || 0} critical Â· ${alerts.warning || 0} warning`}
              status="demo"
              color="orange"
            />
          </section>

          <section className="dashboard-grid">
            <Suspense
              fallback={
                <div className="chart-container dashboard-state">
                  <RefreshCw size={22} />
                  <span>Loading telemetry chart...</span>
                </div>
              }
            >
              <TelemetryChart data={readings} />
            </Suspense>
            <AlertPanel alerts={criticalAlerts} />
          </section>

          <section className="bottom-grid">
            <MissionPanel missions={missionSummary} />
            <EnvironmentPanel />
          </section>

          <footer className="dashboard-footer">
            <div>
              <Command size={14} />
              ASTRA-PULSE AI 2.0
            </div>

            <span>
              Software research prototype Â· Synthetic data only
            </span>

            <div className="footer-status">
              <Signal size={14} /> Interface operational
            </div>
          </footer>
          </div>
        ) : activePage === "Missions" ? (
          <Suspense fallback={<LazyPageFallback />}>
            <MissionsPage />
          </Suspense>
        ) : activePage === "Health Alerts" ? (
          <Suspense fallback={<LazyPageFallback />}>
            <HealthAlertsPage />
          </Suspense>
        ) : activePage === "Simulator" ? (
          <Suspense fallback={<LazyPageFallback />}>
            <SimulatorPage />
          </Suspense>
        ) : activePage === "AI Intelligence" ? (
          <Suspense fallback={<LazyPageFallback />}>
            <AIIntelligencePage />
          </Suspense>
        ) : (
          <div className="page-container dashboard-page">
            <section className="welcome-section">
              <div>
                <div className="eyebrow">
                  <span className="eyebrow-line" />
                  MISSION WORKSPACE
                </div>
                <h1>
                  {activePage.split(" ")[0]}{" "}
                  <span className="gradient-text">
                    {activePage.split(" ").slice(1).join(" ")}
                  </span>
                </h1>
                <p>
                  This workspace module is planned for a future
                  implementation phase.
                </p>
              </div>
            </section>

            <div className="demo-notice">
              <div className="notice-icon">
                <Sparkles size={17} />
              </div>
              <div>
                <strong>Module under development</strong>
                <p>
                  The Overview and Crew Health modules are currently
                  available in this prototype.
                </p>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default DashboardPage;
