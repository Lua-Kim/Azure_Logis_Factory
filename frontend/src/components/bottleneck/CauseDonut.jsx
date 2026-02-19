import ModuleCard from "../common/ModuleCard.jsx";
import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip, Legend } from "recharts";
import { aggregateBottleneckByCause } from "../../utils/aggregate.js";

const COLORS = ["#2563eb", "#f97316", "#16a34a", "#dc2626", "#9333ea"];

const CauseDonut = ({ items = [] }) => {
  const data = aggregateBottleneckByCause(items, 6);

  return (
    <ModuleCard title="CauseDonut" description="Cause distribution">
      {data.length ? (
        <div className="chart-panel">
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie data={data} dataKey="value" nameKey="name" innerRadius={50} outerRadius={80}>
                {data.map((entry, index) => (
                  <Cell key={entry.name} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>
      ) : (
        <p className="muted">No cause data.</p>
      )}
    </ModuleCard>
  );
};

export default CauseDonut;
