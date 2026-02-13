const DataTable = ({
  columns,
  rows,
  emptyMessage = "No data available.",
  onRowClick,
  getRowClassName
}) => {
  if (!rows || rows.length === 0) {
    return <p className="muted">{emptyMessage}</p>;
  }

  return (
    <div className="data-table__wrapper">
      <table className="data-table">
        <thead>
          <tr>
            {columns.map((column) => (
              <th key={column.key}>{column.label}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, index) => {
            const rowKey = row.id || row.key || index;
            const rowClass = getRowClassName ? getRowClassName(row, index) : "";
            const clickableClass = onRowClick ? "is-clickable" : "";
            return (
              <tr
                key={rowKey}
                className={`${rowClass} ${clickableClass}`.trim()}
                onClick={onRowClick ? () => onRowClick(row, index) : undefined}
              >
              {columns.map((column) => (
                <td key={column.key}>
                  {column.render ? column.render(row) : row[column.key]}
                </td>
              ))}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
};

export default DataTable;
