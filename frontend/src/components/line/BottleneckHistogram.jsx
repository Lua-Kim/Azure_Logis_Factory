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

const BottleneckHistogram = ({ items = [] }) => {
  const data = items.map((item) => ({
    bucket: item.bucket ? new Date(item.bucket).toLocaleTimeString() : "-",
    events: item.event_count || 0
  }));

  return (
    <ModuleCard title="BottleneckHistogram" description="Event distribution">
      {data.length ? (
        <div className="chart-panel">
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="bucket" />
              <YAxis allowDecimals={false} />
              <Tooltip />
              <Bar dataKey="events" fill="#9333ea" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      ) : (
        <p className="muted">No histogram data.</p>
      )}
    </ModuleCard>
  );
};

export default BottleneckHistogram;
