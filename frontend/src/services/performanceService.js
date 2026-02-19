import { request } from "./apiClient.js";

/**
 * 성능 대시보드 관련 API 서비스
 */

const getSummary = ({ center_id, hours = 24 } = {}) =>
  request("/api/performance/summary", {
    params: { center_id, hours }
  });

const getLineMetrics = ({ center_id, hours = 24 } = {}) =>
  request("/api/performance/line-metrics", {
    params: { center_id, hours }
  });

const getErrorAnalysis = ({ center_id, hours = 24 } = {}) =>
  request("/api/performance/error-analysis", {
    params: { center_id, hours }
  });

const getTrend = ({ center_id, interval = "hourly" } = {}) =>
  request("/api/performance/trend", {
    params: { center_id, interval }
  });

const getSensorMonitoring = ({ center_id, limit = 100, hours = 1 } = {}) =>
  request("/api/performance/sensor-monitoring", {
    params: { center_id, limit, hours }
  });

export {
  getSummary,
  getLineMetrics,
  getErrorAnalysis,
  getTrend,
  getSensorMonitoring
};
