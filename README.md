# ASTRA-PULSE AI
### Trust-Aware Astronaut Health Intelligence & Mission Resilience Platform

ASTRA-PULSE AI is a software prototype designed to support astronaut health monitoring through health-data analysis, anomaly detection, virtual sensor simulation, and trust-aware decision support.

The platform helps evaluate whether available health readings are reliable enough to support a decision and provides explainable outcomes through a Mission Control dashboard.

---

## 1. Project Overview

ASTRA-PULSE AI focuses on five major workflow stages:

1. **Health Data Input** – Receives astronaut health parameters or synthetic sensor readings.
2. **Data Processing** – Processes and validates incoming health data.
3. **AI Analysis** – Detects unusual health-related patterns.
4. **Trust-Aware Decision Engine** – Evaluates sensor reliability and generates decisions.
5. **Mission Control Dashboard** – Displays health insights, alerts, and decision explanations.

## 2. Key Features

- Astronaut health monitoring dashboard.
- Heart rate, SpO₂, temperature, and respiratory-rate monitoring.
- Astronaut-specific health baseline.
- Rule-based anomaly detection.
- Virtual health sensor simulation.
- Sensor fault simulation:
  - NORMAL
  - NOISE
  - DRIFT
  - DROPOUT
  - DISCONNECTED
- Trust-Aware Decision Engine.
- Mission and crew management.
- Health alerts and insights.
- 3D astronaut sensor-placement visualization.
- Role-Based Access Control (RBAC).

## 3. Trust-Aware Decision Engine

The decision engine provides four possible outcomes:

| Decision | Description |
|---|---|
| ACCEPT | Reading passes configured software checks. |
| REMEASURE | A repeat measurement is recommended. |
| CROSS_CHECK | Independent sensor evidence is available. |
| ABSTAIN | Available evidence is insufficient or unreliable. |

**Note:** CROSS_CHECK currently identifies independent evidence availability. It does not perform numerical comparison between sensor readings.

## 4. Technology Stack

### Frontend
- React
- Vite
- JavaScript
- Zustand
- CSS

### Backend
- Python
- Django
- Django REST Framework
- SQLite (development database)

### Other Components
- REST API integration
- Authentication and authorization
- Virtual sensor simulation
- Data analysis and visualization

## 5. Project Structure

```text
ASTRA-PULSE-AI/
│
├── backend/
│   ├── manage.py
│   ├── astra_accounts/
│   ├── astra_crew/
│   ├── astra_health/
│   ├── astra_simulator/
│   └── ...
│
├── frontend/
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── vite.config.js
│
└── README.md
```

## 6. System Requirements

- Windows 10/11, Linux, or macOS
- Python 3.12
- Node.js and npm
- Modern web browser
- Minimum 8 GB RAM recommended

## 7. How to Run the Project

### Step 1: Download or Extract the Project

Extract the ASTRA-PULSE AI project folder to your computer.

Open PowerShell or the terminal inside the project directory.

### Step 2: Start the Backend

Navigate to the backend directory:

```powershell
cd backend
```

Activate your Python virtual environment if it already exists:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install dependencies if required:

```powershell
pip install -r requirements.txt
```

Run database migrations:

```powershell
python manage.py migrate
```

Start the Django development server:

```powershell
python manage.py runserver
```

Backend address:

http://127.0.0.1:8000/

### Step 3: Start the Frontend

Open a second terminal window.

Navigate to the frontend directory:

```powershell
cd frontend
```

Install frontend dependencies:

```powershell
npm install
```

Start the frontend:

```powershell
npm run dev
```

Frontend address:

http://localhost:5173/

### Step 4: Open the Application

Open your browser and visit:

http://localhost:5173/

Log in using the Mission Control demo account below.

## 8. Demo Login Credentials

### Mission Control Demo Account

| Field | Credentials |
|---|---|
| Username | `astra_mission_control_demo` |
| Password | `Hak@123456789` |
| Role | MISSION_CONTROL |
| Badge ID | MC-DEMO-001 |

**Important:** These are local demonstration credentials. The demo account must already exist in the backend database. Do not use this password for a production account or commit real credentials to a public repository.

## 9. Demonstration Workflow

For a project demonstration:

1. Start the backend and frontend servers.
2. Open the application in your browser.
3. Log in using the Mission Control demo account.
4. Explore the Mission Control dashboard.
5. Open the Virtual Sensor Simulator.
6. Select an astronaut and an available virtual sensor.
7. Generate a normal synthetic health reading.
8. Review the generated sensor data.
9. Run the Trust-Aware Decision Engine.
10. Review the decision, evidence, and recommended action.
11. Try a sensor fault scenario such as NOISE or DRIFT.

## 10. Important API Endpoint

Trust decision endpoint:

```text
POST /api/simulator/trust-decisions/
```

Example request:

```json
{
  "reading_id": 1
}
```

The endpoint requires authentication and appropriate simulator-control permissions.

## 11. Testing

Backend test command:

```powershell
python manage.py test
```

Frontend production build:

```powershell
npm run build
```

## 12. Current Limitations

- The current prototype uses synthetic health telemetry.
- Physical wearable-device integration is not implemented.
- The anomaly detection system uses configured rules and thresholds.
- No validated astronaut medical dataset is currently used to establish clinical accuracy.
- The platform is not medically certified or flight-certified.
- It is a decision-support prototype, not a medical diagnostic system.

## 13. Future Scope

- Integration with physical wearable health sensors.
- Real-time astronaut health telemetry.
- Advanced machine-learning-based anomaly analysis.
- Numerical comparison of independent sensor readings.
- Improved predictive health analytics.
- Enhanced mission resilience and decision support.
- Further security, performance, and system validation.

## 14. Project Objective

The objective of ASTRA-PULSE AI is to move beyond basic astronaut health monitoring by introducing a trust-aware software intelligence layer that evaluates unusual health patterns, assesses sensor-data reliability, and provides explainable decision support to Mission Control.

---

**ASTRA-PULSE AI**

*Beyond Health Monitoring — Towards Trustworthy Space Health Intelligence.*

