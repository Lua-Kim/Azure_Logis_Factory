import { useMemo, useState } from "react";
import useAsync from "../hooks/useAsync.js";
import { getCostLossSummary } from "../services/performanceService.js";
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer
} from "recharts";

const CENTER_OPTIONS = [
  { label: "All (Main)", value: "" },
  { label: "Center 100", value: 100 },
  { label: "Center 110", value: 110 },
  { label: "Center 120", value: 120 },
  { label: "Center 130", value: 130 },
  { label: "Center 140", value: 140 }
];

const DAY_OPTIONS = [7, 14, 30];

const formatNumber = (value) =>
  new Intl.NumberFormat("en-US").format(value || 0);

const CostLossDashboard = () => {
  const [centerId, setCenterId] = useState("");
  const [days, setDays] = useState(7);
  const [showGuide, setShowGuide] = useState(true);

  const summaryState = useAsync(
    () =>
      centerId
        ? getCostLossSummary({ center_id: Number(centerId), days })
        : getCostLossSummary({ days }),
    [centerId, days]
  );

  const summary = summaryState.data || {};
  const costByCategory = summary.cost_by_category || [];
  const lossByLine = summary.loss_by_line || [];
  const costTrend = summary.cost_trend || [];
  const lossTrend = summary.loss_trend || [];
  const aggregationTrend = summary.aggregation_trend || [];

  const metrics = useMemo(() => {
    const costTotal = summary.cost_total || 0;
    const lossTotal = summary.loss_total || 0;
    const lossRate = costTotal > 0 ? (lossTotal / costTotal) * 100 : 0;
    const avgDailyCost = costTotal / Math.max(days, 1);

    return [
      { label: "Total Cost", value: formatNumber(costTotal), helper: "Last period" },
      { label: "Total Loss", value: formatNumber(lossTotal), helper: "Loss analysis" },
      { label: "Loss Rate", value: `${lossRate.toFixed(1)}%`, helper: "Loss vs cost" },
      { label: "Avg Daily Cost", value: formatNumber(Math.round(avgDailyCost)), helper: "Daily average" }
    ];
  }, [summary, days]);

  return (
    <section className="cost-loss-page">
      <div className="cost-hero">
        <div>
          <p className="cost-eyebrow">Operations Finance</p>
          <h1>Cost and Loss Intelligence</h1>
          <p className="cost-subtitle">
            Track operational spend, detect leakage, and validate throughput impact
            across centers in near real-time.
          </p>
        </div>
        <div className="cost-controls">
          <label className="filter-item">
            Center
            <select
              className="input"
              value={centerId}
              onChange={(event) => setCenterId(event.target.value)}
            >
              {CENTER_OPTIONS.map((option) => (
                <option key={option.label} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>
          <label className="filter-item">
            Period
            <select
              className="input"
              value={days}
              onChange={(event) => setDays(Number(event.target.value))}
            >
              {DAY_OPTIONS.map((value) => (
                <option key={value} value={value}>
                  Last {value} days
                </option>
              ))}
            </select>
          </label>
        </div>
      </div>

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
            <p className="muted">Cost/Loss는 기간별 비용과 손실을 요약합니다.</p>
            <p className="muted">Cost by Category: 카테고리별 비용 분포입니다.</p>
            <p className="muted">Loss by Line: 손실이 큰 라인을 비교합니다.</p>
            <p className="muted">Daily Trend: 비용/손실의 일별 변화 추세입니다.</p>
            <p className="muted">Throughput vs Bottlenecks: 집계 요약 지표를 함께 봅니다.</p>
          </div>
        </div>
      ) : null}

      {summaryState.loading ? (
        <p className="muted">Loading cost and loss data...</p>
      ) : summaryState.error ? (
        <p className="error">Failed to load cost and loss summary.</p>
      ) : (
        <>
          <div className="cost-metrics">
            {metrics.map((metric) => (
              <div key={metric.label} className="metric-card">
                <div>
                  <p className="metric-label">{metric.label}</p>
                  <p className="metric-value">{metric.value}</p>
                </div>
                <p className="metric-helper">{metric.helper}</p>
              </div>
            ))}
          </div>

          <div className="cost-grid">
            <div className="card cost-panel">
              <h2>Cost by Category</h2>
              {costByCategory.length ? (
                <ResponsiveContainer width="100%" height={260}>
                  <BarChart data={costByCategory}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="category" tick={{ fontSize: 11 }} />
                    <YAxis tick={{ fontSize: 11 }} />
                    <Tooltip />
                    <Bar dataKey="amount" fill="#2563eb" />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <p className="muted">No cost data yet.</p>
              )}
            </div>

            <div className="card cost-panel">
              <h2>Loss by Line</h2>
              {lossByLine.length ? (
                <ResponsiveContainer width="100%" height={260}>
                  <BarChart data={lossByLine}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="line_id" tick={{ fontSize: 11 }} />
                    <YAxis tick={{ fontSize: 11 }} />
                    <Tooltip />
                    <Bar dataKey="loss_amount" fill="#ef4444" />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <p className="muted">No loss data yet.</p>
              )}
            </div>

            <div className="card cost-panel">
              <h2>Daily Cost Trend</h2>
              {costTrend.length ? (
                <ResponsiveContainer width="100%" height={240}>
                  <AreaChart data={costTrend}>
                    <defs>
                      <linearGradient id="costGradient" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#2563eb" stopOpacity={0.35} />
                        <stop offset="95%" stopColor="#2563eb" stopOpacity={0.02} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                    <YAxis tick={{ fontSize: 11 }} />
                    <Tooltip />
                    <Area type="monotone" dataKey="amount" stroke="#2563eb" fill="url(#costGradient)" />
                  </AreaChart>
                </ResponsiveContainer>
              ) : (
                <p className="muted">No daily cost trend.</p>
              )}
            </div>

            <div className="card cost-panel">
              <h2>Daily Loss Trend</h2>
              {lossTrend.length ? (
                <ResponsiveContainer width="100%" height={240}>
                  <LineChart data={lossTrend}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                    <YAxis tick={{ fontSize: 11 }} />
                    <Tooltip />
                    <Line type="monotone" dataKey="loss_amount" stroke="#f97316" strokeWidth={2} />
                  </LineChart>
                </ResponsiveContainer>
              ) : (
                <p className="muted">No loss trend yet.</p>
              )}
            </div>

            <div className="card cost-panel cost-span">
              <div className="panel-header">
                <h2>Throughput vs Bottlenecks</h2>
                <p className="muted">Aggregated from aggregation_summary</p>
              </div>
              {aggregationTrend.length ? (
                <ResponsiveContainer width="100%" height={260}>
                  <LineChart data={aggregationTrend}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="timestamp" tick={{ fontSize: 11 }} />
                    <YAxis yAxisId="left" tick={{ fontSize: 11 }} />
                    <YAxis yAxisId="right" orientation="right" tick={{ fontSize: 11 }} />
                    <Tooltip />
                    <Line yAxisId="left" type="monotone" dataKey="throughput_total" stroke="#10b981" strokeWidth={2} />
                    <Line yAxisId="right" type="monotone" dataKey="bottleneck_count" stroke="#ef4444" strokeWidth={2} />
                  </LineChart>
                </ResponsiveContainer>
              ) : (
                <p className="muted">No aggregation summary data.</p>
              )}
            </div>
          </div>
        </>
      )}
    </section>
  );
};

export default CostLossDashboard;
