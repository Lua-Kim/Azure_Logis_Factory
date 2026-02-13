import ModuleCard from "../common/ModuleCard.jsx";
import DataTable from "../common/DataTable.jsx";

const KPITable = ({ items }) => (
  <ModuleCard title="KPITable" description="KPI summary table">
    <DataTable
      rows={items}
      columns={[
        {
          key: "window_end",
          label: "Window End",
          render: (row) =>
            row.window_end ? new Date(row.window_end).toLocaleString() : "-"
        },
        { key: "center_id", label: "Center" },
        { key: "line_id", label: "Line" },
        { key: "throughput_count", label: "Throughput" }
      ]}
      emptyMessage="No KPI data."
    />
  </ModuleCard>
);

export default KPITable;
