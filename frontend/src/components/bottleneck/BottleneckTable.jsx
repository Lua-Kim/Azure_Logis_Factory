import ModuleCard from "../common/ModuleCard.jsx";
import DataTable from "../common/DataTable.jsx";

const BottleneckTable = ({ items }) => (
  <ModuleCard title="BottleneckTable" description="Bottleneck details">
    <DataTable
      rows={items}
      columns={[
        { key: "bottleneck_id", label: "ID" },
        { key: "line_id", label: "Line" },
        { key: "duration_sec", label: "Duration" },
        { key: "cause_code", label: "Cause" },
        {
          key: "occurred_at",
          label: "Occurred",
          render: (row) =>
            row.occurred_at ? new Date(row.occurred_at).toLocaleString() : "-"
        }
      ]}
      emptyMessage="No bottleneck records."
    />
  </ModuleCard>
);

export default BottleneckTable;
