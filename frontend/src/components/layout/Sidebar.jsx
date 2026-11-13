import {
  CircleHelp,
  HeartPulse,
  LayoutDashboard,
  Orbit,
  Radio,
  Settings,
  ShieldAlert,
  Cpu,
  X,
} from "lucide-react";

const navigation = [
  { label: "Overview", icon: LayoutDashboard },
  { label: "Crew Health", icon: HeartPulse },
  { label: "Missions", icon: Orbit },
  { label: "AI Intelligence", icon: Cpu },
  { label: "Health Alerts", icon: ShieldAlert },
  { label: "Simulator", icon: Radio },
];

function Sidebar({ active, onNavigate, open, onClose, openAlerts = 0 }) {
  return (
    <>
      {open && (
        <button
          className="sidebar-overlay"
          onClick={onClose}
          aria-label="Close navigation"
        />
      )}

      <aside className={`sidebar ${open ? "sidebar-open" : ""}`}>
        <div className="brand">
          <div className="brand-symbol">
            <Orbit size={25} />
          </div>

          <div className="brand-copy">
            <strong>ASTRA<span>-PULSE</span></strong>
            <small>SPACE HEALTH INTELLIGENCE</small>
          </div>

          <button
            className="mobile-close"
            onClick={onClose}
            aria-label="Close sidebar"
          >
            <X size={19} />
          </button>
        </div>

        <div className="workspace-label">MISSION WORKSPACE</div>

        <nav className="navigation">
          {navigation.map((item) => {
            const Icon = item.icon;

            return (
              <button
                key={item.label}
                className={`nav-item ${
                  active === item.label ? "nav-active" : ""
                }`}
                onClick={() => {
                  onNavigate(item.label);
                  onClose();
                }}
              >
                <Icon size={18} />
                <span>{item.label}</span>

                {item.label === "Health Alerts" && openAlerts > 0 && (
                  <span className="nav-count">
                    {openAlerts > 99 ? "99+" : openAlerts}
                  </span>
                )}
              </button>
            );
          })}
        </nav>

        <div className="sidebar-bottom">
          <div className="sidebar-status">
            <div className="status-heading">
              <span className="live-dot" />
              SYSTEM OPERATIONAL
            </div>

            <p>Demo environment active</p>

            <div className="system-progress">
              <span />
            </div>
          </div>

          <button className="nav-item" disabled>
            <Settings size={18} />
            <span>Settings · Coming soon</span>
          </button>

          <button className="nav-item" disabled>
            <CircleHelp size={18} />
            <span>Documentation · Coming soon</span>
          </button>

          <div className="sidebar-version">
            ASTRA-PULSE AI · v2.0.0
          </div>
        </div>
      </aside>
    </>
  );
}

export default Sidebar;
