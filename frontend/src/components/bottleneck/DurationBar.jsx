import ModuleCard from "../common/ModuleCard.jsx";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";
import { aggregateBottleneckDurationByLine } from "../../utils/aggregate.js";

const DurationBar = ({ items = [] }) => {
  const data = aggregateBottleneckDurationByLine(items, 8);

  return (
    <ModuleCard title="DurationBar" description="Bottleneck duration bars">
      {data.length ? (
        <div className="chart-panel">
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="line" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="duration" fill="#f97316" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      ) : (
        <p className="muted">No duration data.</p>
      )}
    </ModuleCard>
  );
};

export default DurationBar;
