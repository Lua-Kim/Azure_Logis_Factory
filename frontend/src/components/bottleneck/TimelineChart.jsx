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
import { aggregateEventsByHour } from "../../utils/aggregate.js";

const TimelineChart = ({ items = [] }) => {
  const data = aggregateEventsByHour(items).slice(-24);

  return (
    <ModuleCard title="TimelineChart" description="Time-based trend">
      {data.length ? (
        <div className="chart-panel">
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="timeLabel" />
              <YAxis allowDecimals={false} />
              <Tooltip />
              <Line type="monotone" dataKey="count" stroke="#16a34a" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      ) : (
        <p className="muted">No timeline data.</p>
      )}
    </ModuleCard>
  );
};

export default TimelineChart;
