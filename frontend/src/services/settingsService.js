import { request } from "./apiClient.js";

const listCenters = ({ page = 1, size = 20, q } = {}) =>
  request("/api/settings/centers", { params: { page, size, q } });

const createCenter = (payload) =>
  request("/api/settings/centers", { method: "POST", body: payload });

const updateCenter = (center_id, payload) =>
  request(`/api/settings/centers/${center_id}`, { method: "PUT", body: payload });

const listZones = (center_id) =>
  request(`/api/settings/centers/${center_id}/zones`);

const createZone = (payload) =>
  request("/api/settings/zones", { method: "POST", body: payload });

const listLines = (center_id) =>
  request(`/api/settings/centers/${center_id}/lines`);

const createLine = (payload) =>
  request("/api/settings/lines", { method: "POST", body: payload });

const listSections = (line_id) =>
  request(`/api/settings/lines/${line_id}/sections`);

const createSection = (payload) =>
  request("/api/settings/sections", { method: "POST", body: payload });

const listSensors = (line_id) =>
  request(`/api/settings/lines/${line_id}/sensors`);

const createSensor = (payload) =>
  request("/api/settings/sensors", { method: "POST", body: payload });

const listThresholds = () => request("/api/settings/thresholds");

const updateThreshold = (config_key, payload) =>
  request(`/api/settings/thresholds/${config_key}`, {
    method: "PUT",
    body: payload
  });

export {
  listCenters,
  createCenter,
  updateCenter,
  listZones,
  createZone,
  listLines,
  createLine,
  listSections,
  createSection,
  listSensors,
  createSensor,
  listThresholds,
  updateThreshold
};
