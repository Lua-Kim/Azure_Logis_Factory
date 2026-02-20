import { useEffect, useMemo, useState } from "react";
import useAsync from "../hooks/useAsync.js";
import { useFilters } from "../context/FilterContext.jsx";
import { getKpi, getLineStatus } from "../services/metricsService.js";
import usePolling from "../hooks/usePolling.js";
import useWebSocketSnapshot from "../hooks/useWebSocketSnapshot.js";
import KPIHeatmap from "../components/kpi/KPIHeatmap.jsx";
import KPITable from "../components/kpi/KPITable.jsx";
import SLATrendChart from "../components/kpi/SLATrendChart.jsx";
import ThroughputScatter from "../components/kpi/ThroughputScatter.jsx";

const KPIReport = () => {
  const { window: globalWindow, refreshMs, wsEnabled } = useFilters();
  const [window, setWindow] = useState(globalWindow);
  const [showGuide, setShowGuide] = useState(true);
  const [centerId, setCenterId] = useState("");
  const [lineId, setLineId] = useState("");
  const [lineList, setLineList] = useState([]);

  useEffect(() => {
    getLineStatus().then((data) => {
      if (Array.isArray(data)) {
        setLineList(data);
      }
    });
  }, []);

  const centerList = useMemo(
    () => [...new Set(lineList.map((line) => line.center_id))],
    [lineList]
  );

  const filteredLines = useMemo(() => {
    if (!centerId) {
      return lineList;
    }
    return lineList.filter((line) => line.center_id === Number(centerId));
  }, [lineList, centerId]);

  const { data, loading, error, run } = useAsync(
    () =>
      getKpi(window, 50, {
        center_id: centerId ? Number(centerId) : undefined,
        line_id: lineId ? Number(lineId) : undefined
      }),
    [window, centerId, lineId]
  );
  const { snapshot } = useWebSocketSnapshot(wsEnabled, {
    window,
    center_id: centerId ? Number(centerId) : undefined,
    line_id: lineId ? Number(lineId) : undefined
  });

  usePolling(run, wsEnabled ? 0 : refreshMs);
  const items = useMemo(() => {
    const hasLiveKpi = wsEnabled && Array.isArray(snapshot?.kpi) && snapshot.kpi.length > 0;
    const base = hasLiveKpi ? snapshot.kpi : data || [];
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
            <p className="muted">Window에서 집계 기간을 선택합니다.</p>
            <p className="muted">SLA/Throughput/Heatmap/표를 함께 비교하세요.</p>
            <p className="muted">필터로 센터/라인을 좁히면 더 정확합니다.</p>
          </div>
        </div>
      ) : null}
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
      <div className="card">
        <h2>Scope</h2>
        <div className="form-grid">
          <label className="filter-item">
            Center ID
            <select
              className="input"
              value={centerId}
              onChange={(event) => {
                setCenterId(event.target.value);
                setLineId("");
              }}
            >
              <option value="">All Centers</option>
              {centerList.map((id) => (
                <option key={id} value={id}>
                  {id}
                </option>
              ))}
            </select>
          </label>
          <label className="filter-item">
            Line ID
            <select
              className="input"
              value={lineId}
              onChange={(event) => setLineId(event.target.value)}
            >
              <option value="">All Lines</option>
              {filteredLines.map((line) => (
                <option key={line.id} value={line.id}>
                  {line.name}
                </option>
              ))}
            </select>
          </label>
        </div>
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
