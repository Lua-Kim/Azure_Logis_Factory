import { request } from "./apiClient.js";

const getLineStatus = () => request("/api/line/status");

const getKpi = (window = "5m", limit = 200) =>
  request("/api/kpi", { params: { window, limit } });

const getBottlenecks = ({ from_ts, to_ts, center_id, line_id, limit = 200 } = {}) =>
  request("/api/bottlenecks", {
    params: { from_ts, to_ts, center_id, line_id, limit }
  });

const getRecentEvents = (limit = 100) =>
  request("/api/events/recent", { params: { limit } });

const getLineAnalytics = ({ line_id, granularity = "hour", start_ts, end_ts }) =>
  request("/api/line/analytics", {
    params: { line_id, granularity, start_ts, end_ts }
  });

export {
  getLineStatus,
  getKpi,
  getBottlenecks,
  getRecentEvents,
  getLineAnalytics
};
