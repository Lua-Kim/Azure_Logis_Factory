import ModuleCard from "../common/ModuleCard.jsx";
import DataTable from "../common/DataTable.jsx";

const LineStatusTable = ({ items }) => (
  <ModuleCard title="LineStatusTable" description="Line status overview">
    <DataTable
      rows={items}
      columns={[
        { key: "line_id", label: "Line" },
        { key: "current_status", label: "Status" },
        { key: "active_bottlenecks", label: "Bottlenecks" },
        {
          key: "last_updated_at",
          label: "Last Updated",
          render: (row) =>
            row.last_updated_at
              ? new Date(row.last_updated_at).toLocaleString()
              : "-"
        }
      ]}
      emptyMessage="No line status available."
    />
  </ModuleCard>
);

export default LineStatusTable;
