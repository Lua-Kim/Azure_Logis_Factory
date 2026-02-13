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
