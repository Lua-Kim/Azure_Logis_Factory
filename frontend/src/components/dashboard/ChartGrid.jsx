import ModuleCard from "../common/ModuleCard.jsx";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";
import { aggregateKpiSeries } from "../../utils/aggregate.js";

const ChartGrid = ({ kpiItems = [] }) => {
  const seriesData = aggregateKpiSeries(kpiItems, 24);

  return (
    <ModuleCard title="ChartGrid" description="Multi-chart visualization grid">
      {seriesData.length ? (
        <div className="chart-panel">
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={seriesData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="timeLabel" />
              <YAxis />
              <Tooltip />
              <Line
                type="monotone"
                dataKey="throughput"
                stroke="#2563eb"
                strokeWidth={2}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      ) : (
        <p className="muted">No KPI data for chart.</p>
      )}
    </ModuleCard>
  );
};

export default ChartGrid;
