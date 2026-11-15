import { useState } from "react";
import { Canvas } from "@react-three/fiber";
import { Html, OrbitControls } from "@react-three/drei";
import { Activity, RotateCcw } from "lucide-react";
import "./VirtualSensorBody.css";

const LOCATIONS = [
  {
    id: "chest",
    label: "Chest / ECG",
    short: "CHEST",
    side: "FRONT",
    position: [0, 1.48, 0.37],
    purpose: "Illustrative chest-mounted cardiac sensor position.",
  },
  {
    id: "left-wrist",
    label: "Left Wrist",
    short: "L-WRIST",
    side: "FRONT",
    position: [-0.91, 0.65, 0.17],
    purpose: "Illustrative wrist wearable position.",
  },
  {
    id: "right-wrist",
    label: "Right Wrist",
    short: "R-WRIST",
    side: "FRONT",
    position: [0.91, 0.65, 0.17],
    purpose: "Illustrative wrist wearable position.",
  },
  {
    id: "upper-arm",
    label: "Upper Arm",
    short: "ARM",
    side: "FRONT",
    position: [-0.68, 1.31, 0.17],
    purpose: "Illustrative upper-arm sensor position.",
  },
  {
    id: "waist",
    label: "Waist / IMU",
    short: "WAIST",
    side: "FRONT",
    position: [0, 0.83, 0.32],
    purpose: "Illustrative motion and activity sensor position.",
  },
  {
    id: "upper-back",
    label: "Upper Back",
    short: "BACK",
    side: "BACK",
    position: [0, 1.48, -0.36],
    purpose: "Illustrative upper-back sensor position.",
  },
  {
    id: "lower-back",
    label: "Lower Back",
    short: "L-BACK",
    side: "BACK",
    position: [0, 0.94, -0.32],
    purpose: "Illustrative lower-back sensor position.",
  },
];

function Capsule({ position, args, rotation = [0, 0, 0], color = "#b9c9dc" }) {
  return (
    <mesh position={position} rotation={rotation} castShadow>
      <capsuleGeometry args={args} />
      <meshStandardMaterial
        color={color}
        roughness={0.58}
        metalness={0.22}
      />
    </mesh>
  );
}

function AstronautMannequin() {
  return (
    <group>
      {/* Helmet and visor */}
      <mesh position={[0, 2.18, 0]} castShadow>
        <sphereGeometry args={[0.245, 32, 32]} />
        <meshStandardMaterial
          color="#d9e7f5"
          metalness={0.42}
          roughness={0.3}
        />
      </mesh>

      <mesh position={[0, 2.19, 0.205]}>
        <sphereGeometry args={[0.155, 28, 20]} />
        <meshStandardMaterial
          color="#17446a"
          metalness={0.72}
          roughness={0.2}
          transparent
          opacity={0.92}
        />
      </mesh>

      <Capsule position={[0, 1.89, 0]} args={[0.105, 0.13, 5, 12]} color="#8199b5" />

      {/* Torso */}
      <Capsule position={[0, 1.34, 0]} args={[0.35, 0.63, 8, 16]} color="#d5e1ef" />
      <Capsule position={[0, 0.84, 0]} args={[0.29, 0.18, 6, 14]} color="#a8bbd2" />

      {/* Chest control panel */}
      <mesh position={[0, 1.48, 0.315]}>
        <boxGeometry args={[0.25, 0.19, 0.045]} />
        <meshStandardMaterial color="#274a6a" metalness={0.45} />
      </mesh>

      {/* Arms */}
      <Capsule position={[-0.49, 1.43, 0]} args={[0.135, 0.43, 6, 12]} rotation={[0, 0, -0.19]} />
      <Capsule position={[0.49, 1.43, 0]} args={[0.135, 0.43, 6, 12]} rotation={[0, 0, 0.19]} />

      <Capsule position={[-0.72, 0.91, 0]} args={[0.105, 0.39, 6, 12]} rotation={[0, 0, -0.08]} color="#b8c9dd" />
      <Capsule position={[0.72, 0.91, 0]} args={[0.105, 0.39, 6, 12]} rotation={[0, 0, 0.08]} color="#b8c9dd" />

      <mesh position={[-0.83, 0.63, 0]}>
        <sphereGeometry args={[0.105, 18, 18]} />
        <meshStandardMaterial color="#9eb2c9" />
      </mesh>
      <mesh position={[0.83, 0.63, 0]}>
        <sphereGeometry args={[0.105, 18, 18]} />
        <meshStandardMaterial color="#9eb2c9" />
      </mesh>

      {/* Legs */}
      <Capsule position={[-0.2, 0.35, 0]} args={[0.15, 0.48, 6, 12]} color="#c4d2e2" />
      <Capsule position={[0.2, 0.35, 0]} args={[0.15, 0.48, 6, 12]} color="#c4d2e2" />

      <Capsule position={[-0.2, -0.25, 0]} args={[0.125, 0.45, 6, 12]} color="#aabed4" />
      <Capsule position={[0.2, -0.25, 0]} args={[0.125, 0.45, 6, 12]} color="#aabed4" />

      <mesh position={[-0.2, -0.57, 0.055]} castShadow>
        <boxGeometry args={[0.29, 0.18, 0.38]} />
        <meshStandardMaterial color="#627e9e" roughness={0.65} />
      </mesh>
      <mesh position={[0.2, -0.57, 0.055]} castShadow>
        <boxGeometry args={[0.29, 0.18, 0.38]} />
        <meshStandardMaterial color="#627e9e" roughness={0.65} />
      </mesh>
    </group>
  );
}

function SensorMarker({ location, active, status, onSelect }) {
  const statusClass = active
    ? String(status || "ACTIVE").toLowerCase()
    : "available";

  return (
    <group position={location.position}>
      <mesh>
        <sphereGeometry args={[active ? 0.075 : 0.055, 20, 20]} />
        <meshStandardMaterial
          color={active ? "#38d9f5" : "#6c9fc5"}
          emissive={active ? "#087baf" : "#173e5e"}
          emissiveIntensity={active ? 1.8 : 0.7}
        />
      </mesh>

      <mesh>
        <torusGeometry args={[0.105, 0.009, 8, 28]} />
        <meshBasicMaterial color={active ? "#66e6ff" : "#5488ae"} />
      </mesh>

      <Html position={[0, 0.15, 0]} center distanceFactor={8}>
        <button
          type="button"
          className={`vs-body-marker ${active ? "is-selected" : ""} vs-marker-${statusClass}`}
          onPointerDown={(event) => event.stopPropagation()}
          onClick={(event) => {
            event.stopPropagation();
            onSelect(location.id);
          }}
          title={`Select ${location.label}`}
        >
          <span className="vs-body-marker-dot" />
          {location.short}
        </button>
      </Html>
    </group>
  );
}

export default function VirtualSensorBody({ selectedSensor }) {
  const [view, setView] = useState("FRONT");
  const [selectedPosition, setSelectedPosition] = useState("chest");

  const visibleLocations = LOCATIONS.filter(
    (location) => location.side === view
  );

  const activeLocation = LOCATIONS.find(
    (location) => location.id === selectedPosition
  );

  const status = selectedSensor?.status || "UNASSIGNED";

  return (
    <section className="vs-body-card">
      <div className="vs-body-header">
        <div>
          <span className="vs-body-eyebrow">VIRTUAL WEARABLE MAPPING</span>
          <h3>3D Astronaut Sensor Placement</h3>
          <p>Select a body marker to preview a sensor position.</p>
        </div>

        <div className="vs-body-view-switch" aria-label="Astronaut body view">
          <button
            type="button"
            className={view === "FRONT" ? "active" : ""}
            onClick={() => setView("FRONT")}
          >
            Front
          </button>
          <button
            type="button"
            className={view === "BACK" ? "active" : ""}
            onClick={() => setView("BACK")}
          >
            Back
          </button>
        </div>
      </div>

      <div className="vs-body-stage">
        <Canvas
          shadows
          dpr={[1, 1.5]}
          camera={{ position: [0, 1.15, 5.7], fov: 38 }}
        >
          <color attach="background" args={["#0b1728"]} />
          <ambientLight intensity={1.25} />
          <directionalLight
            position={[3, 5, 5]}
            intensity={2.2}
            castShadow
          />
          <pointLight position={[-3, 1, -2]} intensity={1.2} color="#278acb" />

          <group rotation={[0, view === "BACK" ? Math.PI : 0, 0]}>
            <AstronautMannequin />

            {visibleLocations.map((location) => (
              <SensorMarker
                key={location.id}
                location={location}
                active={location.id === selectedPosition}
                status={status}
                onSelect={setSelectedPosition}
              />
            ))}
          </group>

          <OrbitControls
            enablePan={false}
            minDistance={4.2}
            maxDistance={7}
            minPolarAngle={Math.PI / 3}
            maxPolarAngle={Math.PI / 1.7}
          />
        </Canvas>

        <div className="vs-body-canvas-hint">
          <RotateCcw size={13} />
          Drag to rotate ? Scroll to zoom
        </div>
      </div>

      <div className="vs-body-detail">
        <div className="vs-body-detail-icon">
          <Activity size={19} />
        </div>

        <div className="vs-body-detail-copy">
          <span>SELECTED BODY POSITION</span>
          <strong>{activeLocation?.label || "Chest / ECG"}</strong>
          <small>{activeLocation?.purpose}</small>
        </div>

        <div className="vs-body-sensor-status">
          <span>SELECTED SENSOR</span>
          <strong>{selectedSensor?.sensor_code || "No sensor selected"}</strong>
          <small>{selectedSensor ? status : "Select from registry"}</small>
        </div>
      </div>

      <p className="vs-body-disclaimer">
        Position markers are illustrative UI previews only. Sensor placement
        is not saved to the backend and does not represent a validated
        medical-device configuration.
      </p>
    </section>
  );
}
