import { Orbit, ShieldCheck } from "lucide-react";

function MissionPanel({ missions = [] }) {
  return (
    <section className="panel crew-panel">
      <div className="section-heading">
        <div>
          <div className="section-title">Mission Summary</div>
          <div className="section-subtitle">
            Backend mission records · Synthetic health data
          </div>
        </div>

        <Orbit size={19} className="heading-icon" />
      </div>

      <div className="crew-list">
        {missions.length > 0 ? (
          missions.map((mission, index) => {
            const status = String(mission.status || "UNKNOWN").toUpperCase();

            return (
              <div className="crew-member" key={mission.id}>
                <div className={`crew-avatar ${["blue", "violet", "cyan"][index % 3]}`}>
                  <Orbit size={17} />
                </div>

                <div className="crew-info">
                  <strong>{mission.mission_name || mission.mission_code}</strong>
                  <span>
                    {mission.mission_code} · {mission.destination || "Destination unavailable"}
                  </span>
                  <span>
                    Crew: {mission.crew_count} · Readings: {mission.reading_count}
                  </span>
                </div>

                <span className={`crew-status ${status === "ABORTED" ? "review" : ""}`}>
                  <i />
                  {status}
                </span>
              </div>
            );
          })
        ) : (
          <div className="dashboard-state">
            <Orbit size={23} />
            <strong>No mission records available</strong>
            <span>Create or assign a mission to populate this section.</span>
          </div>
        )}
      </div>

      <div className="crew-footer">
        <span>{missions.length} mission summaries shown</span>

        <span className="crew-footer-label">
          <ShieldCheck size={14} /> Human review required
        </span>
      </div>
    </section>
  );
}

export default MissionPanel;
