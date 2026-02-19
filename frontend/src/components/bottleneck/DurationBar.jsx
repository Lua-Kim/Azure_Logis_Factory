import ModuleCard from "../common/ModuleCard.jsx";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  Cell,
  Label
} from "recharts";
import { aggregateBottleneckDurationByLine } from "../../utils/aggregate.js";

const DurationBar = ({ items = [] }) => {
  const data = aggregateBottleneckDurationByLine(items, 8);

  // 색상 팔레트: 지속시간이 길수록 진한 색
  const COLORS = ["#3b82f6", "#0ea5e9", "#06b6d4", "#14b8a6", "#10b981", "#f97316", "#ef4444", "#dc2626"];

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
          <p style={{ margin: "0 0 4px 0", fontWeight: "bold" }}>{data.line}</p>
          <p style={{ margin: 0 }}>{data.duration}초</p>
        </div>
      );
    }
    return null;
  };

  return (
    <ModuleCard 
      title="Bottleneck Duration by Line" 
      description="Average bottleneck duration per line in seconds"
    >
      {data.length ? (
        <div className="chart-panel" style={{ width: "100%" }}>
          <ResponsiveContainer width="100%" height={420}>
            <BarChart 
              data={data}
              margin={{ top: 50, right: 30, left: 20, bottom: 100 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis 
                dataKey="line"
                angle={-45}
                textAnchor="end"
                height={80}
                tick={{ fontSize: 12 }}
              />
              <YAxis 
                label={{ value: "Duration (seconds)", angle: -90, position: "insideLeft" }}
                tick={{ fontSize: 12 }}
              />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="duration" radius={[8, 8, 0, 0]}>
                {data.map((entry, index) => (
                  <Cell 
                    key={`cell-${index}`} 
                    fill={COLORS[index % COLORS.length]}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      ) : (
        <p className="muted">데이터가 없습니다.</p>
      )}
    </ModuleCard>
  );
};

export default DurationBar;
