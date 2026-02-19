import { request } from "./apiClient.js";

const listCenters = ({ page = 1, size = 20, q } = {}) =>
  request("/api/settings/centers", { params: { page, size, q } });

const createCenter = (payload) =>
  request("/api/settings/centers", { method: "POST", body: payload });

const updateCenter = (center_id, payload) =>
  request(`/api/settings/centers/${center_id}`, { method: "PUT", body: payload });

const deleteCenter = (center_id) =>
  request(`/api/settings/centers/${center_id}`, { method: "DELETE" });

const listZones = (center_id) =>
  request(`/api/settings/centers/${center_id}/zones`);

const createZone = (payload) =>
  request("/api/settings/zones", { method: "POST", body: payload });

const listLines = (center_id) =>
  request(`/api/settings/centers/${center_id}/lines`);

const createLine = (payload, center_id) =>
  request("/api/settings/lines", { method: "POST", body: payload, params: { center_id } });

const listSections = (line_id, center_id) =>
  request(`/api/settings/lines/${line_id}/sections`, {
    params: center_id ? { center_id } : undefined
  });

const createSection = (payload, center_id) =>
  request("/api/settings/sections", { method: "POST", body: payload, params: { center_id } });

const listSensors = (line_id, center_id) =>
  request(`/api/settings/lines/${line_id}/sensors`, {
    params: center_id ? { center_id } : undefined
  });

const createSensor = (payload, center_id) =>
  request("/api/settings/sensors", { method: "POST", body: payload, params: { center_id } });


export {
  listCenters,
  createCenter,
  updateCenter,
  deleteCenter,
  listZones,
  createZone,
  listLines,
  createLine,
  listSections,
  createSection,
  listSensors,
  createSensor
};
