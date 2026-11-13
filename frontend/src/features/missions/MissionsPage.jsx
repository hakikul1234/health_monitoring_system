import { useEffect, useMemo, useState } from "react";

import {
  Orbit,
  Plus,
  RefreshCw,
  Search,
  CalendarDays,
  Users,
  MapPin,
  Clock3,
  Pencil,
  Trash2,
  X,
  Rocket,
  AlertCircle,
  Info,
  CheckCircle2,
  Eye,
  Flag,
} from "lucide-react";

import useAuthStore from "../../stores/authStore";
import useMissionStore from "./missionStore";
import useCrewHealthStore from "../crew/crewHealthStore";

import "./MissionsPage.css";

const MISSION_TYPES = [
  { value: "ORBITAL", label: "Orbital Mission" },
  { value: "LUNAR", label: "Lunar Mission" },
  { value: "DEEP_SPACE", label: "Deep Space Mission" },
  { value: "RESEARCH", label: "Research Mission" },
];

const MISSION_STATUSES = [
  { value: "PLANNED", label: "Planned" },
  { value: "ACTIVE", label: "Active" },
  { value: "COMPLETED", label: "Completed" },
  { value: "ABORTED", label: "Aborted" },
];

const EMPTY_FORM = {
  mission_code: "",
  mission_name: "",
  mission_type: "RESEARCH",
  status: "PLANNED",
  destination: "",
  description: "",
  objectives: "",
  planned_start_date: "",
  planned_end_date: "",
  crew_ids: [],
};

function formatLabel(value) {
  return String(value || "UNKNOWN")
    .replaceAll("_", " ")
    .toLowerCase()
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function formatDate(value) {
  if (!value) return "Not scheduled";

  const date = new Date(`${value}T00:00:00`);

  if (Number.isNaN(date.getTime())) {
    return "Not available";
  }

  return date.toLocaleDateString([], {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

function getCrewName(member) {
  return member.full_name || member.call_sign || member.astronaut_code;
}

function MissionStatus({ status }) {
  const normalized = String(status || "UNKNOWN").toLowerCase();

  return (
    <span className={`mission-status mission-status-${normalized}`}>
      <span />
      {formatLabel(status)}
    </span>
  );
}

function SummaryCard({ icon: Icon, label, value, tone }) {
  return (
    <article className="mission-summary-card">
      <div className={`mission-summary-icon mission-tone-${tone}`}>
        <Icon size={19} />
      </div>

      <div>
        <span>{label}</span>
        <strong>{value}</strong>
      </div>
    </article>
  );
}

function MissionForm({
  initialData,
  astronauts,
  isSaving,
  error,
  onClose,
  onSubmit,
}) {
  const [form, setForm] = useState(() => ({
    ...EMPTY_FORM,
    ...(initialData || {}),
    crew_ids: (initialData?.crew || []).map((member) => member.id),
    planned_start_date: initialData?.planned_start_date || "",
    planned_end_date: initialData?.planned_end_date || "",
  }));

  const [formError, setFormError] = useState("");

  const editing = Boolean(initialData?.id);

  const updateField = (field, value) => {
    setForm((current) => ({
      ...current,
      [field]: value,
    }));

    setFormError("");
  };

  const handleCrewChange = (event) => {
    const ids = Array.from(
      event.target.selectedOptions,
      (option) => Number(option.value)
    );

    updateField("crew_ids", ids);
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setFormError("");

    if (!form.mission_code.trim() || !form.mission_name.trim()) {
      setFormError("Mission code and mission name are required.");
      return;
    }

    if (
      form.planned_start_date &&
      form.planned_end_date &&
      form.planned_end_date < form.planned_start_date
    ) {
      setFormError("End date cannot be earlier than start date.");
      return;
    }

    const payload = {
      mission_code: form.mission_code.trim(),
      mission_name: form.mission_name.trim(),
      mission_type: form.mission_type,
      status: form.status,
      destination: form.destination.trim(),
      description: form.description.trim(),
      objectives: form.objectives.trim(),
      planned_start_date: form.planned_start_date || null,
      planned_end_date: form.planned_end_date || null,
      crew_ids: form.crew_ids,
    };

    try {
      await onSubmit(payload);
    } catch {
      // Store exposes the API error in the form.
    }
  };

  return (
    <div
      className="mission-modal-backdrop"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) onClose();
      }}
    >
      <section
        className="mission-modal mission-form-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="mission-form-title"
      >
        <header className="mission-modal-header">
          <div>
            <span className="mission-modal-eyebrow">
              MISSION CONTROL
            </span>

            <h2 id="mission-form-title">
              {editing ? "Update mission" : "Create mission"}
            </h2>

            <p>
              Configure mission details and assign available crew.
            </p>
          </div>

          <button
            type="button"
            className="mission-icon-button"
            onClick={onClose}
            aria-label="Close form"
          >
            <X size={19} />
          </button>
        </header>

        <form className="mission-form" onSubmit={handleSubmit}>
          <div className="mission-form-grid">
            <label>
              Mission code *
              <input
                value={form.mission_code}
                onChange={(event) =>
                  updateField("mission_code", event.target.value)
                }
                placeholder="e.g. AP-ORBIT-001"
                maxLength={40}
                required
              />
            </label>

            <label>
              Mission name *
              <input
                value={form.mission_name}
                onChange={(event) =>
                  updateField("mission_name", event.target.value)
                }
                placeholder="Enter mission name"
                maxLength={150}
                required
              />
            </label>

            <label>
              Mission type
              <select
                value={form.mission_type}
                onChange={(event) =>
                  updateField("mission_type", event.target.value)
                }
              >
                {MISSION_TYPES.map((type) => (
                  <option key={type.value} value={type.value}>
                    {type.label}
                  </option>
                ))}
              </select>
            </label>

            <label>
              Mission status
              <select
                value={form.status}
                onChange={(event) =>
                  updateField("status", event.target.value)
                }
              >
                {MISSION_STATUSES.map((status) => (
                  <option key={status.value} value={status.value}>
                    {status.label}
                  </option>
                ))}
              </select>
            </label>

            <label className="mission-form-full">
              Destination
              <input
                value={form.destination}
                onChange={(event) =>
                  updateField("destination", event.target.value)
                }
                placeholder="e.g. Low Earth Orbit"
                maxLength={150}
              />
            </label>

            <label>
              Planned start date
              <input
                type="date"
                value={form.planned_start_date}
                onChange={(event) =>
                  updateField("planned_start_date", event.target.value)
                }
              />
            </label>

            <label>
              Planned end date
              <input
                type="date"
                min={form.planned_start_date || undefined}
                value={form.planned_end_date}
                onChange={(event) =>
                  updateField("planned_end_date", event.target.value)
                }
              />
            </label>

            <label className="mission-form-full">
              Mission description
              <textarea
                rows={3}
                value={form.description}
                onChange={(event) =>
                  updateField("description", event.target.value)
                }
                placeholder="Describe the mission..."
              />
            </label>

            <label className="mission-form-full">
              Mission objectives
              <textarea
                rows={3}
                value={form.objectives}
                onChange={(event) =>
                  updateField("objectives", event.target.value)
                }
                placeholder="List mission objectives..."
              />
            </label>

            <label className="mission-form-full">
              Assign astronaut crew
              <select
                multiple
                size={Math.min(Math.max(astronauts.length, 3), 6)}
                value={form.crew_ids.map(String)}
                onChange={handleCrewChange}
                className="mission-crew-select"
              >
                {astronauts.map((astronaut) => (
                  <option
                    key={astronaut.id}
                    value={String(astronaut.id)}
                  >
                    {astronaut.profile?.full_name ||
                      astronaut.call_sign ||
                      astronaut.astronaut_code}
                    {" — "}
                    {astronaut.astronaut_code}
                  </option>
                ))}
              </select>

              <small className="mission-field-help">
                Hold Ctrl (Windows) or Command (Mac) to select multiple crew members.
                {form.crew_ids.length > 0
                  ? ` ${form.crew_ids.length} selected.`
                  : " No crew selected."}
              </small>

              {astronauts.length === 0 && (
                <small className="mission-field-warning">
                  No astronaut profiles are currently available.
                  Create crew profiles before assigning astronauts.
                </small>
              )}
            </label>
          </div>

          {(formError || error) && (
            <div className="mission-form-error">
              <AlertCircle size={16} />
              <span>{formError || String(error)}</span>
            </div>
          )}

          <footer className="mission-form-actions">
            <button
              type="button"
              className="mission-secondary-button"
              onClick={onClose}
            >
              Cancel
            </button>

            <button
              type="submit"
              className="mission-primary-button"
              disabled={isSaving}
            >
              {isSaving && <RefreshCw size={15} className="mission-spin" />}
              {editing ? "Save changes" : "Create mission"}
            </button>
          </footer>
        </form>
      </section>
    </div>
  );
}

function MissionDetails({ mission, onClose, canManage, onEdit, onDelete }) {
  if (!mission) return null;

  return (
    <div className="mission-modal-backdrop" onMouseDown={(event) => {
      if (event.target === event.currentTarget) onClose();
    }}>
      <section
        className="mission-modal mission-detail-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="mission-detail-title"
      >
        <header className="mission-modal-header">
          <div>
            <span className="mission-modal-eyebrow">
              MISSION RECORD · {mission.mission_code}
            </span>
            <h2 id="mission-detail-title">{mission.mission_name}</h2>
            <p>{formatLabel(mission.mission_type)}</p>
          </div>

          <button
            type="button"
            className="mission-icon-button"
            onClick={onClose}
            aria-label="Close details"
          >
            <X size={19} />
          </button>
        </header>

        <div className="mission-detail-content">
          <div className="mission-detail-status">
            <MissionStatus status={mission.status} />
            <span>{mission.destination || "Destination not specified"}</span>
          </div>

          <div className="mission-detail-grid">
            <div>
              <span>Start date</span>
              <strong>{formatDate(mission.planned_start_date)}</strong>
            </div>

            <div>
              <span>End date</span>
              <strong>{formatDate(mission.planned_end_date)}</strong>
            </div>

            <div>
              <span>Created by</span>
              <strong>{mission.created_by?.username || "Unavailable"}</strong>
            </div>

            <div>
              <span>Crew assigned</span>
              <strong>{mission.crew?.length || 0} members</strong>
            </div>
          </div>

          <div className="mission-detail-section">
            <h3>Description</h3>
            <p>{mission.description || "No description provided."}</p>
          </div>

          <div className="mission-detail-section">
            <h3>Mission objectives</h3>
            <p>{mission.objectives || "No objectives provided."}</p>
          </div>

          <div className="mission-detail-section">
            <h3>Assigned crew</h3>

            {mission.crew?.length ? (
              <div className="mission-detail-crew">
                {mission.crew.map((member) => (
                  <div key={member.id}>
                    <Users size={15} />
                    <span>{getCrewName(member)}</span>
                    <small>{member.astronaut_code}</small>
                  </div>
                ))}
              </div>
            ) : (
              <p>No crew members assigned.</p>
            )}
          </div>
        </div>

        <footer className="mission-form-actions">
          <button
            type="button"
            className="mission-secondary-button"
            onClick={onClose}
          >
            Close
          </button>

          {canManage && (
            <>
              <button
                type="button"
                className="mission-secondary-button"
                onClick={() => onEdit(mission)}
              >
                <Pencil size={15} /> Edit
              </button>

              <button
                type="button"
                className="mission-danger-button"
                onClick={() => onDelete(mission)}
              >
                <Trash2 size={15} /> Delete
              </button>
            </>
          )}
        </footer>
      </section>
    </div>
  );
}

function MissionsPage() {
  const user = useAuthStore((state) => state.user);

  const missions = useMissionStore((state) => state.missions);
  const selectedMission = useMissionStore((state) => state.selectedMission);

  const isLoading = useMissionStore((state) => state.isLoading);
  const isSaving = useMissionStore((state) => state.isSaving);
  const isDeleting = useMissionStore((state) => state.isDeleting);

  const error = useMissionStore((state) => state.error);
  const mutationError = useMissionStore((state) => state.mutationError);

  const fetchMissions = useMissionStore((state) => state.fetchMissions);
  const fetchMissionDetail = useMissionStore(
    (state) => state.fetchMissionDetail
  );
  const addMission = useMissionStore((state) => state.addMission);
  const editMission = useMissionStore((state) => state.editMission);
  const removeMission = useMissionStore((state) => state.removeMission);
  const clearSelectedMission = useMissionStore(
    (state) => state.clearSelectedMission
  );
  const clearMutationError = useMissionStore(
    (state) => state.clearMutationError
  );

  const astronauts = useCrewHealthStore((state) => state.astronauts);
  const fetchCrewHealth = useCrewHealthStore(
    (state) => state.fetchCrewHealth
  );

  const canManage =
    user?.role === "MISSION_CONTROL" ||
    user?.role === "SYSTEM_ADMIN";

  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [typeFilter, setTypeFilter] = useState("ALL");

  const [showForm, setShowForm] = useState(false);
  const [editingMission, setEditingMission] = useState(null);
  const [detailsLoadingId, setDetailsLoadingId] = useState(null);

  useEffect(() => {
    fetchMissions().catch(() => {});
    fetchCrewHealth().catch(() => {});
  }, [fetchMissions, fetchCrewHealth]);

  const summary = useMemo(() => ({
    total: missions.length,
    active: missions.filter((item) => item.status === "ACTIVE").length,
    planned: missions.filter((item) => item.status === "PLANNED").length,
    completed: missions.filter((item) => item.status === "COMPLETED").length,
  }), [missions]);

  const filteredMissions = useMemo(() => {
    const query = search.trim().toLowerCase();

    return missions.filter((mission) => {
      const matchesSearch = [
        mission.mission_code,
        mission.mission_name,
        mission.destination,
      ].some((value) => String(value || "").toLowerCase().includes(query));

      const matchesStatus =
        statusFilter === "ALL" || mission.status === statusFilter;

      const matchesType =
        typeFilter === "ALL" || mission.mission_type === typeFilter;

      return matchesSearch && matchesStatus && matchesType;
    });
  }, [missions, search, statusFilter, typeFilter]);

  const handleRefresh = () => {
    fetchMissions({ force: true }).catch(() => {});
    fetchCrewHealth({ force: true }).catch(() => {});
  };

  const handleCreate = () => {
    clearMutationError();
    setEditingMission(null);
    setShowForm(true);
  };

  const handleEdit = (mission) => {
    clearSelectedMission();
    clearMutationError();
    setEditingMission(mission);
    setShowForm(true);
  };

  const handleFormSubmit = async (payload) => {
    if (editingMission) {
      await editMission(editingMission.id, payload);
    } else {
      await addMission(payload);
    }

    setShowForm(false);
    setEditingMission(null);
  };

  const handleDelete = async (mission) => {
    const confirmed = window.confirm(
      `Delete mission "${mission.mission_name}" (${mission.mission_code})? This action cannot be undone.`
    );

    if (!confirmed) return;

    try {
      await removeMission(mission.id);
      clearSelectedMission();
    } catch {
      // The store retains the API error.
    }
  };

  const handleOpenDetails = async (mission) => {
    setDetailsLoadingId(mission.id);

    try {
      await fetchMissionDetail(mission.id);
    } catch {
      // Detail error is exposed by the store.
    } finally {
      setDetailsLoadingId(null);
    }
  };

  return (
    <div className="page-container missions-page">
      <section className="mission-page-heading">
        <div>
          <div className="eyebrow">
            <span className="eyebrow-line" />
            SPACE OPERATIONS WORKSPACE
          </div>

          <h1>
            Mission <span className="gradient-text">Management</span>
          </h1>

          <p>
            Plan, organize and monitor mission records and assigned crew.
          </p>
        </div>

        <div className="mission-heading-actions">
          <button
            type="button"
            className="mission-secondary-button"
            onClick={handleRefresh}
            disabled={isLoading}
          >
            <RefreshCw size={15} className={isLoading ? "mission-spin" : ""} />
            Refresh
          </button>

          {canManage && (
            <button
              type="button"
              className="mission-primary-button"
              onClick={handleCreate}
            >
              <Plus size={17} />
              New mission
            </button>
          )}
        </div>
      </section>

      <div className="mission-prototype-notice">
        <Info size={18} />

        <div>
          <strong>Research prototype · Mission records</strong>
          <p>
            ASTRA-PULSE AI 2.0 is a software research prototype.
            Mission records and telemetry do not represent live space operations.
          </p>
        </div>
      </div>

      <section className="mission-summary-grid">
        <SummaryCard
          icon={Orbit}
          label="Total missions"
          value={summary.total}
          tone="blue"
        />

        <SummaryCard
          icon={Rocket}
          label="Active missions"
          value={summary.active}
          tone="green"
        />

        <SummaryCard
          icon={Clock3}
          label="Planned missions"
          value={summary.planned}
          tone="violet"
        />

        <SummaryCard
          icon={CheckCircle2}
          label="Completed missions"
          value={summary.completed}
          tone="cyan"
        />
      </section>

      {error && (
        <div className="mission-error-state">
          <AlertCircle size={19} />
          <div>
            <strong>Mission records could not be loaded</strong>
            <p>{String(error)}</p>
          </div>

          <button
            type="button"
            onClick={handleRefresh}
            disabled={isLoading}
          >
            Retry
          </button>
        </div>
      )}

      {mutationError && !showForm && (
        <div className="mission-error-state">
          <AlertCircle size={19} />
          <div>
            <strong>Mission operation failed</strong>
            <p>{String(mutationError)}</p>
          </div>

          <button type="button" onClick={clearMutationError}>
            Dismiss
          </button>
        </div>
      )}

      <section className="mission-directory">
        <div className="mission-directory-heading">
          <div>
            <h2>Mission directory</h2>
            <p>
              {filteredMissions.length} of {missions.length} mission records
            </p>
          </div>

          <span className="mission-directory-indicator">
            <span />
            API DATA
          </span>
        </div>

        <div className="mission-filter-bar">
          <label className="mission-search">
            <Search size={17} />
            <input
              type="search"
              placeholder="Search missions, codes or destinations..."
              value={search}
              onChange={(event) => setSearch(event.target.value)}
            />
          </label>

          <select
            value={statusFilter}
            onChange={(event) => setStatusFilter(event.target.value)}
            aria-label="Filter by mission status"
          >
            <option value="ALL">All statuses</option>
            {MISSION_STATUSES.map((status) => (
              <option key={status.value} value={status.value}>
                {status.label}
              </option>
            ))}
          </select>

          <select
            value={typeFilter}
            onChange={(event) => setTypeFilter(event.target.value)}
            aria-label="Filter by mission type"
          >
            <option value="ALL">All mission types</option>
            {MISSION_TYPES.map((type) => (
              <option key={type.value} value={type.value}>
                {type.label}
              </option>
            ))}
          </select>
        </div>

        {isLoading && missions.length === 0 ? (
          <div className="mission-empty-state">
            <RefreshCw size={26} className="mission-spin" />
            <strong>Loading mission records...</strong>
            <p>Connecting to the mission database.</p>
          </div>
        ) : filteredMissions.length === 0 ? (
          <div className="mission-empty-state">
            <div className="mission-empty-icon">
              {missions.length === 0 ? (
                <Orbit size={27} />
              ) : (
                <Search size={25} />
              )}
            </div>

            <strong>
              {missions.length === 0
                ? "No missions registered yet"
                : "No matching missions found"}
            </strong>

            <p>
              {missions.length === 0
                ? canManage
                  ? "Create your first mission to begin organizing mission records and crew assignments."
                  : "Mission records will appear here when they are created by Mission Control."
                : "Try changing your search query or filters."}
            </p>

            {missions.length === 0 && canManage && (
              <button
                type="button"
                className="mission-primary-button"
                onClick={handleCreate}
              >
                <Plus size={16} />
                Create first mission
              </button>
            )}
          </div>
        ) : (
          <div className="mission-card-grid">
            {filteredMissions.map((mission) => (
              <article className="mission-card" key={mission.id}>
                <div className="mission-card-top">
                  <div className="mission-card-symbol">
                    <Orbit size={19} />
                  </div>

                  <MissionStatus status={mission.status} />
                </div>

                <div className="mission-card-title">
                  <span>{mission.mission_code}</span>
                  <h3>{mission.mission_name}</h3>
                  <p>{formatLabel(mission.mission_type)}</p>
                </div>

                <div className="mission-card-meta">
                  <div>
                    <MapPin size={15} />
                    <span>{mission.destination || "Destination not specified"}</span>
                  </div>

                  <div>
                    <CalendarDays size={15} />
                    <span>
                      {formatDate(mission.planned_start_date)}
                    </span>
                  </div>

                  <div>
                    <Users size={15} />
                    <span>
                      {mission.crew?.length || 0} assigned crew members
                    </span>
                  </div>
                </div>

                <div className="mission-card-footer">
                  <button
                    type="button"
                    className="mission-view-button"
                    onClick={() => handleOpenDetails(mission)}
                    disabled={detailsLoadingId === mission.id}
                  >
                    {detailsLoadingId === mission.id ? (
                      <RefreshCw size={15} className="mission-spin" />
                    ) : (
                      <Eye size={15} />
                    )}
                    View details
                  </button>

                  {canManage && (
                    <div className="mission-card-actions">
                      <button
                        type="button"
                        onClick={() => handleEdit(mission)}
                        aria-label={`Edit ${mission.mission_name}`}
                      >
                        <Pencil size={15} />
                      </button>

                      <button
                        type="button"
                        className="mission-card-delete"
                        onClick={() => handleDelete(mission)}
                        disabled={isDeleting}
                        aria-label={`Delete ${mission.mission_name}`}
                      >
                        <Trash2 size={15} />
                      </button>
                    </div>
                  )}
                </div>
              </article>
            ))}
          </div>
        )}
      </section>

      <footer className="mission-page-footer">
        <Flag size={14} />
        <span>
          Mission data is managed through the authenticated ASTRA-PULSE API.
        </span>
      </footer>

      {showForm && canManage && (
        <MissionForm
          initialData={editingMission}
          astronauts={astronauts}
          isSaving={isSaving}
          error={mutationError}
          onClose={() => {
            setShowForm(false);
            setEditingMission(null);
            clearMutationError();
          }}
          onSubmit={handleFormSubmit}
        />
      )}

      {selectedMission && (
        <MissionDetails
          mission={selectedMission}
          canManage={canManage}
          onClose={clearSelectedMission}
          onEdit={handleEdit}
          onDelete={handleDelete}
        />
      )}
    </div>
  );
}

export default MissionsPage;
