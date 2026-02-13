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

const SLATrendChart = ({ items = [] }) => {
  const data = aggregateKpiSeries(items, 30);

  return (
    <ModuleCard title="SLATrendChart" description="SLA compliance trend">
      {data.length ? (
        <div className="chart-panel">
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="timeLabel" />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey="throughput" stroke="#2563eb" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      ) : (
        <p className="muted">No SLA trend data.</p>
      )}
    </ModuleCard>
  );
};

export default SLATrendChart;
