import {
  Activity,
  Gauge,
  Thermometer,
  Wind,
  Zap,
} from "lucide-react";

function EnvironmentPanel() {
  const environment = [
    { label: "Cabin temperature", value: "22.4", unit: "°C", icon: Thermometer },
    { label: "Cabin CO₂", value: "0.08", unit: "%", icon: Wind },
    { label: "Relative humidity", value: "45", unit: "%", icon: Activity },
    { label: "Radiation index", value: "0.12", unit: "mSv", icon: Zap },
  ];

  return (
    <section className="panel environment-panel">
      <div className="section-heading">
        <div>
          <div className="section-title">Cabin Environment</div>
          <div className="section-subtitle">
            Virtual environment · Synthetic values
          </div>
        </div>

        <Gauge size={19} className="heading-icon" />
      </div>

      <div className="environment-grid">
        {environment.map((item) => {
          const Icon = item.icon;

          return (
            <div className="environment-item" key={item.label}>
              <div className="environment-icon">
                <Icon size={16} />
              </div>

              <span>{item.label}</span>

              <strong>
                {item.value}<small> {item.unit}</small>
              </strong>
            </div>
          );
        })}
      </div>
    </section>
  );
}

export default EnvironmentPanel;
