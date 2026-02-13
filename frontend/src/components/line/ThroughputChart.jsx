import ModuleCard from "../common/ModuleCard.jsx";
import DataTable from "../common/DataTable.jsx";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";

const ThroughputChart = ({ items }) => {
  const chartData = (items || []).map((item) => ({
    bucket: item.bucket ? new Date(item.bucket).toLocaleTimeString() : "-",
    events: item.event_count || 0
  }));

  return (
    <ModuleCard title="ThroughputChart" description="Throughput trend">
      {chartData.length ? (
        <div className="chart-panel">
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="bucket" />
              <YAxis allowDecimals={false} />
              <Tooltip />
              <Line type="monotone" dataKey="events" stroke="#2563eb" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      ) : (
        <p className="muted">No throughput data.</p>
      )}
      <DataTable
        rows={items}
        columns={[
          {
            key: "bucket",
            label: "Bucket",
            render: (row) =>
              row.bucket ? new Date(row.bucket).toLocaleString() : "-"
          },
          { key: "event_count", label: "Events" },
          { key: "arrival_count", label: "Arrivals" },
          { key: "departure_count", label: "Departures" }
        ]}
        emptyMessage="No throughput data."
      />
    </ModuleCard>
  );
};

export default ThroughputChart;
