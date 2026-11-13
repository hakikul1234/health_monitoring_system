import { useEffect, useMemo, useState } from "react";

import {
  Activity,
  AlertCircle,
  Clock3,
  HeartPulse,
  RefreshCw,
  Search,
  ShieldCheck,
  Users,
  Wind,
  Thermometer,
  Droplets,
  UserRound,
  XCircle,
} from "lucide-react";

import useCrewHealthStore from "./crewHealthStore";
import CrewReadingAnalysis from "./CrewReadingAnalysis";

import "./CrewHealthPage.css";

const STATUS_OPTIONS = [
  "ALL",
  "TRAINING",
  "ACTIVE",
  "ON_MISSION",
  "INACTIVE",
];

function formatStatus(status) {
  return String(status || "UNKNOWN")
    .replaceAll("_", " ")
    .toLowerCase()
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function formatDate(value) {
  if (!value) return "Not available";

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return "Not available";
  }

  return date.toLocaleString([], {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

function getLatestReading(readings, astronautId) {
  return readings
    .filter(
      (reading) =>
        reading.astronaut?.id === astronautId &&
        reading.is_synthetic === true
    )
    .slice()
    .sort(
      (a, b) =>
        new Date(b.recorded_at).getTime() -
        new Date(a.recorded_at).getTime()
    )[0] || null;
}

function Metric({ icon: Icon, label, value, unit }) {
  return (
    <div className="crew-vital">
      <div className="crew-vital-icon">
        <Icon size={15} />
      </div>

      <div className="crew-vital-copy">
        <span>{label}</span>
        <strong>
          {value ?? "--"}
          {value !== null && value !== undefined && value !== "--" && (
            <small> {unit}</small>
          )}
        </strong>
      </div>
    </div>
  );
}

function QualityBadge({ quality }) {
  const normalized = quality || "UNAVAILABLE";

  const className = normalized.toLowerCase().replaceAll("_", "-");

  return (
    <span className={`crew-quality crew-quality-${className}`}>
      <span />
      {formatStatus(normalized)}
    </span>
  );
}

function CrewHealthPage() {
  const astronauts = useCrewHealthStore((state) => state.astronauts);
  const readings = useCrewHealthStore((state) => state.readings);

  const isLoading = useCrewHealthStore((state) => state.isLoading);
  const error = useCrewHealthStore((state) => state.error);

  const fetchCrewHealth = useCrewHealthStore(
    (state) => state.fetchCrewHealth
  );

  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("ALL");

  useEffect(() => {
    fetchCrewHealth().catch(() => {});
  }, [fetchCrewHealth]);

  const crewWithReadings = useMemo(() => {
    return astronauts.map((astronaut) => ({
      astronaut,
      reading: getLatestReading(readings, astronaut.id),
    }));
  }, [astronauts, readings]);

  const filteredCrew = useMemo(() => {
    const query = search.trim().toLowerCase();

    return crewWithReadings.filter(({ astronaut }) => {
      const fullName = astronaut.profile?.full_name || "";
      const code = astronaut.astronaut_code || "";
      const callSign = astronaut.call_sign || "";
      const designation = astronaut.designation || "";

      const matchesSearch = [
        fullName,
        code,
        callSign,
        designation,
      ].some((value) => value.toLowerCase().includes(query));

      const matchesStatus =
        statusFilter === "ALL" ||
        astronaut.status === statusFilter;

      return matchesSearch && matchesStatus;
    });
  }, [crewWithReadings, search, statusFilter]);

  const summary = useMemo(() => {
    return {
      total: astronauts.length,
      active: astronauts.filter(
        (item) => item.status === "ACTIVE"
      ).length,
      onMission: astronauts.filter(
        (item) => item.status === "ON_MISSION"
      ).length,
      withReadings: crewWithReadings.filter(
        (item) => item.reading !== null
      ).length,
    };
  }, [astronauts, crewWithReadings]);

  return (
    <div className="page-container crew-health-page">
      <section className="crew-page-heading">
        <div>
          <div className="eyebrow">
            <span className="eyebrow-line" />
            CREW HEALTH INTELLIGENCE
          </div>

          <h1>
            Crew <span className="gradient-text">Health</span>
          </h1>

          <p>
            Explore astronaut profiles and available synthetic
            physiological telemetry.
          </p>
        </div>

        <button
          className="crew-refresh-button"
          type="button"
          onClick={() => fetchCrewHealth({ force: true }).catch(() => {})}
          disabled={isLoading}
        >
          <RefreshCw
            size={15}
            className={isLoading ? "crew-spin" : ""}
          />
          Refresh data
        </button>
      </section>

      <div className="crew-prototype-notice">
        <ShieldCheck size={19} />

        <div>
          <strong>Research prototype · Synthetic telemetry only</strong>
          <p>
            These readings are simulated demonstration data, not
            clinical measurements. They must not be used for diagnosis
            or operational medical decisions.
          </p>
        </div>
      </div>

      <section className="crew-summary-grid">
        <div className="crew-summary-card">
          <div className="crew-summary-icon crew-icon-blue">
            <Users size={19} />
          </div>
          <div>
            <span>Total crew profiles</span>
            <strong>{summary.total}</strong>
          </div>
        </div>

        <div className="crew-summary-card">
          <div className="crew-summary-icon crew-icon-green">
            <UserRound size={19} />
          </div>
          <div>
            <span>Active profiles</span>
            <strong>{summary.active}</strong>
          </div>
        </div>

        <div className="crew-summary-card">
          <div className="crew-summary-icon crew-icon-violet">
            <Activity size={19} />
          </div>
          <div>
            <span>On mission</span>
            <strong>{summary.onMission}</strong>
          </div>
        </div>

        <div className="crew-summary-card">
          <div className="crew-summary-icon crew-icon-cyan">
            <HeartPulse size={19} />
          </div>
          <div>
            <span>Profiles with readings</span>
            <strong>{summary.withReadings}</strong>
          </div>
        </div>
      </section>

      <section className="crew-directory-panel">
        <div className="crew-directory-heading">
          <div>
            <h2>Crew Directory</h2>
            <p>
              {filteredCrew.length} of {astronauts.length} crew profiles
            </p>
          </div>

          <span className="crew-live-indicator">
            <span />
            API DATA
          </span>
        </div>

        <div className="crew-filters">
          <div className="crew-search">
            <Search size={17} />

            <input
              type="search"
              placeholder="Search name, code or call sign..."
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              aria-label="Search crew"
            />

            {search && (
              <button
                type="button"
                onClick={() => setSearch("")}
                aria-label="Clear search"
              >
                <XCircle size={16} />
              </button>
            )}
          </div>

          <select
            value={statusFilter}
            onChange={(event) => setStatusFilter(event.target.value)}
            aria-label="Filter crew by status"
          >
            {STATUS_OPTIONS.map((status) => (
              <option key={status} value={status}>
                {status === "ALL" ? "All statuses" : formatStatus(status)}
              </option>
            ))}
          </select>
        </div>

        {error && (
          <div className="crew-state crew-error">
            <AlertCircle size={20} />
            <div>
              <strong>Unable to load crew data</strong>
              <p>{String(error)}</p>
            </div>

            <button
              type="button"
              onClick={() => fetchCrewHealth({ force: true }).catch(() => {})}
              disabled={isLoading}
            >
              Retry
            </button>
          </div>
        )}

        {isLoading && astronauts.length === 0 && !error && (
          <div className="crew-state">
            <RefreshCw size={22} className="crew-spin" />
            <strong>Loading crew directory...</strong>
            <p>Retrieving authorized crew and telemetry records.</p>
          </div>
        )}

        {!isLoading && !error && astronauts.length === 0 && (
          <div className="crew-state">
            <Users size={28} />
            <strong>No astronaut profiles available</strong>
            <p>
              No crew records were returned by the backend for this
              account. No sample profiles have been fabricated.
            </p>
          </div>
        )}

        {!isLoading && !error && astronauts.length > 0 &&
          filteredCrew.length === 0 && (
            <div className="crew-state">
              <Search size={25} />
              <strong>No matching crew members</strong>
              <p>Try another search term or status filter.</p>
            </div>
          )}

        {filteredCrew.length > 0 && (
          <div className="crew-card-grid">
            {filteredCrew.map(({ astronaut, reading }) => {
              const name =
                astronaut.profile?.full_name ||
                astronaut.profile?.username ||
                "Unnamed astronaut";

              return (
                <article
                  className="crew-member-card"
                  key={astronaut.id}
                >
                  <div className="crew-member-heading">
                    <div className="crew-avatar">
                      {name
                        .split(/\s+/)
                        .slice(0, 2)
                        .map((part) => part[0])
                        .join("")
                        .toUpperCase()}
                    </div>

                    <div className="crew-member-identity">
                      <h3>{name}</h3>
                      <span>
                        {astronaut.call_sign || "Call sign unavailable"}
                      </span>
                    </div>

                    <span
                      className={`crew-status crew-status-${String(
                        astronaut.status || "unknown"
                      ).toLowerCase()}`}
                    >
                      {formatStatus(astronaut.status)}
                    </span>
                  </div>

                  <div className="crew-member-meta">
                    <div>
                      <span>Astronaut code</span>
                      <strong>{astronaut.astronaut_code || "--"}</strong>
                    </div>

                    <div>
                      <span>Designation</span>
                      <strong>{astronaut.designation || "--"}</strong>
                    </div>

                    <div>
                      <span>Specialization</span>
                      <strong>
                        {astronaut.mission_specialization || "--"}
                      </strong>
                    </div>
                  </div>

                  <div className="crew-vitals-heading">
                    <span>Latest synthetic telemetry</span>
                    <QualityBadge
                      quality={reading?.data_quality || "UNAVAILABLE"}
                    />
                  </div>

                  {reading ? (
                    <>
                      <div className="crew-vitals-grid">
                        <Metric
                          icon={HeartPulse}
                          label="Heart rate"
                          value={reading.heart_rate_bpm}
                          unit="BPM"
                        />

                        <Metric
                          icon={Droplets}
                          label="SpO2"
                          value={reading.spo2_percent}
                          unit="%"
                        />

                        <Metric
                          icon={Thermometer}
                          label="Temperature"
                          value={reading.body_temperature_c}
                          unit="°C"
                        />

                        <Metric
                          icon={Wind}
                          label="Respiratory rate"
                          value={reading.respiratory_rate_bpm}
                          unit="/min"
                        />
                      </div>

                      <div className="crew-reading-time">
                        <Clock3 size={13} />
                        Recorded {formatDate(reading.recorded_at)}
                      </div>

                      <CrewReadingAnalysis readingId={reading.id} />
                    </>
                  ) : (
                    <div className="crew-no-reading">
                      <Activity size={17} />
                      <span>No synthetic telemetry available</span>
                    </div>
                  )}
                </article>
              );
            })}
          </div>
        )}
      </section>

      <footer className="crew-page-footer">
        ASTRA-PULSE AI 2.0 · Crew data is subject to backend role permissions.
      </footer>
    </div>
  );
}

export default CrewHealthPage;
