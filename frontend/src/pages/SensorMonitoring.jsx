import { useEffect, useState } from "react";
import useAsync from "../hooks/useAsync.js";
import { getSensorMonitoring } from "../services/performanceService.js";

const SensorMonitoring = () => {
  const [limit, setLimit] = useState(50);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [lastRefresh, setLastRefresh] = useState(0);

  const sensorState = useAsync(
    () => getSensorMonitoring({ limit, hours: 1 }),
    [limit, lastRefresh]
  );

  useEffect(() => {
    if (!autoRefresh) return;
    const interval = setInterval(() => {
      setLastRefresh((prev) => prev + 1);
    }, 5000);
    return () => clearInterval(interval);
  }, [autoRefresh]);

  const data = sensorState.data || {};
  const sensorHealth = data.sensor_health || [];
  const errorEvents = data.error_events || [];

  const getHealthColor = (status) => {
    switch (status) {
      case "HEALTHY": return "#10b981";
      case "WARNING": return "#f59e0b";
      case "CRITICAL": return "#ef4444";
      default: return "#6b7280";
    }
  };

  const getHealthLabel = (status) => {
    if (status === "HEALTHY") return "정상";
    if (status === "WARNING") return "경고";
    if (status === "CRITICAL") return "위험";
    return "미확인";
  };

  return (
    <div style={{ padding: "20px", backgroundColor: "#f9fafb", minHeight: "100vh" }}>
      <div style={{ marginBottom: "30px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h1 style={{ margin: 0, fontSize: "28px", fontWeight: "bold" }}>🚨 센서 모니터링</h1>
        <div style={{ display: "flex", gap: "15px" }}>
          <button
            onClick={() => setAutoRefresh(!autoRefresh)}
            style={{
              padding: "8px 16px",
              borderRadius: "6px",
              border: "none",
              backgroundColor: autoRefresh ? "#3b82f6" : "#e5e7eb",
              color: autoRefresh ? "white" : "#374151",
              cursor: "pointer"
            }}
          >
            {autoRefresh ? "🔄 ON" : "OFF"}
          </button>
          <select
            value={limit}
            onChange={(e) => setLimit(Number(e.target.value))}
            style={{ padding: "8px 12px", borderRadius: "6px", border: "1px solid #d1d5db" }}
          >
            <option value={10}>10개</option>
            <option value={50}>50개</option>
            <option value={100}>100개</option>
          </select>
        </div>
      </div>

      {sensorState.loading ? (
        <p style={{ color: "#6b7280" }}>로딩 중...</p>
      ) : sensorState.error ? (
        <p style={{ color: "#ef4444" }}>데이터 로드 실패: {sensorState.error.message}</p>
      ) : (
        <>
          {errorEvents.length > 0 && (
            <div style={{ backgroundColor: "#fef2f2", borderRadius: "8px", padding: "20px", marginBottom: "20px", borderLeft: "4px solid #ef4444" }}>
              <h2 style={{ fontSize: "16px", fontWeight: "bold", color: "#dc2626", margin: "0 0 10px 0" }}>
                🚨 오류 이벤트 ({errorEvents.length})
              </h2>
              {errorEvents.slice(0, 5).map((evt) => (
                <div key={evt.event_id} style={{ padding: "8px 0", fontSize: "13px", borderBottom: "1px solid #fecaca" }}>
                  <strong>{evt.error_code}</strong> - Line {evt.line_id}, Sensor {evt.sensor_id}
                </div>
              ))}
            </div>
          )}

          <div style={{ backgroundColor: "white", borderRadius: "8px", padding: "20px", boxShadow: "0 1px 3px rgba(0,0,0,0.1)" }}>
            <h2 style={{ fontSize: "16px", fontWeight: "bold", marginBottom: "15px", margin: "0 0 15px 0" }}>📊 센서 건강도</h2>
            {sensorHealth.length === 0 ? (
              <p style={{ color: "#6b7280" }}>데이터 없음</p>
            ) : (
              <table style={{ width: "100%", borderCollapse: "collapse" }}>
                <thead>
                  <tr style={{ borderBottom: "2px solid #e5e7eb" }}>
                    <th style={{ padding: "10px", textAlign: "left", fontWeight: "600" }}>라인</th>
                    <th style={{ padding: "10px", textAlign: "left", fontWeight: "600" }}>센서</th>
                    <th style={{ padding: "10px", textAlign: "center", fontWeight: "600" }}>이벤트</th>
                    <th style={{ padding: "10px", textAlign: "center", fontWeight: "600" }}>오류</th>
                    <th style={{ padding: "10px", textAlign: "center", fontWeight: "600" }}>상태</th>
                    <th style={{ padding: "10px", textAlign: "center", fontWeight: "600" }}>점수</th>
                  </tr>
                </thead>
                <tbody>
                  {sensorHealth.slice(0, 20).map((s) => (
                    <tr key={`${s.line_id}-${s.sensor_id}`} style={{ borderBottom: "1px solid #f3f4f6", fontSize: "13px" }}>
                      <td style={{ padding: "10px" }}>{s.line_id}</td>
                      <td style={{ padding: "10px" }}>S-{s.sensor_id}</td>
                      <td style={{ padding: "10px", textAlign: "center" }}>{s.event_count}</td>
                      <td style={{ padding: "10px", textAlign: "center", color: "#ef4444" }}>{s.error_count}</td>
                      <td style={{ padding: "10px", textAlign: "center" }}>
                        <span style={{
                          display: "inline-block",
                          padding: "3px 8px",
                          borderRadius: "4px",
                          backgroundColor: getHealthColor(s.health_status),
                          color: "white",
                          fontSize: "11px"
                        }}>
                          {getHealthLabel(s.health_status)}
                        </span>
                      </td>
                      <td style={{ padding: "10px", textAlign: "center", fontWeight: "bold" }}>{s.health_score.toFixed(0)}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </>
      )}
    </div>
  );
};

export default SensorMonitoring;
