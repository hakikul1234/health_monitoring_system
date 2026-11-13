import { motion } from "framer-motion";

function MetricCard({
  icon: Icon,
  label,
  value,
  unit,
  detail,
  status,
  color,
}) {
  return (
    <motion.article
      className="metric-card panel"
      whileHover={{ y: -3 }}
      transition={{ duration: 0.2 }}
    >
      <div className="metric-top">
        <div className={`metric-icon ${color}`}>
          <Icon size={19} />
        </div>

        <span className={`metric-status ${status}`}>
          <span />
          {status === "normal" ? "NOMINAL" : "DEMO"}
        </span>
      </div>

      <div className="metric-label">{label}</div>

      <div className="metric-value">
        {value}
        <span>{unit}</span>
      </div>

      <div className="metric-detail">{detail}</div>
    </motion.article>
  );
}

export default MetricCard;
