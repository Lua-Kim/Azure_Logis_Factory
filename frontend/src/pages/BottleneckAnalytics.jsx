import { useEffect, useMemo, useState } from "react";
import useAsync from "../hooks/useAsync.js";
import { useFilters } from "../context/FilterContext.jsx";
import { getBottlenecks, getLineStatus } from "../services/metricsService.js";
import usePolling from "../hooks/usePolling.js";
import useWebSocketSnapshot from "../hooks/useWebSocketSnapshot.js";
import BottleneckTable from "../components/bottleneck/BottleneckTable.jsx";
import CauseDonut from "../components/bottleneck/CauseDonut.jsx";
import DurationBar from "../components/bottleneck/DurationBar.jsx";
import TimelineChart from "../components/bottleneck/TimelineChart.jsx";

const BottleneckAnalytics = () => {
  const {
    centerId: globalCenterId,
    lineId: globalLineId,
    refreshMs,
    wsEnabled
  } = useFilters();
  const [centerId, setCenterId] = useState(globalCenterId);
  const [lineId, setLineId] = useState(globalLineId);
  const [limit, setLimit] = useState(20);
  const [lineList, setLineList] = useState([]);
  const [centerList, setCenterList] = useState([]);

  // Load line status to get center and line options
  const { data: lineStatusData } = useAsync(getLineStatus, []);

  useEffect(() => {
    if (lineStatusData && Array.isArray(lineStatusData)) {
      setLineList(lineStatusData);
      const uniqueCenters = [...new Set(lineStatusData.map(l => l.center_id))];
      setCenterList(uniqueCenters);
    }
  }, [lineStatusData]);

  const { data, loading, error, run } = useAsync(
    () => {
      const params = { limit };
      if (centerId && centerId !== "") params.center_id = Number(centerId);
      if (lineId && lineId !== "") params.line_id = Number(lineId);
      console.log("🔍 Fetching bottlenecks with params:", params);
      return getBottlenecks(params);
    },
    [centerId, lineId, limit]
  );

  const { snapshot } = useWebSocketSnapshot(wsEnabled, {
    center_id: centerId || undefined,
    line_id: lineId || undefined
  });

  usePolling(run, wsEnabled ? 0 : refreshMs);

  const items = useMemo(() => {
    if (wsEnabled && snapshot?.bottlenecks) {
      return snapshot.bottlenecks;
    }
    return data || [];
  }, [data, snapshot, wsEnabled]);

  useEffect(() => {
    setCenterId(globalCenterId);
  }, [globalCenterId]);

  useEffect(() => {
    setLineId(globalLineId);
  }, [globalLineId]);

  // Filter lines by center (show all if no center selected)
  const filteredLines = centerId 
    ? lineList.filter(l => l.center_id === Number(centerId)) 
    : lineList;

  // Get line IDs that have bottleneck data
  const lineIdsWithBottlenecks = new Set(items.map(item => item.line_id));

  useEffect(() => {
    console.log("📊 State update:", { centerId, lineId, count: items.length, loading, error });
  }, [centerId, lineId, items, loading, error]);

  return (
    <section className="page">
      {/* Filters */}
      <div className="card">
        <h2>Filters</h2>
        <div className="form-grid">
          <label>
            Center ID
            <select
              className="input"
              value={centerId}
              onChange={(event) => {
                setCenterId(event.target.value);
                setLineId(""); // Reset line ID when center changes
              }}
            >
              <option value="">All Centers</option>
              {centerList.map(cid => (
                <option key={cid} value={cid}>{cid}</option>
              ))}
            </select>
          </label>
          <label>
            Line ID
            <select
              className="input"
              value={String(lineId)}
              onChange={(event) => setLineId(event.target.value)}
            >
              <option value="">All Lines</option>
              {filteredLines.map(line => (
                <option key={line.id} value={String(line.id)}>
                  {lineIdsWithBottlenecks.has(line.id) ? '✅' : '○'} {line.name} ({line.id})
                </option>
              ))}
            </select>
          </label>
          <label>
            Limit
            <input
              className="input"
              type="number"
              value={limit}
              onChange={(event) => setLimit(Number(event.target.value) || 20)}
              placeholder="Limit"
            />
          </label>
        </div>
      </div>

      {/* Charts Row: CauseDonut, DurationBar, TimelineChart */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "1rem", marginBottom: "1rem" }}>
        <div className="module-card">
          <CauseDonut items={items} />
        </div>
        <div className="module-card">
          <DurationBar items={items} />
        </div>
        <div className="module-card">
          <TimelineChart items={items} />
        </div>
      </div>

      {/* Table Row: BottleneckTable */}
      <div className="module-card" style={{ marginBottom: "1rem" }}>
        <BottleneckTable items={items} />
      </div>

      {/* Recent Bottlenecks */}
      <div className="card">
        <h2>Recent Bottlenecks</h2>
        {loading ? (
          <p className="muted">Loading bottlenecks...</p>
        ) : error ? (
          <p className="error">Failed to load bottlenecks.</p>
        ) : items.length ? (
          <ul className="placeholder-list">
            {items.map((item) => (
              <li key={item.id}>
                <strong>#{item.id}</strong> | Line {item.line_id} | {item.duration_sec}s | {item.cause_code} | {new Date(item.occurred_at).toLocaleString()}
              </li>
            ))}
          </ul>
        ) : (
          <p className="muted">No bottleneck data.</p>
        )}
      </div>
    </section>
  );
};

export default BottleneckAnalytics;
