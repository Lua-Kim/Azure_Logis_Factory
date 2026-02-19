import { useEffect, useMemo, useState } from "react";
import useAsync from "../hooks/useAsync.js";
import DataTable from "../components/common/DataTable.jsx";
import CenterForm from "../components/settings/CenterForm.jsx";
import CenterList from "../components/settings/CenterList.jsx";
import LineTab from "../components/settings/LineTab.jsx";
import SectionTab from "../components/settings/SectionTab.jsx";
import SensorTab from "../components/settings/SensorTab.jsx";
import ThresholdForm from "../components/settings/ThresholdForm.jsx";
import ZoneTab from "../components/settings/ZoneTab.jsx";
import {
  createCenter,
  createLine,
  createSection,
  createSensor,
  createZone,
  deleteCenter,
  listCenters,
  listLines,
  listSections,
  listSensors,
  listThresholds,
  listZones,
  updateCenter,
  updateThreshold
} from "../services/settingsService.js";

const emptyCenter = {
  center_id: null,
  name: "",
  location: "",
  status: "ACTIVE",
  opened_at: ""
};

const Settings = () => {
  const [newCenter, setNewCenter] = useState(emptyCenter);
  const [updateTargetId, setUpdateTargetId] = useState("");
  const [updateCenterPayload, setUpdateCenterPayload] = useState({
    name: "",
    location: "",
    status: "",
    opened_at: ""
  });
  const [zoneCenterId, setZoneCenterId] = useState("");
  const [lineCenterId, setLineCenterId] = useState("");
  const [sectionLineId, setSectionLineId] = useState("");
  const [sensorLineId, setSensorLineId] = useState("");
  const [thresholdKey, setThresholdKey] = useState("");
  const [thresholdValue, setThresholdValue] = useState("");
  const [thresholdDescription, setThresholdDescription] = useState("");
  const [activeTab, setActiveTab] = useState("centers");

  const [zoneForm, setZoneForm] = useState({
    center_id: "",
    name: "",
    type: "",
    status: "ACTIVE"
  });
  const [lineForm, setLineForm] = useState({
    center_id: "",
    name: "",
    type: "",
    status: "ACTIVE",
    rail_length_m: "",
    section_count: ""
  });
  const [sectionForm, setSectionForm] = useState({
    line_id: "",
    name: "",
    order_in_line: "",
    type: ""
  });
  const [sensorForm, setSensorForm] = useState({
    section_id: "",
    equipment_id: "",
    sensor_type: "",
    name: "",
    status: "ACTIVE"
  });

  const centersState = useAsync(() => listCenters({ page: 1, size: 50 }), []);
  const thresholdsState = useAsync(() => listThresholds(), []);

  const zonesState = useAsync(
    () => (zoneCenterId ? listZones(zoneCenterId) : Promise.resolve([])),
    [zoneCenterId]
  );
  const linesState = useAsync(
    () => (lineCenterId ? listLines(lineCenterId) : Promise.resolve([])),
    [lineCenterId]
  );
  const sectionsState = useAsync(
    () => (sectionLineId ? listSections(sectionLineId) : Promise.resolve([])),
    [sectionLineId]
  );
  const sensorsState = useAsync(
    () => (sensorLineId ? listSensors(sensorLineId) : Promise.resolve([])),
    [sensorLineId]
  );

  const centers = centersState.data?.items || [];
  const thresholds = thresholdsState.data || [];
  const zones = zonesState.data || [];
  const lines = linesState.data || [];
  const sections = sectionsState.data || [];
  const sensors = sensorsState.data || [];

  useEffect(() => {
    if (centers.length > 0) {
      // 센터가 선택되지 않으면 첫 센터 선택
      if (!zoneCenterId) {
        setZoneCenterId(centers[0].center_id);
      }
      // lineCenterId도 zoneCenterId와 동기화
      if (!lineCenterId) {
        setLineCenterId(zoneCenterId || centers[0].center_id);
      }
    }
  }, [centers, zoneCenterId, lineCenterId]);

  useEffect(() => {
    // 선택된 센터의 라인 목록 조회
    if (lineCenterId) {
      linesState.run();
    }
  }, [lineCenterId]);

  useEffect(() => {
    if (lines.length && !sectionLineId) {
      setSectionLineId(lines[0].line_id);
    }
    if (lines.length && !sensorLineId) {
      setSensorLineId(lines[0].line_id);
    }
  }, [lines, sectionLineId, sensorLineId]);

  const thresholdOptions = useMemo(
    () => thresholds.map((item) => item.config_key),
    [thresholds]
  );

  const handleCreateCenter = async (event) => {
    event.preventDefault();
    if (newCenter.center_id) {
      // Update mode
      const payload = Object.fromEntries(
        Object.entries(newCenter).filter(
          ([key, value]) => key !== "center_id" && value !== "" && value !== null
        )
      );
      await updateCenter(newCenter.center_id, payload);
    } else {
      // Create mode
      await createCenter(newCenter);
    }
    setNewCenter(emptyCenter);
    centersState.run();
  };

  const handleSelectCenter = (row) => {
    setNewCenter({
      center_id: row.center_id,
      name: row.name || "",
      location: row.location || "",
      status: row.status || "ACTIVE",
      opened_at: row.opened_at || ""
    });
    // 센터 선택 시 zoneCenterId와 lineCenterId도 업데이트하여 stats 표시
    setZoneCenterId(row.center_id);
    setLineCenterId(row.center_id);
  };

  const handleClearForm = () => {
    setNewCenter(emptyCenter);
  };

  const handleDeleteCenter = async () => {
    if (!newCenter.center_id) {
      alert("센터를 선택해주세요");
      return;
    }
    if (confirm(`정말 "${newCenter.name}" 센터를 삭제하시겠습니까?`)) {
      await deleteCenter(newCenter.center_id);
      setNewCenter(emptyCenter);
      centersState.run();
    }
  };

  const handleCreateZone = async (event) => {
    event.preventDefault();
    await createZone({ ...zoneForm, center_id: Number(zoneForm.center_id) });
    setZoneForm({ ...zoneForm, name: "", type: "" });
    zonesState.run();
  };

  const handleCreateLine = async (event) => {
    event.preventDefault();
    await createLine({
      ...lineForm,
      center_id: Number(lineForm.center_id),
      rail_length_m: Number(lineForm.rail_length_m),
      section_count: Number(lineForm.section_count)
    }, Number(lineForm.center_id));
    setLineForm({
      ...lineForm,
      name: "",
      type: "",
      rail_length_m: "",
      section_count: ""
    });
    linesState.run();
  };

  const handleCreateSection = async (event) => {
    event.preventDefault();
    await createSection({
      ...sectionForm,
      line_id: Number(sectionForm.line_id),
      order_in_line: sectionForm.order_in_line
        ? Number(sectionForm.order_in_line)
        : null
    }, Number(lineForm.center_id));
    setSectionForm({ ...sectionForm, name: "", order_in_line: "", type: "" });
    sectionsState.run();
  };

  const handleCreateSensor = async (event) => {
    event.preventDefault();
    await createSensor({
      ...sensorForm,
      section_id: Number(sensorForm.section_id),
      equipment_id: sensorForm.equipment_id
        ? Number(sensorForm.equipment_id)
        : null
    }, Number(lineForm.center_id));
    setSensorForm({
      ...sensorForm,
      equipment_id: "",
      sensor_type: "",
      name: ""
    });
    sensorsState.run();
  };

  const handleUpdateThreshold = async (event) => {
    event.preventDefault();
    if (!thresholdKey) {
      return;
    }
    await updateThreshold(thresholdKey, {
      config_value: thresholdValue,
      description: thresholdDescription
    });
    thresholdsState.run();
  };

  return (
    <section className="page">
      <p>System configuration and master data management.</p>

      <div className="card-grid">
        <div className="card">
          <h2>Current Configuration</h2>
          <div className="stat-block stat-row">
            <div>
              <span className="stat-label">Centers</span>
              <span className="stat-value">{centers.length}</span>
            </div>
            <div>
              <span className="stat-label">Zones (selected center)</span>
              <span className="stat-value">{zones.length}</span>
            </div>
            <div>
              <span className="stat-label">Lines (selected center)</span>
              <span className="stat-value">{lines.length}</span>
            </div>
            <div>
              <span className="stat-label">Sections (selected line)</span>
              <span className="stat-value">{sections.length}</span>
            </div>
            <div>
              <span className="stat-label">Sensors (selected line)</span>
              <span className="stat-value">{sensors.length}</span>
            </div>
          </div>
        </div>
      </div>

      <div className="tab-row">
        <button
          type="button"
          className={activeTab === "centers" ? "tab active" : "tab"}
          onClick={() => setActiveTab("centers")}
        >
          Centers
        </button>
        <button
          type="button"
          className={activeTab === "zones" ? "tab active" : "tab"}
          onClick={() => setActiveTab("zones")}
        >
          Zones
        </button>
        <button
          type="button"
          className={activeTab === "lines" ? "tab active" : "tab"}
          onClick={() => setActiveTab("lines")}
        >
          Lines
        </button>
        <button
          type="button"
          className={activeTab === "sections" ? "tab active" : "tab"}
          onClick={() => setActiveTab("sections")}
        >
          Sections
        </button>
        <button
          type="button"
          className={activeTab === "sensors" ? "tab active" : "tab"}
          onClick={() => setActiveTab("sensors")}
        >
          Sensors
        </button>
        <button
          type="button"
          className={activeTab === "thresholds" ? "tab active" : "tab"}
          onClick={() => setActiveTab("thresholds")}
        >
          Thresholds
        </button>
      </div>

      {activeTab === "centers" ? (
        <div className="card-grid">
          <CenterList>
          {centersState.loading ? (
            <p className="muted">Loading centers...</p>
          ) : centersState.error ? (
            <p className="error">Failed to load centers.</p>
          ) : (
            <DataTable
              rows={centers}
              columns={[
                { key: "center_id", label: "ID" },
                { key: "name", label: "Name" },
                { key: "location", label: "Location" },
                { key: "status", label: "Status" },
                {
                  key: "opened_at",
                  label: "Opened",
                  render: (row) => row.opened_at || "-"
                },
                {
                  key: "actions",
                  label: "Actions",
                  render: (row) => (
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        if (confirm(`정말 "${row.name}" 센터를 삭제하시겠습니까?`)) {
                          console.log("Deleting center:", row.center_id);
                          deleteCenter(row.center_id)
                            .then((res) => {
                              console.log("Delete response:", res);
                              centersState.run();
                              setNewCenter(emptyCenter);
                              alert("센터가 삭제되었습니다.");
                            })
                            .catch((err) => {
                              console.error("Delete error:", err);
                              alert("삭제 중 오류가 발생했습니다: " + err.message);
                            });
                        }
                      }}
                      style={{
                        padding: "6px 12px",
                        backgroundColor: "#ef4444",
                        color: "white",
                        border: "none",
                        borderRadius: "4px",
                        cursor: "pointer",
                        fontSize: "12px"
                      }}
                    >
                      Delete
                    </button>
                  )
                }
              ]}
              emptyMessage="No centers available."
              onRowClick={handleSelectCenter}
            />
          )}
          </CenterList>

          <CenterForm title={newCenter.center_id ? "Update Center" : "Create Center"}>
          <form className="form-grid" onSubmit={handleCreateCenter}>
            <input
              className="input"
              value={newCenter.name}
              onChange={(event) =>
                setNewCenter({ ...newCenter, name: event.target.value })
              }
              placeholder="Name"
              required
            />
            <input
              className="input"
              value={newCenter.location}
              onChange={(event) =>
                setNewCenter({ ...newCenter, location: event.target.value })
              }
              placeholder="Location"
            />
            <input
              className="input"
              value={newCenter.status}
              onChange={(event) =>
                setNewCenter({ ...newCenter, status: event.target.value })
              }
              placeholder="Status"
            />
            <input
              className="input"
              type="date"
              value={newCenter.opened_at}
              onChange={(event) =>
                setNewCenter({ ...newCenter, opened_at: event.target.value })
              }
            />
            <button className="button" type="submit">
              {newCenter.center_id ? "Update" : "Create"}
            </button>
            {newCenter.center_id && (
              <button className="button" type="button" onClick={handleClearForm}>
                Clear
              </button>
            )}
          </form>
          </CenterForm>

        </div>
      ) : null}

      {activeTab === "zones" ? (
        <div className="card-grid">
          <ZoneTab>
          <div className="form-grid">
            <select
              className="input"
              value={zoneCenterId}
              onChange={(event) => setZoneCenterId(event.target.value)}
            >
              <option value="">Select center</option>
              {centers.map((center) => (
                <option key={center.center_id} value={center.center_id}>
                  {center.name || `Center ${center.center_id}`}
                </option>
              ))}
            </select>
          </div>
          {zonesState.loading ? (
            <p className="muted">Loading zones...</p>
          ) : zonesState.error ? (
            <p className="error">Failed to load zones.</p>
          ) : (
            <DataTable
              rows={zones}
              columns={[
                { key: "zone_id", label: "ID" },
                { key: "center_id", label: "Center" },
                { key: "name", label: "Name" },
                { key: "type", label: "Type" },
                { key: "status", label: "Status" }
              ]}
              emptyMessage="No zones available."
            />
          )}
          <form className="form-grid" onSubmit={handleCreateZone}>
            <select
              className="input"
              value={zoneForm.center_id}
              onChange={(event) =>
                setZoneForm({ ...zoneForm, center_id: event.target.value })
              }
              required
            >
              <option value="">Center ID</option>
              {centers.map((center) => (
                <option key={center.center_id} value={center.center_id}>
                  {center.center_id}
                </option>
              ))}
            </select>
            <input
              className="input"
              value={zoneForm.name}
              onChange={(event) =>
                setZoneForm({ ...zoneForm, name: event.target.value })
              }
              placeholder="Zone name"
            />
            <input
              className="input"
              value={zoneForm.type}
              onChange={(event) =>
                setZoneForm({ ...zoneForm, type: event.target.value })
              }
              placeholder="Type"
            />
            <input
              className="input"
              value={zoneForm.status}
              onChange={(event) =>
                setZoneForm({ ...zoneForm, status: event.target.value })
              }
              placeholder="Status"
            />
            <button className="button" type="submit">
              Create Zone
            </button>
          </form>
          </ZoneTab>
        </div>
      ) : null}

      {activeTab === "lines" ? (
        <div className="card-grid">
          <LineTab>
          <div className="form-grid">
            <select
              className="input"
              value={lineCenterId}
              onChange={(event) => setLineCenterId(event.target.value)}
            >
              <option value="">Select center</option>
              {centers.map((center) => (
                <option key={center.center_id} value={center.center_id}>
                  {center.name || `Center ${center.center_id}`}
                </option>
              ))}
            </select>
          </div>
          {linesState.loading ? (
            <p className="muted">Loading lines...</p>
          ) : linesState.error ? (
            <p className="error">Failed to load lines.</p>
          ) : (
            <ul className="placeholder-list">
              {linesState.data?.map((line) => (
                <li key={line.line_id}>
                  {line.name || "Unnamed Line"} (ID: {line.line_id})
                </li>
              ))}
            </ul>
          )}
          <form className="form-grid" onSubmit={handleCreateLine}>
            <select
              className="input"
              value={lineForm.center_id}
              onChange={(event) =>
                setLineForm({ ...lineForm, center_id: event.target.value })
              }
              required
            >
              <option value="">Center ID</option>
              {centers.map((center) => (
                <option key={center.center_id} value={center.center_id}>
                  {center.center_id}
                </option>
              ))}
            </select>
            <input
              className="input"
              value={lineForm.name}
              onChange={(event) =>
                setLineForm({ ...lineForm, name: event.target.value })
              }
              placeholder="Line name"
            />
            <input
              className="input"
              value={lineForm.type}
              onChange={(event) =>
                setLineForm({ ...lineForm, type: event.target.value })
              }
              placeholder="Type"
            />
            <input
              className="input"
              value={lineForm.status}
              onChange={(event) =>
                setLineForm({ ...lineForm, status: event.target.value })
              }
              placeholder="Status"
            />
            <input
              className="input"
              type="number"
              value={lineForm.rail_length_m}
              onChange={(event) =>
                setLineForm({ ...lineForm, rail_length_m: event.target.value })
              }
              placeholder="Rail length (m)"
              required
            />
            <input
              className="input"
              type="number"
              value={lineForm.section_count}
              onChange={(event) =>
                setLineForm({ ...lineForm, section_count: event.target.value })
              }
              placeholder="Section count"
              required
            />
            <button className="button" type="submit">
              Create Line
            </button>
          </form>
          </LineTab>
        </div>
      ) : null}

      {activeTab === "sections" ? (
        <div className="card-grid">
          <SectionTab>
          <div className="form-grid">
            <input
              className="input"
              value={sectionLineId}
              onChange={(event) => setSectionLineId(event.target.value)}
              placeholder="Line ID to list sections"
            />
          </div>
          {sectionsState.loading ? (
            <p className="muted">Loading sections...</p>
          ) : sectionsState.error ? (
            <p className="error">Failed to load sections.</p>
          ) : (
            <ul className="placeholder-list">
              {sectionsState.data?.map((section) => (
                <li key={section.section_id}>
                  {section.name || "Unnamed Section"} (ID: {section.section_id})
                </li>
              ))}
            </ul>
          )}
          <form className="form-grid" onSubmit={handleCreateSection}>
            <input
              className="input"
              value={sectionForm.line_id}
              onChange={(event) =>
                setSectionForm({ ...sectionForm, line_id: event.target.value })
              }
              placeholder="Line ID"
              required
            />
            <input
              className="input"
              value={sectionForm.name}
              onChange={(event) =>
                setSectionForm({ ...sectionForm, name: event.target.value })
              }
              placeholder="Section name"
            />
            <input
              className="input"
              type="number"
              value={sectionForm.order_in_line}
              onChange={(event) =>
                setSectionForm({
                  ...sectionForm,
                  order_in_line: event.target.value
                })
              }
              placeholder="Order in line"
            />
            <input
              className="input"
              value={sectionForm.type}
              onChange={(event) =>
                setSectionForm({ ...sectionForm, type: event.target.value })
              }
              placeholder="Type"
            />
            <button className="button" type="submit">
              Create Section
            </button>
          </form>
          </SectionTab>
        </div>
      ) : null}

      {activeTab === "sensors" ? (
        <div className="card-grid">
          <SensorTab>
          <div className="form-grid">
            <input
              className="input"
              value={sensorLineId}
              onChange={(event) => setSensorLineId(event.target.value)}
              placeholder="Line ID to list sensors"
            />
          </div>
          {sensorsState.loading ? (
            <p className="muted">Loading sensors...</p>
          ) : sensorsState.error ? (
            <p className="error">Failed to load sensors.</p>
          ) : (
            <DataTable
              rows={sensors}
              columns={[
                { key: "sensor_id", label: "ID" },
                { key: "section_id", label: "Section" },
                { key: "sensor_type", label: "Type" },
                { key: "name", label: "Name" },
                { key: "status", label: "Status" }
              ]}
              emptyMessage="No sensors available."
            />
          )}
          <form className="form-grid" onSubmit={handleCreateSensor}>
            <input
              className="input"
              value={sensorForm.section_id}
              onChange={(event) =>
                setSensorForm({ ...sensorForm, section_id: event.target.value })
              }
              placeholder="Section ID"
              required
            />
            <input
              className="input"
              value={sensorForm.equipment_id}
              onChange={(event) =>
                setSensorForm({ ...sensorForm, equipment_id: event.target.value })
              }
              placeholder="Equipment ID (optional)"
            />
            <input
              className="input"
              value={sensorForm.sensor_type}
              onChange={(event) =>
                setSensorForm({ ...sensorForm, sensor_type: event.target.value })
              }
              placeholder="Sensor type"
            />
            <input
              className="input"
              value={sensorForm.name}
              onChange={(event) =>
                setSensorForm({ ...sensorForm, name: event.target.value })
              }
              placeholder="Sensor name"
            />
            <input
              className="input"
              value={sensorForm.status}
              onChange={(event) =>
                setSensorForm({ ...sensorForm, status: event.target.value })
              }
              placeholder="Status"
            />
            <button className="button" type="submit">
              Create Sensor
            </button>
          </form>
          </SensorTab>
        </div>
      ) : null}

      {activeTab === "thresholds" ? (
        <ThresholdForm>
          {thresholdsState.loading ? (
            <p className="muted">Loading thresholds...</p>
          ) : thresholdsState.error ? (
            <p className="error">Failed to load thresholds.</p>
          ) : thresholds.length ? (
            <ul className="placeholder-list">
              {thresholds.map((threshold) => (
                <li key={threshold.config_key}>
                  {threshold.config_key} = {threshold.config_value}
                </li>
              ))}
            </ul>
          ) : (
            <p className="muted">No thresholds configured.</p>
          )}
          <form className="form-grid" onSubmit={handleUpdateThreshold}>
            <select
              className="input"
              value={thresholdKey}
              onChange={(event) => setThresholdKey(event.target.value)}
              required
            >
              <option value="">Select config key</option>
              {thresholdOptions.map((key) => (
                <option key={key} value={key}>
                  {key}
                </option>
              ))}
            </select>
            <input
              className="input"
              value={thresholdValue}
              onChange={(event) => setThresholdValue(event.target.value)}
              placeholder="Value"
              required
            />
            <input
              className="input"
              value={thresholdDescription}
              onChange={(event) => setThresholdDescription(event.target.value)}
              placeholder="Description"
            />
            <button className="button" type="submit">
              Update Threshold
            </button>
          </form>
        </ThresholdForm>
      ) : null}
    </section>
  );
};

export default Settings;
