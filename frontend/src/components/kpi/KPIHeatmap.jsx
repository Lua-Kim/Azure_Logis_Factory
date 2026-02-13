import ModuleCard from "../common/ModuleCard.jsx";
import { aggregateKpiByLine } from "../../utils/aggregate.js";

const KPIHeatmap = ({ items = [] }) => {
  const aggregated = aggregateKpiByLine(items)
    .sort((a, b) => b.throughput - a.throughput)
    .slice(0, 12);
  const maxValue = aggregated.reduce(
    (max, item) => Math.max(max, item.throughput || 0),
    0
  );

  return (
    <ModuleCard title="KPIHeatmap" description="KPI attainment heatmap">
      {aggregated.length ? (
        <div className="heatmap-grid">
          {aggregated.map((item) => {
            const intensity = maxValue ? item.throughput / maxValue : 0;
            const background = `rgba(37, 99, 235, ${0.2 + intensity * 0.7})`;
            return (
              <div
                className="heatmap-cell"
                key={`line-${item.line}`}
                style={{ background }}
              >
                <span>Line {item.line}</span>
                <strong>{Math.round(item.throughput)}</strong>
              </div>
            );
          })}
        </div>
      ) : (
        <p className="muted">No heatmap data.</p>
      )}
    </ModuleCard>
  );
};

export default KPIHeatmap;
