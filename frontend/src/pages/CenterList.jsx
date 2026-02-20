import { useMemo, useState } from "react";
import useAsync from "../hooks/useAsync.js";
import DataTable from "../components/common/DataTable.jsx";
import { getBottlenecks, getKpi } from "../services/metricsService.js";
import { listCenters } from "../services/settingsService.js";

const CenterList = () => {
  const [page, setPage] = useState(1);
  const [size, setSize] = useState(10);
  const [selectedCenterId, setSelectedCenterId] = useState(null);
  const [showGuide, setShowGuide] = useState(true);
  const { data, loading, error } = useAsync(
    () => listCenters({ page, size }),
    [page, size]
  );
  const kpiState = useAsync(
    () =>
      selectedCenterId
        ? getKpi("5m", 200, { center_id: selectedCenterId })
        : Promise.resolve([]),
    [selectedCenterId]
  );
  const bottleneckState = useAsync(
    () =>
      selectedCenterId
        ? getBottlenecks({ center_id: selectedCenterId, limit: 50 })
        : Promise.resolve([]),
    [selectedCenterId]
  );
  const items = data?.items || [];
  const total = data?.total || 0;
  const totalPages = Math.max(1, Math.ceil(total / size));
  const canPrev = page > 1;
  const canNext = page < totalPages;
  const selectedCenter = items.find(
    (center) => center.id === selectedCenterId
  );
  const centerKpi = useMemo(
    () => (kpiState.data || []),
    [kpiState.data]
  );
  const latestKpi = centerKpi[0];
  const throughputTotal = centerKpi.reduce(
    (sum, item) => sum + (item.throughput_count || 0),
    0
  );
  const bottlenecks = bottleneckState.data || [];
  const columns = useMemo(
    () => [
      { key: "id", label: "ID" },
      { key: "name", label: "Name" },
      { key: "location", label: "Location" },
      { key: "status", label: "Status" }
    ],
    []
  );

  return (
    <section className="page">
      <p>Center list with paging and search.</p>
      <div className="guide-toggle">
        <span className="muted">Guide</span>
        <button
          type="button"
          className="tab"
          onClick={() => setShowGuide((prev) => !prev)}
        >
          {showGuide ? "Hide guide" : "Show guide"}
        </button>
      </div>
      {showGuide ? (
        <div className="card guide-panel">
          <h2>이 페이지 보는 방법</h2>
          <div className="stat-block">
            <p className="muted">센터 목록에서 센터를 선택하면 아래 KPI가 갱신됩니다.</p>
            <p className="muted">페이지 크기를 조절해 더 많은 센터를 확인할 수 있습니다.</p>
          </div>
        </div>
      ) : null}
      <div className="card">
        <h2>Center List</h2>
        <div className="center-list__controls">
          <span className="muted">Select a center to view metrics below.</span>
          <select
            className="input center-list__size"
            value={size}
            onChange={(event) => {
              setSize(Number(event.target.value));
              setPage(1);
            }}
          >
            <option value={10}>10 per page</option>
            <option value={20}>20 per page</option>
            <option value={50}>50 per page</option>
          </select>
        </div>
        {loading ? (
          <p className="muted">Loading centers...</p>
        ) : error ? (
          <p className="error">Failed to load centers.</p>
        ) : (
          <DataTable
            rows={items}
            columns={columns}
            emptyMessage="No centers available."
            onRowClick={(row) => setSelectedCenterId(row.id)}
            getRowClassName={(row) =>
              row.id === selectedCenterId ? "is-selected" : ""
            }
          />
        )}
        <div className="pagination">
          <button
            className="button"
            type="button"
            onClick={() => setPage((prev) => Math.max(1, prev - 1))}
            disabled={!canPrev}
          >
            Prev
          </button>
          <span className="muted">
            Page {page} / {totalPages}
          </span>
          <button
            className="button"
            type="button"
            onClick={() => setPage((prev) => Math.min(totalPages, prev + 1))}
            disabled={!canNext}
          >
            Next
          </button>
        </div>
      </div>
      <div className="card">
        <h2>Selected Center Metrics</h2>
        {!selectedCenterId ? (
          <p className="muted">Select a center from the list to see metrics.</p>
        ) : kpiState.loading ? (
          <p className="muted">Loading KPI data...</p>
        ) : kpiState.error ? (
          <p className="error">Failed to load KPI data.</p>
        ) : (
          <div className="stat-block">
            <div>
              <span className="stat-label">Center</span>
              <span className="stat-value">
                {selectedCenter?.name || `ID ${selectedCenterId}`}
              </span>
            </div>
            <div>
              <span className="stat-label">Latest Window</span>
              <span className="stat-value">
                {latestKpi?.window_end
                  ? new Date(latestKpi.window_end).toLocaleString()
                  : "-"}
              </span>
            </div>
            <div>
              <span className="stat-label">Latest Throughput</span>
              <span className="stat-value">
                {latestKpi?.throughput_count ?? 0}
              </span>
            </div>
            <div>
              <span className="stat-label">Total Throughput (window)</span>
              <span className="stat-value">{throughputTotal}</span>
            </div>
            <div>
              <span className="stat-label">Recent Bottlenecks</span>
              <span className="stat-value">
                {bottleneckState.loading
                  ? "Loading..."
                  : bottlenecks.length}
              </span>
            </div>
          </div>
        )}
      </div>
    </section>
  );
};

export default CenterList;
