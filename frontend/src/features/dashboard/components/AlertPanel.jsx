import {
  Activity,
  AlertTriangle,
  ShieldAlert,
} from "lucide-react";

function formatTime(value) {
  if (!value) return "Time unavailable";

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return "Time unavailable";
  }

  return date.toLocaleString();
}

function AlertPanel({ alerts = [] }) {
  return (
    <section className="panel alerts-panel">
      <div className="section-heading">
        <div>
          <div className="section-title">Latest Critical Alerts</div>
          <div className="section-subtitle">
            Backend-generated synthetic health alerts
          </div>
        </div>

        <span className="alert-total">
          {String(alerts.length).padStart(2, "0")}
        </span>
      </div>

      <div className="alert-list">
        {alerts.length > 0 ? (
          alerts.map((alert) => {
            const level = String(alert.severity || "warning").toLowerCase();

            return (
              <div className="alert-item" key={alert.id}>
                <div className={`alert-icon ${level}`}>
                  {level === "critical" ? (
                    <AlertTriangle size={17} />
                  ) : (
                    <ShieldAlert size={17} />
                  )}
                </div>

                <div className="alert-content">
                  <div className="alert-title">
                    {alert.parameter || "Health parameter"} anomaly
                  </div>

                  <p>{alert.explanation || "No explanation provided."}</p>

                  <div className="alert-meta">
                    <span>{alert.rule_code}</span>
                    <span>{formatTime(alert.created_at)}</span>
                  </div>

                  <div className="alert-meta">
                    <span>{alert.astronaut_code}</span>
                    <span>{alert.status}</span>
                  </div>
                </div>

                <span className={`severity-tag ${level}`}>
                  {level}
                </span>
              </div>
            );
          })
        ) : (
          <div className="dashboard-state">
            <Activity size={23} />
            <strong>No critical alerts recorded</strong>
            <span>This does not imply clinical clearance.</span>
          </div>
        )}
      </div>
    </section>
  );
}

export default AlertPanel;
