import { Activity } from "lucide-react";

import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

function TelemetryChart({ data = [] }) {
  return (
    <section className="panel chart-panel">
      <div className="section-heading">
        <div>
          <div className="section-title">Biometric Telemetry</div>
          <div className="section-subtitle">
            Latest valid synthetic readings · Up to 10 samples
          </div>
        </div>

        <div className="chart-legend">
          <span><i className="legend-blue" /> Heart rate</span>
          <span><i className="legend-violet" /> SpO₂</span>
        </div>
      </div>

      <div className="chart-container">
        {data.length > 0 ? (
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart
              data={data}
              margin={{ top: 12, right: 8, left: -20, bottom: 0 }}
            >
              <defs>
                <linearGradient id="heartGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#3B82F6" stopOpacity={0.28} />
                  <stop offset="100%" stopColor="#3B82F6" stopOpacity={0} />
                </linearGradient>

                <linearGradient id="oxygenGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#A78BFA" stopOpacity={0.2} />
                  <stop offset="100%" stopColor="#A78BFA" stopOpacity={0} />
                </linearGradient>
              </defs>

              <CartesianGrid
                stroke="rgba(148,163,184,0.12)"
                strokeDasharray="4 5"
                vertical={false}
              />

              <XAxis
                dataKey="time"
                stroke="#64748B"
                tickLine={false}
                axisLine={false}
                tick={{ fontSize: 11 }}
              />

              <YAxis
                stroke="#64748B"
                tickLine={false}
                axisLine={false}
                tick={{ fontSize: 11 }}
              />

              <Tooltip
                contentStyle={{
                  background: "#111D35",
                  border: "1px solid rgba(148,163,184,.2)",
                  borderRadius: "12px",
                  color: "#EAF2FF",
                }}
              />

              <Area
                type="monotone"
                dataKey="heartRate"
                stroke="#60A5FA"
                strokeWidth={2.5}
                fill="url(#heartGradient)"
                name="Heart rate (bpm)"
                connectNulls={false}
              />

              <Area
                type="monotone"
                dataKey="oxygen"
                stroke="#A78BFA"
                strokeWidth={2}
                fill="url(#oxygenGradient)"
                name="SpO₂ (%)"
                connectNulls={false}
              />
            </AreaChart>
          </ResponsiveContainer>
        ) : (
          <div className="dashboard-state">
            <Activity size={25} />
            <strong>No valid telemetry available</strong>
            <span>Generate synthetic readings using the simulator.</span>
          </div>
        )}
      </div>

      <div className="chart-footer">
        <span><Activity size={14} /> TELEMETRY STREAM: SIMULATED</span>
        <span>Valid samples only</span>
      </div>
    </section>
  );
}

export default TelemetryChart;
