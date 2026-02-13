import ModuleCard from "../common/ModuleCard.jsx";
import {
  CartesianGrid,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";
import { aggregateKpiByLine } from "../../utils/aggregate.js";

const ThroughputScatter = ({ items = [] }) => {
  const data = aggregateKpiByLine(items).map((item) => ({
    line: item.line,
    throughput: item.throughput,
    count: item.count
  }));

  return (
    <ModuleCard title="ThroughputScatter" description="Throughput vs delay scatter">
      {data.length ? (
        <div className="chart-panel">
          <ResponsiveContainer width="100%" height={220}>
            <ScatterChart>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="line" name="Line" />
              <YAxis dataKey="throughput" name="Throughput" />
              <Tooltip cursor={{ strokeDasharray: "3 3" }} />
              <Scatter data={data} fill="#f97316" />
            </ScatterChart>
          </ResponsiveContainer>
        </div>
      ) : (
        <p className="muted">No scatter data.</p>
      )}
    </ModuleCard>
  );
};

export default ThroughputScatter;
