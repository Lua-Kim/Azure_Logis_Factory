import ModuleCard from "../common/ModuleCard.jsx";
import DataTable from "../common/DataTable.jsx";

const EventTable = ({ items }) => (
  <ModuleCard title="EventTable" description="Recent events list">
    <DataTable
      rows={items}
      columns={[
        { key: "event_id", label: "Event" },
        { key: "event_type_code", label: "Type" },
        { key: "line_id", label: "Line" },
        { key: "section_id", label: "Section" },
        {
          key: "occurred_at",
          label: "Occurred",
          render: (row) =>
            row.occurred_at ? new Date(row.occurred_at).toLocaleString() : "-"
        }
      ]}
      emptyMessage="No events available."
    />
  </ModuleCard>
);

export default EventTable;
