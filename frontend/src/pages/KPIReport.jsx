import { useMemo, useState } from "react";
import useAsync from "../hooks/useAsync.js";
import { useFilters } from "../context/FilterContext.jsx";
import { getKpi } from "../services/metricsService.js";
import usePolling from "../hooks/usePolling.js";
import useWebSocketSnapshot from "../hooks/useWebSocketSnapshot.js";
import KPIHeatmap from "../components/kpi/KPIHeatmap.jsx";
import KPITable from "../components/kpi/KPITable.jsx";
import SLATrendChart from "../components/kpi/SLATrendChart.jsx";
import ThroughputScatter from "../components/kpi/ThroughputScatter.jsx";

const KPIReport = () => {
  const { window: globalWindow, refreshMs, wsEnabled, centerId, lineId } = useFilters();
  const [window, setWindow] = useState(globalWindow);
  const { data, loading, error, run } = useAsync(
    () => getKpi(window, 50),
    [window]
  );
  const { snapshot } = useWebSocketSnapshot(wsEnabled, {
    window,
    center_id: centerId || undefined,
    line_id: lineId || undefined
  });

  usePolling(run, wsEnabled ? 0 : refreshMs);
  const items = useMemo(() => {
    const base = wsEnabled && snapshot?.kpi ? snapshot.kpi : data || [];
    return base.filter((item) => {
      if (centerId && item.center_id !== Number(centerId)) {
        return false;
      }
      if (lineId && item.line_id !== Number(lineId)) {
        return false;
      }
      return true;
    });
  }, [data, snapshot, wsEnabled, centerId, lineId]);

  return (
    <section className="page">
      <p>Performance and SLA report placeholder.</p>
      <div className="card">
        <h2>Window</h2>
        <select
          className="input"
          value={window}
          onChange={(event) => setWindow(event.target.value)}
        >
          <option value="5m">5 minutes</option>
          <option value="1h">1 hour</option>
          <option value="24h">24 hours</option>
        </select>
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: "1rem", marginBottom: "1rem" }}>
        <div className="module-card">
          <SLATrendChart items={items} />
        </div>
        <div className="module-card">
          <ThroughputScatter items={items} />
        </div>
        <div className="module-card">
          <KPIHeatmap items={items} />
        </div>
        <div className="module-card">
          <KPITable items={items} />
        </div>
      </div>
      <div className="card">
        <h2>Recent KPI</h2>
        {loading ? (
          <p className="muted">Loading KPI...</p>
        ) : error ? (
          <p className="error">Failed to load KPI.</p>
        ) : items.length ? (
          <ul className="placeholder-list">
            {items.map((item) => (
              <li key={`${item.window_end}-${item.line_id}`}>
                {new Date(item.window_end).toLocaleString()} | line {item.line_id}
                | throughput {item.throughput_count}
              </li>
            ))}
          </ul>
        ) : (
          <p className="muted">No KPI data.</p>
        )}
      </div>
    </section>
  );
};

export default KPIReport;
