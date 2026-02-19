import { useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import useAsync from "../hooks/useAsync.js";
import { getLineAnalytics } from "../services/metricsService.js";
import { useFilters } from "../context/FilterContext.jsx";
import usePolling from "../hooks/usePolling.js";
import BottleneckHistogram from "../components/line/BottleneckHistogram.jsx";
import LineSummaryCard from "../components/line/LineSummaryCard.jsx";
import SectionHeatmap from "../components/line/SectionHeatmap.jsx";
import SectionTable from "../components/line/SectionTable.jsx";
import ThroughputChart from "../components/line/ThroughputChart.jsx";
import TimeRangeTabs from "../components/line/TimeRangeTabs.jsx";

const LineAnalytics = () => {
  const { lineId } = useParams();
  const [granularity, setGranularity] = useState("hour");
  const [showGuide, setShowGuide] = useState(true);

  const { refreshMs } = useFilters();
  const { data, loading, error, run } = useAsync(
    () =>
      lineId
        ? getLineAnalytics({ line_id: Number(lineId), granularity })
        : Promise.resolve([]),
    [lineId, granularity]
  );

  usePolling(run, refreshMs);

  const buckets = useMemo(() => data || [], [data]);

  return (
    <section className="page">
      <p>Line-level throughput and bottleneck analysis placeholder.</p>
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
            <p className="muted">라인 단위 처리량/병목 추이를 분석합니다.</p>
            <p className="muted">시간 단위를 변경해 추세를 비교하세요.</p>
            <p className="muted">섹션 히트맵에서 병목 구간을 확인합니다.</p>
          </div>
        </div>
      ) : null}
      <div className="card">
        <h2>Line {lineId || "-"} Overview</h2>
        <div className="form-grid">
          <select
            className="input"
            value={granularity}
            onChange={(event) => setGranularity(event.target.value)}
          >
            <option value="hour">Hour</option>
            <option value="day">Day</option>
            <option value="month">Month</option>
            <option value="year">Year</option>
          </select>
        </div>
        {loading ? (
          <p className="muted">Loading analytics...</p>
        ) : error ? (
          <p className="error">Failed to load analytics.</p>
        ) : buckets.length ? (
          <ul className="placeholder-list">
            {buckets.map((bucket) => (
              <li key={bucket.bucket}>
                {new Date(bucket.bucket).toLocaleString()} | events:
                {" "}{bucket.event_count}
              </li>
            ))}
          </ul>
        ) : (
          <p className="muted">No analytics data.</p>
        )}
      </div>
      <div className="module-grid">
        <LineSummaryCard />
        <TimeRangeTabs />
        <ThroughputChart items={buckets} />
        <BottleneckHistogram items={buckets} />
        <SectionHeatmap />
        <SectionTable />
      </div>
    </section>
  );
};

export default LineAnalytics;
