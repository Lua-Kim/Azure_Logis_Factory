import { useEffect, useState } from "react";
import { useMemo } from "react";
import useAsync from "../hooks/useAsync.js";
import {
  getSummary,
  getLineMetrics,
  getErrorAnalysis,
  getTrend
} from "../services/performanceService.js";
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
  Legend,
  ResponsiveContainer,
  Cell
} from "recharts";

const PerformanceDashboard = () => {
  const [centerId, setCenterId] = useState(null);
  const [hours, setHours] = useState(24);

  const summaryState = useAsync(
    () =>
      centerId
        ? getSummary({ center_id: centerId, hours })
        : getSummary({ hours }),
    [centerId, hours]
  );

  const metricsState = useAsync(
    () =>
      centerId
        ? getLineMetrics({ center_id: centerId, hours })
        : getLineMetrics({ hours }),
    [centerId, hours]
  );

  const errorState = useAsync(
    () =>
      centerId
        ? getErrorAnalysis({ center_id: centerId, hours })
        : getErrorAnalysis({ hours }),
    [centerId, hours]
  );

  const trendState = useAsync(
    () =>
      centerId
        ? getTrend({ center_id: centerId, interval: "hourly" })
        : getTrend({ interval: "hourly" }),
    [centerId]
  );

  const summary = summaryState.data || {};
  const metrics = metricsState.data || [];
  const errors = errorState.data || {};
  const trend = trendState.data || {};

  // KPI 계산
  const summaryKpis = useMemo(
    () => [
      {
        label: "병목 이벤트",
        value: summary.total_bottleneck_events || 0,
        icon: "⚠️",
        color: "#ef4444"
      },
      {
        label: "평균 지속시간",
        value: `${(summary.avg_bottleneck_duration_sec || 0).toFixed(2)}초`,
        icon: "⏱️",
        color: "#f59e0b"
      },
      {
        label: "총 가동중단",
        value: `${Math.round((summary.total_downtime_sec || 0) / 60)}분`,
        icon: "🛑",
        color: "#ef5350"
      },
      {
        label: "처리량",
        value: summary.total_throughput || 0,
        icon: "📦",
        color: "#10b981"
      }
    ],
    [summary]
  );

  // 라인별 가용성 색상
  const getAvailabilityColor = (availability) => {
    if (availability >= 95) return "#10b981";
    if (availability >= 90) return "#f59e0b";
    if (availability >= 80) return "#f97316";
    return "#ef4444";
  };

  return (
    <div style={{ padding: "20px", backgroundColor: "#f9fafb", minHeight: "100vh" }}>
      {/* 헤더 */}
      <div
        style={{
          marginBottom: "30px",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center"
        }}
      >
        <h1 style={{ margin: 0, fontSize: "28px", fontWeight: "bold" }}>
          📊 성능 대시보드
        </h1>
        <div style={{ display: "flex", gap: "15px" }}>
          <select
            value={hours}
            onChange={(e) => setHours(Number(e.target.value))}
            style={{
              padding: "8px 12px",
              borderRadius: "6px",
              border: "1px solid #d1d5db",
              fontSize: "14px",
              backgroundColor: "white"
            }}
          >
            <option value={1}>지난 1시간</option>
            <option value={6}>지난 6시간</option>
            <option value={24}>지난 24시간</option>
            <option value={168}>지난 7일</option>
          </select>
        </div>
      </div>

      {/* KPI 카드 그리드 */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
          gap: "15px",
          marginBottom: "30px"
        }}
      >
        {summaryKpis.map((kpi) => (
          <div
            key={kpi.label}
            style={{
              backgroundColor: "white",
              borderRadius: "8px",
              padding: "20px",
              boxShadow: "0 1px 3px rgba(0,0,0,0.1)",
              borderLeft: `4px solid ${kpi.color}`
            }}
          >
            <div style={{ fontSize: "32px", marginBottom: "8px" }}>
              {kpi.icon}
            </div>
            <div
              style={{ fontSize: "12px", color: "#6b7280", marginBottom: "8px" }}
            >
              {kpi.label}
            </div>
            <div
              style={{
                fontSize: "24px",
                fontWeight: "bold",
                color: kpi.color
              }}
            >
              {kpi.value}
            </div>
          </div>
        ))}
      </div>

      {/* 라인별 성능 지표 테이블 */}
      <div
        style={{
          backgroundColor: "white",
          borderRadius: "8px",
          padding: "20px",
          marginBottom: "30px",
          boxShadow: "0 1px 3px rgba(0,0,0,0.1)"
        }}
      >
        <h2
          style={{
            fontSize: "18px",
            fontWeight: "bold",
            marginBottom: "15px",
            margin: "0 0 15px 0"
          }}
        >
          📈 라인별 성능 지표
        </h2>

        {metricsState.loading ? (
          <p style={{ color: "#6b7280" }}>로딩 중...</p>
        ) : metricsState.error ? (
          <p style={{ color: "#ef4444" }}>데이터를 불러올 수 없습니다.</p>
        ) : metrics.length === 0 ? (
          <p style={{ color: "#6b7280" }}>데이터가 없습니다.</p>
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table
              style={{
                width: "100%",
                borderCollapse: "collapse",
                fontSize: "14px"
              }}
            >
              <thead>
                <tr style={{ borderBottom: "2px solid #e5e7eb" }}>
                  <th
                    style={{
                      padding: "12px",
                      textAlign: "left",
                      fontWeight: "600",
                      color: "#374151"
                    }}
                  >
                    라인명
                  </th>
                  <th style={{ ...headerStyle }}>처리량</th>
                  <th style={{ ...headerStyle }}>병목(건)</th>
                  <th style={{ ...headerStyle }}>평균시간(초)</th>
                  <th style={{ ...headerStyle }}>최대시간(초)</th>
                  <th style={{ ...headerStyle }}>가용성</th>
                  <th style={{ ...headerStyle }}>오류율</th>
                </tr>
              </thead>
              <tbody>
                {metrics.map((line) => (
                  <tr
                    key={line.line_id}
                    style={{ borderBottom: "1px solid #f3f4f6" }}
                  >
                    <td style={{ padding: "12px", fontWeight: "500" }}>
                      {line.line_name}
                    </td>
                    <td style={{ padding: "12px", textAlign: "center" }}>
                      {line.throughput}
                    </td>
                    <td style={{ padding: "12px", textAlign: "center" }}>
                      {line.bottleneck_count}
                    </td>
                    <td style={{ padding: "12px", textAlign: "center" }}>
                      {line.avg_bottleneck_duration_sec}
                    </td>
                    <td style={{ padding: "12px", textAlign: "center" }}>
                      {line.max_bottleneck_duration_sec}
                    </td>
                    <td style={{ padding: "12px", textAlign: "center" }}>
                      <span
                        style={{
                          display: "inline-block",
                          padding: "4px 8px",
                          borderRadius: "4px",
                          backgroundColor: getAvailabilityColor(
                            line.availability_percent
                          ),
                          color: "white",
                          fontWeight: "bold"
                        }}
                      >
                        {line.availability_percent}%
                      </span>
                    </td>
                    <td style={{ padding: "12px", textAlign: "center" }}>
                      <span style={{ color: line.error_rate_percent > 5 ? "#ef4444" : "#10b981" }}>
                        {line.error_rate_percent.toFixed(2)}%
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* 성능 추이 차트 */}
      {trend.throughput_trend && trend.throughput_trend.length > 0 && (
        <div
          style={{
            backgroundColor: "white",
            borderRadius: "8px",
            padding: "20px",
            marginBottom: "30px",
            boxShadow: "0 1px 3px rgba(0,0,0,0.1)"
          }}
        >
          <h2
            style={{
              fontSize: "18px",
              fontWeight: "bold",
              marginBottom: "15px",
              margin: "0 0 15px 0"
            }}
          >
            📊 시간대별 처리량 추이
          </h2>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={trend.throughput_trend}>
              <defs>
                <linearGradient id="colorThroughput" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.8} />
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis
                dataKey="timestamp"
                tick={{ fontSize: 12 }}
                angle={-45}
                textAnchor="end"
                height={80}
              />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip
                contentStyle={{
                  backgroundColor: "#fff",
                  border: "1px solid #e5e7eb",
                  borderRadius: "4px"
                }}
              />
              <Area
                type="monotone"
                dataKey="throughput"
                stroke="#3b82f6"
                fillOpacity={1}
                fill="url(#colorThroughput)"
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* 병목 이벤트 추이 */}
      {trend.bottleneck_trend && trend.bottleneck_trend.length > 0 && (
        <div
          style={{
            backgroundColor: "white",
            borderRadius: "8px",
            padding: "20px",
            marginBottom: "30px",
            boxShadow: "0 1px 3px rgba(0,0,0,0.1)"
          }}
        >
          <h2
            style={{
              fontSize: "18px",
              fontWeight: "bold",
              marginBottom: "15px",
              margin: "0 0 15px 0"
            }}
          >
            ⚠️ 시간대별 병목 이벤트
          </h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={trend.bottleneck_trend}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis
                dataKey="timestamp"
                tick={{ fontSize: 12 }}
                angle={-45}
                textAnchor="end"
                height={80}
              />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip
                contentStyle={{
                  backgroundColor: "#fff",
                  border: "1px solid #e5e7eb",
                  borderRadius: "4px"
                }}
              />
              <Legend />
              <Bar dataKey="event_count" fill="#ef4444" name="이벤트 수" />
              <Bar dataKey="avg_duration_sec" fill="#f59e0b" name="평균 지속시간(초)" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* 오류 분석 */}
      {errors.error_code_distribution && errors.error_code_distribution.length > 0 && (
        <div
          style={{
            backgroundColor: "white",
            borderRadius: "8px",
            padding: "20px",
            boxShadow: "0 1px 3px rgba(0,0,0,0.1)"
          }}
        >
          <h2
            style={{
              fontSize: "18px",
              fontWeight: "bold",
              marginBottom: "15px",
              margin: "0 0 15px 0"
            }}
          >
            🔍 오류 분석
          </h2>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "20px" }}>
            <div>
              <h3 style={{ fontSize: "14px", fontWeight: "600", marginBottom: "10px" }}>
                오류 유형별 분포
              </h3>
              <ul style={{ margin: 0, paddingLeft: "20px" }}>
                {errors.error_code_distribution.slice(0, 5).map((e) => (
                  <li key={e.error_code} style={{ marginBottom: "8px", color: "#374151" }}>
                    <strong>{e.error_code}</strong>: {e.count}건
                  </li>
                ))}
              </ul>
            </div>
            <div>
              <h3 style={{ fontSize: "14px", fontWeight: "600", marginBottom: "10px" }}>
                주요 오류 센서
              </h3>
              <ul style={{ margin: 0, paddingLeft: "20px" }}>
                {(errors.top_error_sensors || []).slice(0, 5).map((s) => (
                  <li key={s.sensor_id} style={{ marginBottom: "8px", color: "#374151" }}>
                    <strong>센서 {s.sensor_id}</strong>: {s.error_count}건
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

const headerStyle = {
  padding: "12px",
  textAlign: "center",
  fontWeight: "600",
  color: "#374151",
  borderBottom: "2px solid #e5e7eb"
};

export default PerformanceDashboard;
