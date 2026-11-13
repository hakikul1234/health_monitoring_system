import { useEffect, useMemo, useState } from "react";
import {
  Activity,
  AlertCircle,
  AlertTriangle,
  CheckCircle2,
  Clock3,
  Eye,
  Filter,
  RefreshCw,
  Search,
  ShieldCheck,
  X,
  ChevronLeft,
  ChevronRight,
  UserRound,
  Orbit,
  HeartPulse,
  ClipboardCheck,
} from "lucide-react";

import useAuthStore from "../../stores/authStore";
import useAlertStore from "./alertStore";

import "./HealthAlertsPage.css";

const PAGE_SIZE = 20;

const MANAGEMENT_ROLES = [
  "MEDICAL_OFFICER",
  "MISSION_CONTROL",
  "SYSTEM_ADMIN",
];

function formatDate(value) {
  if (!value) return "—";

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) return "—";

  return date.toLocaleString([], {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

function formatValue(value) {
  if (value === null || value === undefined) return "—";
  return String(value);
}

function getErrorMessage(error) {
  if (typeof error === "string") return error;

  if (error && typeof error === "object") {
    return (
      error.detail ||
      error.message ||
      Object.values(error).flat().join(" ") ||
      "An unexpected error occurred."
    );
  }

  return "An unexpected error occurred.";
}

function SeverityBadge({ severity }) {
  const critical = severity === "CRITICAL";

  return (
    <span className={`ha-badge ${critical ? "critical" : "warning"}`}>
      {critical ? (
        <AlertTriangle size={13} />
      ) : (
        <AlertCircle size={13} />
      )}
      {severity || "UNKNOWN"}
    </span>
  );
}

function StatusBadge({ status }) {
  const className = {
    OPEN: "open",
    ACKNOWLEDGED: "acknowledged",
    RESOLVED: "resolved",
  }[status] || "unknown";

  return (
    <span className={`ha-status ${className}`}>
      {status || "UNKNOWN"}
    </span>
  );
}

function StatCard({ label, value, icon: Icon, tone }) {
  return (
    <div className={`ha-stat-card ${tone}`}>
      <div className="ha-stat-icon">
        <Icon size={20} />
      </div>
      <div className="ha-stat-copy">
        <span>{label}</span>
        <strong>{value ?? 0}</strong>
      </div>
    </div>
  );
}

function AlertDetailModal({
  alert,
  canManage,
  isMutating,
  mutationError,
  onClose,
  onAcknowledge,
  onResolve,
  onClearMutationError,
}) {
  const [resolutionNotes, setResolutionNotes] = useState("");

  if (!alert) return null;

  const canAcknowledge =
    canManage && alert.status === "OPEN";

  const canResolve =
    canManage && alert.status === "ACKNOWLEDGED";

  const handleResolve = async (event) => {
    event.preventDefault();

    if (!resolutionNotes.trim()) return;

    await onResolve(alert.id, resolutionNotes.trim());
  };

  return (
    <div className="ha-modal-backdrop" onMouseDown={onClose}>
      <section
        className="ha-detail-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="ha-modal-title"
        onMouseDown={(event) => event.stopPropagation()}
      >
        <header className="ha-modal-header">
          <div>
            <span className="ha-eyebrow">ALERT INVESTIGATION</span>
            <h2 id="ha-modal-title">Alert Details</h2>
          </div>

          <button
            type="button"
            className="ha-icon-button"
            onClick={onClose}
            aria-label="Close alert details"
          >
            <X size={19} />
          </button>
        </header>

        <div className="ha-modal-body">
          <div className="ha-detail-badges">
            <SeverityBadge severity={alert.severity} />
            <StatusBadge status={alert.status} />
          </div>

          <div className="ha-detail-heading">
            <h3>{alert.parameter || "Health parameter"}</h3>
            <p>{alert.rule_code || "Rule not specified"}</p>
          </div>

          <div className="ha-observed-value">
            <span>Observed value</span>
            <strong>{formatValue(alert.observed_value)}</strong>
            <small>Recorded synthetic reading</small>
          </div>

          <div className="ha-detail-grid">
            <div>
              <UserRound size={16} />
              <span>Astronaut</span>
              <strong>
                {alert.astronaut?.full_name || "Unknown"}
              </strong>
              <small>
                {alert.astronaut?.astronaut_code || "No code"}
              </small>
            </div>

            <div>
              <Orbit size={16} />
              <span>Mission</span>
              <strong>
                {alert.mission?.mission_name || "Not assigned"}
              </strong>
              <small>
                {alert.mission?.mission_code || "No mission code"}
              </small>
            </div>

            <div>
              <Clock3 size={16} />
              <span>Created</span>
              <strong>{formatDate(alert.created_at)}</strong>
            </div>

            <div>
              <ShieldCheck size={16} />
              <span>Data source</span>
              <strong>
                {alert.is_synthetic ? "Synthetic" : "Non-synthetic"}
              </strong>
            </div>
          </div>

          <div className="ha-explanation">
            <h4>Explainable alert information</h4>
            <p>
              {alert.explanation || "No explanation provided."}
            </p>
          </div>

          {alert.acknowledged_by_username && (
            <div className="ha-audit-line">
              Acknowledged by {alert.acknowledged_by_username}
              {alert.acknowledged_at
                ? ` · ${formatDate(alert.acknowledged_at)}`
                : ""}
            </div>
          )}

          {alert.resolved_by_username && (
            <div className="ha-audit-line">
              Resolved by {alert.resolved_by_username}
              {alert.resolved_at
                ? ` · ${formatDate(alert.resolved_at)}`
                : ""}
            </div>
          )}

          {alert.resolution_notes && (
            <div className="ha-explanation">
              <h4>Resolution notes</h4>
              <p>{alert.resolution_notes}</p>
            </div>
          )}

          {canManage && (
            <div className="ha-modal-actions">
              {canAcknowledge && (
                <button
                  type="button"
                  className="ha-action-button acknowledge"
                  disabled={isMutating}
                  onClick={() => onAcknowledge(alert.id)}
                >
                  <ClipboardCheck size={16} />
                  Acknowledge alert
                </button>
              )}

              {canResolve && (
                <form
                  className="ha-resolution-form"
                  onSubmit={handleResolve}
                >
                  <label htmlFor="ha-resolution-notes">
                    Resolution notes
                  </label>

                  <textarea
                    id="ha-resolution-notes"
                    rows={3}
                    maxLength={5000}
                    required
                    value={resolutionNotes}
                    onChange={(event) =>
                      setResolutionNotes(event.target.value)
                    }
                    placeholder="Describe the review and resolution..."
                  />

                  <button
                    type="submit"
                    className="ha-action-button resolve"
                    disabled={isMutating || !resolutionNotes.trim()}
                  >
                    <CheckCircle2 size={16} />
                    Resolve alert
                  </button>
                </form>
              )}

              {mutationError && (
                <div className="ha-inline-error" role="alert">
                  {getErrorMessage(mutationError)}
                  <button
                    type="button"
                    onClick={onClearMutationError}
                  >
                    Dismiss
                  </button>
                </div>
              )}
            </div>
          )}

          {!canManage && (
            <p className="ha-readonly-note">
              Your account has read-only access to alert management.
            </p>
          )}
        </div>
      </section>
    </div>
  );
}

export default function HealthAlertsPage() {
  const user = useAuthStore((state) => state.user);

  const {
    alerts,
    selectedAlert,
    statistics,
    totalCount,
    next,
    previous,
    isLoading,
    isDetailLoading,
    isMutating,
    error,
    detailError,
    mutationError,
    fetchAlerts,
    fetchAlertDetail,
    acknowledgeAlert,
    resolveAlert,
    clearSelectedAlert,
    clearMutationError,
  } = useAlertStore();

  const canManage = MANAGEMENT_ROLES.includes(user?.role);

  const [searchInput, setSearchInput] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [severityFilter, setSeverityFilter] = useState("");
  const [currentPage, setCurrentPage] = useState(1);

  const filters = useMemo(
    () => ({
      page: currentPage,
      page_size: PAGE_SIZE,
      ...(searchInput.trim()
        ? { search: searchInput.trim() }
        : {}),
      ...(statusFilter ? { status: statusFilter } : {}),
      ...(severityFilter ? { severity: severityFilter } : {}),
    }),
    [currentPage, searchInput, statusFilter, severityFilter]
  );

  useEffect(() => {
    fetchAlerts(filters).catch(() => {});
  }, [fetchAlerts, filters]);

  const refresh = () => {
    fetchAlerts(filters).catch(() => {});
  };

  const openDetails = async (id) => {
    try {
      await fetchAlertDetail(id);
    } catch {
      // The store retains the detail error for display.
    }
  };

  const handleAcknowledge = async (id) => {
    try {
      await acknowledgeAlert(id);
      await fetchAlertDetail(id);
    } catch {
      // Mutation error is displayed by the store.
    }
  };

  const handleResolve = async (id, notes) => {
    try {
      await resolveAlert(id, notes);
      await fetchAlertDetail(id);
    } catch {
      // Mutation error is displayed by the store.
    }
  };

  const changeStatus = (value) => {
    setCurrentPage(1);
    setStatusFilter(value);
  };

  const changeSeverity = (value) => {
    setCurrentPage(1);
    setSeverityFilter(value);
  };

  const totalPages = Math.max(
    1,
    Math.ceil(totalCount / PAGE_SIZE)
  );

  return (
    <div className="page-container ha-page">
      <section className="ha-page-heading">
        <div>
          <span className="ha-eyebrow">
            ASTRA-PULSE / MISSION SAFETY
          </span>
          <h1>
            Health <span>Alerts</span>
          </h1>
          <p>
            Review explainable synthetic health alerts and track
            their acknowledgement and resolution workflow.
          </p>
        </div>

        <button
          type="button"
          className="ha-refresh-button"
          onClick={refresh}
          disabled={isLoading}
        >
          <RefreshCw
            size={16}
            className={isLoading ? "ha-spin" : ""}
          />
          Refresh
        </button>
      </section>

      <div className="ha-disclaimer">
        <ShieldCheck size={18} />
        <p>
          <strong>Research prototype:</strong> All alert records
          and statistics are synthetic demonstration data.
          They are not medical diagnoses or operational guidance.
          Human review is required.
        </p>
      </div>

      <section className="ha-stat-grid">
        <StatCard
          label="Total alerts"
          value={statistics.total_alerts}
          icon={Activity}
          tone="blue"
        />
        <StatCard
          label="Open"
          value={statistics.open_alerts}
          icon={AlertCircle}
          tone="orange"
        />
        <StatCard
          label="Acknowledged"
          value={statistics.acknowledged_alerts}
          icon={Clock3}
          tone="violet"
        />
        <StatCard
          label="Resolved"
          value={statistics.resolved_alerts}
          icon={CheckCircle2}
          tone="green"
        />
        <StatCard
          label="Critical"
          value={statistics.critical_alerts}
          icon={AlertTriangle}
          tone="red"
        />
      </section>

      <section className="ha-panel">
        <div className="ha-panel-heading">
          <div>
            <h2>Alert Directory</h2>
            <p>
              {totalCount} alert record{totalCount === 1 ? "" : "s"}
              {" "}available for your account
            </p>
          </div>

          <span className="ha-live-label">
            <i />
            API CONNECTED
          </span>
        </div>

        <div className="ha-toolbar">
          <div className="ha-search">
            <Search size={17} />
            <input
              type="search"
              value={searchInput}
              onChange={(event) => {
                setCurrentPage(1);
                setSearchInput(event.target.value);
              }}
              placeholder="Search parameter, rule, astronaut or mission..."
              aria-label="Search health alerts"
            />
          </div>

          <div className="ha-filter">
            <Filter size={15} />
            <select
              value={severityFilter}
              onChange={(event) => changeSeverity(event.target.value)}
              aria-label="Filter by severity"
            >
              <option value="">All severities</option>
              <option value="CRITICAL">Critical</option>
              <option value="WARNING">Warning</option>
            </select>
          </div>

          <div className="ha-filter">
            <select
              value={statusFilter}
              onChange={(event) => changeStatus(event.target.value)}
              aria-label="Filter by status"
            >
              <option value="">All statuses</option>
              <option value="OPEN">Open</option>
              <option value="ACKNOWLEDGED">Acknowledged</option>
              <option value="RESOLVED">Resolved</option>
            </select>
          </div>
        </div>

        {error && (
          <div className="ha-error-state" role="alert">
            <AlertTriangle size={20} />
            <div>
              <strong>Unable to load health alerts</strong>
              <p>{getErrorMessage(error)}</p>
            </div>
            <button type="button" onClick={refresh}>
              Retry
            </button>
          </div>
        )}

        {isLoading && (
          <div className="ha-loading">
            <RefreshCw size={22} className="ha-spin" />
            <span>Loading alert records...</span>
          </div>
        )}

        {!isLoading && !error && alerts.length === 0 && (
          <div className="ha-empty-state">
            <div className="ha-empty-icon">
              <HeartPulse size={27} />
            </div>
            <h3>No health alerts found</h3>
            <p>
              No records match the selected filters. Alerts will
              appear here when synthetic telemetry analysis
              generates persistent findings.
            </p>
            {(searchInput || statusFilter || severityFilter) && (
              <button
                type="button"
                onClick={() => {
                  setSearchInput("");
                  setStatusFilter("");
                  setSeverityFilter("");
                  setCurrentPage(1);
                }}
              >
                Clear filters
              </button>
            )}
          </div>
        )}

        {!isLoading && !error && alerts.length > 0 && (
          <>
            <div className="ha-table-wrap">
              <table className="ha-table">
                <thead>
                  <tr>
                    <th>Alert</th>
                    <th>Astronaut</th>
                    <th>Severity</th>
                    <th>Observed</th>
                    <th>Status</th>
                    <th>Created</th>
                    <th>Action</th>
                  </tr>
                </thead>

                <tbody>
                  {alerts.map((alert) => (
                    <tr key={alert.id}>
                      <td>
                        <div className="ha-alert-cell">
                          <strong>{alert.parameter}</strong>
                          <small>{alert.rule_code}</small>
                        </div>
                      </td>

                      <td>
                        <div className="ha-astronaut-cell">
                          <strong>
                            {alert.astronaut?.full_name || "Unknown"}
                          </strong>
                          <small>
                            {alert.astronaut?.astronaut_code || "—"}
                          </small>
                        </div>
                      </td>

                      <td>
                        <SeverityBadge severity={alert.severity} />
                      </td>

                      <td className="ha-value-cell">
                        {formatValue(alert.observed_value)}
                      </td>

                      <td>
                        <StatusBadge status={alert.status} />
                      </td>

                      <td className="ha-date-cell">
                        {formatDate(alert.created_at)}
                      </td>

                      <td>
                        <button
                          type="button"
                          className="ha-view-button"
                          onClick={() => openDetails(alert.id)}
                          aria-label={`View alert ${alert.id}`}
                        >
                          <Eye size={15} />
                          View
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="ha-pagination">
              <span>
                Showing {Math.min((currentPage - 1) * PAGE_SIZE + 1, totalCount)}
                {" "}–{Math.min(currentPage * PAGE_SIZE, totalCount)}
                {" "}of {totalCount}
              </span>

              <div>
                <button
                  type="button"
                  disabled={!previous || currentPage <= 1}
                  onClick={() => setCurrentPage((page) => page - 1)}
                  aria-label="Previous page"
                >
                  <ChevronLeft size={17} />
                </button>

                <strong>{currentPage} / {totalPages}</strong>

                <button
                  type="button"
                  disabled={!next || currentPage >= totalPages}
                  onClick={() => setCurrentPage((page) => page + 1)}
                  aria-label="Next page"
                >
                  <ChevronRight size={17} />
                </button>
              </div>
            </div>
          </>
        )}
      </section>

      {isDetailLoading && (
        <div className="ha-detail-loading">
          <RefreshCw size={17} className="ha-spin" />
          Loading alert details...
        </div>
      )}

      {detailError && (
        <div className="ha-error-state" role="alert">
          {getErrorMessage(detailError)}
          <button type="button" onClick={clearSelectedAlert}>
            Dismiss
          </button>
        </div>
      )}

      {selectedAlert && !isDetailLoading && (
        <AlertDetailModal
          alert={selectedAlert}
          canManage={canManage}
          isMutating={isMutating}
          mutationError={mutationError}
          onClose={clearSelectedAlert}
          onAcknowledge={handleAcknowledge}
          onResolve={handleResolve}
          onClearMutationError={clearMutationError}
        />
      )}
    </div>
  );
}
