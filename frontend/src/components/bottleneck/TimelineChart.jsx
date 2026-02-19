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

  // 커스텀 Tooltip
  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div style={{ 
          backgroundColor: "rgba(0, 0, 0, 0.8)", 
          padding: "8px 12px", 
          borderRadius: "4px",
          color: "#fff"
        }}>
          <p style={{ margin: "0 0 4px 0", fontWeight: "bold" }}>{data.timeLabel}</p>
          <p style={{ margin: 0 }}>Events: {data.count}</p>
        </div>
      );
    }
    return null;
  };

  return (
    <ModuleCard 
      title="Bottleneck Timeline" 
      description="Bottleneck events over time (last 24 hours)"
    >
      {data.length ? (
        <div className="chart-panel">
          <ResponsiveContainer width="100%" height={280}>
            <LineChart 
              data={data}
              margin={{ top: 20, right: 30, left: 20, bottom: 60 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis 
                dataKey="timeLabel"
                angle={-45}
                textAnchor="end"
                height={80}
                tick={{ fontSize: 12 }}
              />
              <YAxis 
                label={{ value: "Event Count", angle: -90, position: "insideLeft" }}
                allowDecimals={false}
                tick={{ fontSize: 12 }}
              />
              <Tooltip content={<CustomTooltip />} />
              <Line 
                type="monotone" 
                dataKey="count" 
                stroke="#0ea5e9" 
                strokeWidth={2}
                dot={{ fill: '#0ea5e9', r: 4 }}
                activeDot={{ r: 6 }}
              />
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
