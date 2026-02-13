import ModuleCard from "../common/ModuleCard.jsx";

const KPIHeader = ({ subtitle, stats = [] }) => (
  <ModuleCard title="KPIHeader" description={subtitle || "Top-level KPI summary"}>
    {stats.length ? (
      <div className="kpi-grid">
        {stats.map((stat) => (
          <div className="kpi-card" key={stat.label}>
            <span className="stat-label">{stat.label}</span>
            <span className="stat-value">{stat.value}</span>
          </div>
        ))}
      </div>
    ) : (
      <p className="muted">KPI cards will render here.</p>
    )}
  </ModuleCard>
);

export default KPIHeader;
