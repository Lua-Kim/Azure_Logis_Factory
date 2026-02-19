import { useMemo, useState } from "react";
import useAsync from "../hooks/useAsync.js";
import { useFilters } from "../context/FilterContext.jsx";
import { getBottlenecks, getKpi, getLineStatus } from "../services/metricsService.js";
import usePolling from "../hooks/usePolling.js";
import useWebSocketSnapshot from "../hooks/useWebSocketSnapshot.js";
import BottleneckTable from "../components/dashboard/BottleneckTable.jsx";
import CenterSummaryTable from "../components/dashboard/CenterSummaryTable.jsx";
import ChartGrid from "../components/dashboard/ChartGrid.jsx";
import Filters from "../components/dashboard/Filters.jsx";
import KPIHeader from "../components/dashboard/KPIHeader.jsx";

const DashboardHQ = () => {
  const { window, refreshMs, wsEnabled, centerId, lineId } = useFilters();
  const [showGuide, setShowGuide] = useState(true);
  const {
    data: lineStatus,
    loading: lineLoading,
    error: lineError,
    run: runLineStatus
  } = useAsync(() => getLineStatus(), []);
  const {
    data: kpiData,
    loading: kpiLoading,
    error: kpiError,
    run: runKpi
  } = useAsync(() => getKpi(window, 20), [window]);
  const {
    data: bottleneckData,
    loading: bottleneckLoading,
    error: bottleneckError,
    run: runBottlenecks
  } = useAsync(
    () =>
      getBottlenecks({
        limit: 10,
        center_id: centerId ? Number(centerId) : undefined,
        line_id: lineId ? Number(lineId) : undefined
      }),
    [centerId, lineId]
  );

  const { snapshot, status: wsStatus } = useWebSocketSnapshot(wsEnabled, {
    window,
    center_id: centerId || undefined,
    line_id: lineId || undefined
  });
  const interval = wsEnabled ? 0 : refreshMs;

  usePolling(runLineStatus, interval);
  usePolling(runKpi, interval);
  usePolling(runBottlenecks, interval);

  const liveLineStatus = snapshot?.line_status || lineStatus;
  const liveKpiData = snapshot?.kpi || kpiData;
  const liveBottlenecks = snapshot?.bottlenecks || bottleneckData;

  const filteredKpi = useMemo(() => {
    if (!liveKpiData) {
      return [];
    }
    return liveKpiData.filter((item) => {
      if (centerId && item.center_id !== Number(centerId)) {
        return false;
      }
      if (lineId && item.line_id !== Number(lineId)) {
        return false;
      }
      return true;
    });
  }, [liveKpiData, centerId, lineId]);

  const filteredBottlenecks = useMemo(() => {
    if (!liveBottlenecks) {
      return [];
    }
    return liveBottlenecks.filter((item) => {
      if (centerId && item.center_id !== Number(centerId)) {
        return false;
      }
      if (lineId && item.line_id !== Number(lineId)) {
        return false;
      }
      return true;
    });
  }, [liveBottlenecks, centerId, lineId]);

  const latestKpi = filteredKpi?.[0];
  const totalLines = liveLineStatus?.length || 0;
  const activeBottlenecks = liveLineStatus?.reduce(
    (sum, line) => sum + (line.active_bottlenecks || 0),
    0
  );

  const centerSummary = useMemo(() => {
    if (!filteredKpi) {
      return [];
    }
    const summaryMap = new Map();
    filteredKpi.forEach((item) => {
      if (!item.center_id) {
        return;
      }
      const current = summaryMap.get(item.center_id) || {
        center_id: item.center_id,
        throughput_total: 0,
        last_window_end: null
      };
      current.throughput_total += item.throughput_count || 0;
      if (!current.last_window_end || item.window_end > current.last_window_end) {
        current.last_window_end = item.window_end;
      }
      summaryMap.set(item.center_id, current);
    });
    return Array.from(summaryMap.values()).sort(
      (a, b) => a.center_id - b.center_id
    );
  }, [filteredKpi]);

  return (
    <section className="page">
      <p>Multi-center aggregate dashboard placeholder.</p>
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
            <p className="muted">
              ChartGrid: 처리량의 시간적 추이를 추적(Tracking)합니다.
            </p>
            <p className="muted">
              Line Status / Latest KPI Window: 전체 라인의 현재 상태 요약과
              가장 최신 KPI 집계 시점을 빠르게 확인합니다.
            </p>
            <p className="muted">
              KPIHeader / Filters: 핵심 KPI 카드와 필터 영역으로, 센터·라인 등
              기준을 바꿔가며 요약을 볼 수 있습니다.
            </p>
            <p className="muted">
              CenterSummaryTable: 센터별 처리량 누적 요약을 테이블로
              보여줍니다.
            </p>
            <p className="muted">
              BottleneckTable: 최근 병목 이벤트를 리스트로 표시해 문제 구간을
              빠르게 파악합니다.
            </p>
          </div>
        </div>
      ) : null}
      <div className="dashboard-rows">
        <div className="dashboard-row dashboard-row--full">
          <ChartGrid kpiItems={filteredKpi || []} />
        </div>
        <div className="dashboard-row dashboard-row--two">
          <div className="card">
            <h2>Line Status</h2>
            {lineLoading ? (
              <p className="muted">Loading line status...</p>
            ) : lineError ? (
              <p className="error">Failed to load line status.</p>
            ) : (
              <div className="stat-block">
                <div>
                  <span className="stat-label">Total Lines</span>
                  <span className="stat-value">{totalLines}</span>
                </div>
                <div>
                  <span className="stat-label">Active Bottlenecks</span>
                  <span className="stat-value">{activeBottlenecks}</span>
                </div>
              </div>
            )}
          </div>
          <div className="card">
            <h2>Latest KPI Window</h2>
            {kpiLoading ? (
              <p className="muted">Loading KPI data...</p>
            ) : kpiError ? (
              <p className="error">Failed to load KPI data.</p>
            ) : latestKpi ? (
              <div className="stat-block">
                <div>
                  <span className="stat-label">Window End</span>
                  <span className="stat-value">
                    {new Date(latestKpi.window_end).toLocaleString()}
                  </span>
                </div>
                <div>
                  <span className="stat-label">Throughput</span>
                  <span className="stat-value">
                    {latestKpi.throughput_count ?? 0}
                  </span>
                </div>
              </div>
            ) : (
              <p className="muted">No KPI data available.</p>
            )}
          </div>
        </div>
        <div className="dashboard-row dashboard-row--two">
          <KPIHeader
            subtitle="Aggregate KPIs"
            stats={[
              { label: "Total Lines", value: totalLines },
              { label: "Active Bottlenecks", value: activeBottlenecks },
              {
                label: "Latest Throughput",
                value: latestKpi?.throughput_count ?? 0
              }
            ]}
          />
          <Filters />
        </div>
        <div className="dashboard-row dashboard-row--full">
          <CenterSummaryTable items={centerSummary} />
        </div>
        <div className="dashboard-row dashboard-row--full">
          {bottleneckLoading ? (
            <p className="muted">Loading bottlenecks...</p>
          ) : bottleneckError ? (
            <p className="error">Failed to load bottlenecks.</p>
          ) : (
            <BottleneckTable items={filteredBottlenecks} />
          )}
        </div>
      </div>
    </section>
  );
};

export default DashboardHQ;
