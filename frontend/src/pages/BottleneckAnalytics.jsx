import { useEffect, useMemo, useState } from "react";
import useAsync from "../hooks/useAsync.js";
import { useFilters } from "../context/FilterContext.jsx";
import { getBottlenecks } from "../services/metricsService.js";
import usePolling from "../hooks/usePolling.js";
import useWebSocketSnapshot from "../hooks/useWebSocketSnapshot.js";
import BottleneckTable from "../components/bottleneck/BottleneckTable.jsx";
import CauseDonut from "../components/bottleneck/CauseDonut.jsx";
import DurationBar from "../components/bottleneck/DurationBar.jsx";
import ErrorTable from "../components/bottleneck/ErrorTable.jsx";
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

  const { data, loading, error, run } = useAsync(
    () =>
      getBottlenecks({
        center_id: centerId ? Number(centerId) : undefined,
        line_id: lineId ? Number(lineId) : undefined,
        limit
      }),
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

  return (
    <section className="page">
      <p>Bottleneck and anomaly analysis placeholder.</p>
      <div className="card">
        <h2>Filters</h2>
        <div className="form-grid">
          <input
            className="input"
            value={centerId}
            onChange={(event) => setCenterId(event.target.value)}
            placeholder="Center ID"
          />
          <input
            className="input"
            value={lineId}
            onChange={(event) => setLineId(event.target.value)}
            placeholder="Line ID"
          />
          <input
            className="input"
            type="number"
            value={limit}
            onChange={(event) => setLimit(Number(event.target.value) || 20)}
            placeholder="Limit"
          />
        </div>
      </div>
      <div className="card">
        <h2>Recent Bottlenecks</h2>
        {loading ? (
          <p className="muted">Loading bottlenecks...</p>
        ) : error ? (
          <p className="error">Failed to load bottlenecks.</p>
        ) : items.length ? (
          <ul className="placeholder-list">
            {items.map((item) => (
              <li key={item.bottleneck_id}>
                #{item.bottleneck_id} | line {item.line_id} | {item.duration_sec}s
              </li>
            ))}
          </ul>
        ) : (
          <p className="muted">No bottleneck data.</p>
        )}
      </div>
      <div className="module-grid">
        <CauseDonut items={items} />
        <DurationBar items={items} />
        <TimelineChart items={items} />
        <BottleneckTable items={items} />
        <ErrorTable />
      </div>
    </section>
  );
};

export default BottleneckAnalytics;
