import ModuleCard from "../common/ModuleCard.jsx";
import DataTable from "../common/DataTable.jsx";

const CenterSummaryTable = ({ items }) => (
  <ModuleCard title="CenterSummaryTable" description="Center-level summary table">
    <DataTable
      rows={items}
      columns={[
        { key: "center_id", label: "Center" },
        { key: "throughput_total", label: "Throughput" },
        {
          key: "last_window_end",
          label: "Last Window",
          render: (row) =>
            row.last_window_end
              ? new Date(row.last_window_end).toLocaleString()
              : "-"
        }
      ]}
      emptyMessage="No center summary available."
    />
  </ModuleCard>
);

export default CenterSummaryTable;
