export const telemetryData = [
  { time: "08:00", heartRate: 68, oxygen: 98 },
  { time: "09:00", heartRate: 72, oxygen: 98 },
  { time: "10:00", heartRate: 70, oxygen: 97 },
  { time: "11:00", heartRate: 76, oxygen: 98 },
  { time: "12:00", heartRate: 74, oxygen: 97 },
  { time: "13:00", heartRate: 82, oxygen: 98 },
  { time: "14:00", heartRate: 77, oxygen: 99 },
  { time: "15:00", heartRate: 73, oxygen: 98 },
];

export const alerts = [
  {
    id: 1,
    level: "warning",
    title: "Heart rate deviation",
    description: "Elevated heart rate in synthetic demo stream",
    time: "12 min ago",
    code: "HR-DEV-01",
  },
  {
    id: 2,
    level: "critical",
    title: "Oxygen level anomaly",
    description: "Low simulated SpO2 value detected",
    time: "24 min ago",
    code: "SPO2-AN-02",
  },
  {
    id: 3,
    level: "info",
    title: "Data quality review",
    description: "One synthetic sample requires review",
    time: "38 min ago",
    code: "DQ-REV-03",
  },
];

export const crew = [
  {
    name: "Commander Alex",
    role: "Mission Commander",
    initials: "AC",
    status: "Nominal",
    color: "blue",
  },
  {
    name: "Dr. Sarah Chen",
    role: "Medical Officer",
    initials: "SC",
    status: "Nominal",
    color: "violet",
  },
  {
    name: "Pilot James",
    role: "Flight Engineer",
    initials: "JP",
    status: "Review",
    color: "cyan",
  },
];
