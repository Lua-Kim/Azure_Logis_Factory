import { useEffect, useMemo, useState } from "react";
import useAsync from "../hooks/useAsync.js";
import DataTable from "../components/common/DataTable.jsx";
import CenterForm from "../components/settings/CenterForm.jsx";
import CenterList from "../components/settings/CenterList.jsx";
import LineTab from "../components/settings/LineTab.jsx";
import SectionTab from "../components/settings/SectionTab.jsx";
import SensorTab from "../components/settings/SensorTab.jsx";
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
  listZones,
  updateCenter
} from "../services/settingsService.js";

const emptyCenter = {
  center_id: null,
  name: "",
  location: "",
  status: "ACTIVE",
  opened_at: ""
};

const zoneNameOptions = ["Inbound", "Outbound", "Dock", "Sort", "Buffer"];
const zoneTypeOptions = ["RECEIVE", "SHIP", "SORT", "GENERAL", "STORAGE"];
const zoneStatusOptions = ["ACTIVE", "INACTIVE", "MAINTENANCE"];
const emptyList = [];

const Settings = () => {
  const [newCenter, setNewCenter] = useState(emptyCenter);
  const [zoneCenterId, setZoneCenterId] = useState("");
  const [lineCenterId, setLineCenterId] = useState("");
  const [lineSelectedId, setLineSelectedId] = useState("");
  const [sectionLineId, setSectionLineId] = useState("");
  const [sensorLineId, setSensorLineId] = useState("");
  const [activeTab, setActiveTab] = useState("centers");
  const [showGuide, setShowGuide] = useState(true);

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

  const resolveLineId = (line) => {
    const rawId = line?.line_id ?? line?.id;
    const parsedId = Number(rawId);
    return Number.isFinite(parsedId) ? parsedId : null;
  };

  const centersState = useAsync(() => listCenters({ page: 1, size: 50 }), []);

  const zonesState = useAsync(
    () => (zoneCenterId ? listZones(zoneCenterId) : Promise.resolve([])),
    [zoneCenterId]
  );
  const linesState = useAsync(
    () => (lineCenterId ? listLines(lineCenterId) : Promise.resolve([])),
    [lineCenterId]
  );
  const sectionsState = useAsync(
    () =>
      sectionLineId && lineCenterId
        ? listSections(sectionLineId, lineCenterId)
        : Promise.resolve([]),
    [sectionLineId, lineCenterId]
  );
  const sensorsState = useAsync(
    () =>
      sensorLineId && lineCenterId
        ? listSensors(sensorLineId, lineCenterId)
        : Promise.resolve([]),
    [sensorLineId, lineCenterId]
  );

  const rawCenters = centersState.data?.items ?? emptyList;
  const centers = useMemo(
    () =>
      rawCenters
        .map((center) => {
          const rawId = center.center_id ?? center.id;
          const parsedId = Number(rawId);
          return {
            ...center,
            center_id: Number.isFinite(parsedId) ? parsedId : null
          };
        })
        .filter((center) => center.center_id !== null),
    [rawCenters]
  );

  const zones = zonesState.data || [];
  const lines = linesState.data || [];
  const sections = sectionsState.data || [];
  const sensors = sensorsState.data || [];

  const centerIdsKey = useMemo(
    () => centers.map((center) => center.center_id).join(","),
    [centers]
  );

  const statsState = useAsync(async () => {
    if (!centers.length) {
      return { centers: 0, zones: 0, lines: 0, sections: 0, sensors: 0 };
    }

    const selectedCenterId = newCenter.center_id
      ? Number(newCenter.center_id)
      : null;
    const centerIds = selectedCenterId
      ? [selectedCenterId]
      : centers.map((center) => center.center_id);

    let zonesTotal = 0;
    let linesTotal = 0;
    let sectionsTotal = 0;
    let sensorsTotal = 0;

    for (const centerId of centerIds) {
      const [centerZones, centerLines] = await Promise.all([
        listZones(centerId),
        listLines(centerId)
      ]);

      zonesTotal += centerZones.length;
      linesTotal += centerLines.length;

      const perLineTotals = await Promise.all(
        centerLines.map(async (line) => {
          const lineId = resolveLineId(line);
          if (lineId === null) {
            return { sections: 0, sensors: 0 };
          }
          const [lineSections, lineSensors] = await Promise.all([
            listSections(lineId, centerId),
            listSensors(lineId, centerId)
          ]);
          return {
            sections: lineSections.length,
            sensors: lineSensors.length
          };
        })
      );

      sectionsTotal += perLineTotals.reduce(
        (sum, item) => sum + item.sections,
        0
      );
      sensorsTotal += perLineTotals.reduce(
        (sum, item) => sum + item.sensors,
        0
      );
    }

    return {
      centers: selectedCenterId ? 1 : centers.length,
      zones: zonesTotal,
      lines: linesTotal,
      sections: sectionsTotal,
      sensors: sensorsTotal
    };
  }, [centerIdsKey, newCenter.center_id]);

  const selectedCenterName = newCenter.center_id
    ? centers.find((center) => center.center_id === Number(newCenter.center_id))
        ?.name || `Center ${newCenter.center_id}`
    : null;

  useEffect(() => {
    if (centers.length > 0) {
      if (!zoneCenterId) {
        setZoneCenterId(String(centers[0].center_id));
      }
      if (!lineCenterId) {
        setLineCenterId(String(centers[0].center_id));
      }
    }
  }, [centers, zoneCenterId, lineCenterId]);

  useEffect(() => {
    if (lineCenterId) {
      linesState.run();
      setLineForm((prev) => ({ ...prev, center_id: lineCenterId }));
      setLineSelectedId("");
    }
  }, [lineCenterId]);

  useEffect(() => {
    if (lines.length && !sectionLineId) {
      const lineId = resolveLineId(lines[0]);
      if (lineId !== null) {
        setSectionLineId(String(lineId));
      }
    }
    if (lines.length && !sensorLineId) {
      const lineId = resolveLineId(lines[0]);
      if (lineId !== null) {
        setSensorLineId(String(lineId));
      }
    }
  }, [lines, sectionLineId, sensorLineId]);

  useEffect(() => {
    if (zoneCenterId) {
      setZoneForm((prev) => ({ ...prev, center_id: zoneCenterId }));
    }
  }, [zoneCenterId]);

  const handleCreateCenter = async (event) => {
    event.preventDefault();
    if (newCenter.center_id) {
      const payload = Object.fromEntries(
        Object.entries(newCenter).filter(
          ([key, value]) => key !== "center_id" && value !== "" && value !== null
        )
      );
      await updateCenter(newCenter.center_id, payload);
    } else {
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
    setZoneCenterId(String(row.center_id));
    setLineCenterId(String(row.center_id));
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
    const resolvedCenterId = zoneCenterId || zoneForm.center_id;
    if (!resolvedCenterId) {
      alert("센터를 먼저 선택해주세요");
      return;
    }
    await createZone({
      ...zoneForm,
      center_id: Number(resolvedCenterId)
    });
    setZoneForm({ ...zoneForm, name: "", type: "" });
    zonesState.run();
  };

  const handleCreateLine = async (event) => {
    event.preventDefault();
    const resolvedCenterId = lineCenterId || lineForm.center_id;
    if (!resolvedCenterId) {
      alert("센터를 먼저 선택해주세요");
      return;
    }
    await createLine(
      {
        ...lineForm,
        center_id: Number(resolvedCenterId),
        rail_length_m: Number(lineForm.rail_length_m),
        section_count: Number(lineForm.section_count)
      },
      Number(resolvedCenterId)
    );
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
    await createSection(
      {
        ...sectionForm,
        line_id: Number(sectionForm.line_id || sectionLineId),
        order_in_line: sectionForm.order_in_line
          ? Number(sectionForm.order_in_line)
          : null
      },
      Number(lineCenterId)
    );
    setSectionForm({ ...sectionForm, name: "", order_in_line: "", type: "" });
    sectionsState.run();
  };

  const handleCreateSensor = async (event) => {
    event.preventDefault();
    await createSensor(
      {
        ...sensorForm,
        section_id: Number(sensorForm.section_id),
        equipment_id: sensorForm.equipment_id
          ? Number(sensorForm.equipment_id)
          : null
      },
      Number(lineCenterId)
    );
    setSensorForm({
      ...sensorForm,
      equipment_id: "",
      sensor_type: "",
      name: ""
    });
    sensorsState.run();
  };

  return (
    <section className="page">
      <p>System configuration and master data management.</p>
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
            <p className="muted">센터/라인/섹션/센서 마스터를 생성·수정합니다.</p>
            <p className="muted">탭별로 설정 항목이 분리되어 있습니다.</p>
          </div>
        </div>
      ) : null}

      <div className="card-grid">
        <div className="card">
          <h2>Current Configuration</h2>
          <div className="stat-block stat-row">
            <div>
              <span className="stat-label">Centers</span>
              <span className="stat-value">
                {selectedCenterName || statsState.data?.centers || 0}
              </span>
            </div>
            <div>
              <span className="stat-label">Zones (selected center)</span>
              <span className="stat-value">{statsState.data?.zones ?? 0}</span>
            </div>
            <div>
              <span className="stat-label">Lines (selected center)</span>
              <span className="stat-value">{statsState.data?.lines ?? 0}</span>
            </div>
            <div>
              <span className="stat-label">Sections (selected center)</span>
              <span className="stat-value">{statsState.data?.sections ?? 0}</span>
            </div>
            <div>
              <span className="stat-label">Sensors (selected center)</span>
              <span className="stat-value">{statsState.data?.sensors ?? 0}</span>
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
                        onClick={(event) => {
                          event.stopPropagation();
                          if (confirm(`정말 "${row.name}" 센터를 삭제하시겠습니까?`)) {
                            deleteCenter(row.center_id)
                              .then(() => {
                                centersState.run();
                                setNewCenter(emptyCenter);
                              })
                              .catch((err) => {
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
              {newCenter.center_id ? (
                <button className="button" type="button" onClick={handleClearForm}>
                  Clear
                </button>
              ) : null}
            </form>
          </CenterForm>
        </div>
      ) : null}

      {activeTab === "zones" ? (
        <div className="card-grid">
          <ZoneTab>
            <div className="stack-md">
              <div className="form-grid">
                <select
                  className="input"
                  value={zoneCenterId}
                  onChange={(event) => setZoneCenterId(event.target.value)}
                >
                  <option value="">센터 선택</option>
                  {centers.map((center) => (
                    <option key={center.center_id} value={center.center_id}>
                      {center.name || `Center ${center.center_id}`}
                    </option>
                  ))}
                </select>
              </div>

              <form className="form-grid" onSubmit={handleCreateZone}>
                <input
                  className="input"
                  list="zone-name-options"
                  value={zoneForm.name}
                  onChange={(event) =>
                    setZoneForm({ ...zoneForm, name: event.target.value })
                  }
                  placeholder="Zone name"
                  required
                />
                <datalist id="zone-name-options">
                  {zoneNameOptions.map((option) => (
                    <option key={option} value={option} />
                  ))}
                </datalist>
                <input
                  className="input"
                  list="zone-type-options"
                  value={zoneForm.type}
                  onChange={(event) =>
                    setZoneForm({ ...zoneForm, type: event.target.value })
                  }
                  placeholder="Type"
                  required
                />
                <datalist id="zone-type-options">
                  {zoneTypeOptions.map((option) => (
                    <option key={option} value={option} />
                  ))}
                </datalist>
                <select
                  className="input"
                  value={zoneForm.status}
                  onChange={(event) =>
                    setZoneForm({ ...zoneForm, status: event.target.value })
                  }
                  required
                >
                  <option value="">Status</option>
                  {zoneStatusOptions.map((option) => (
                    <option key={option} value={option}>
                      {option}
                    </option>
                  ))}
                </select>
                <button className="button" type="submit" disabled={!zoneCenterId}>
                  Create Zone
                </button>
              </form>
            </div>
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
                <option value="">센터 선택</option>
                {centers.map((center) => (
                  <option key={center.center_id} value={center.center_id}>
                    {center.name || `Center ${center.center_id}`}
                  </option>
                ))}
              </select>
              <select
                className="input"
                value={lineSelectedId}
                onChange={(event) => setLineSelectedId(event.target.value)}
                disabled={!lineCenterId || linesState.loading}
              >
                <option value="">라인 선택</option>
                {(linesState.data || []).map((line) => {
                  const lineId = resolveLineId(line);
                  if (lineId === null) {
                    return null;
                  }
                  return (
                    <option key={lineId} value={lineId}>
                      {line.name || "Line"} ({lineId})
                    </option>
                  );
                })}
              </select>
              {lineCenterId ? (
                <p className="muted">
                  선택된 센터: {centers.find((c) => c.center_id === Number(lineCenterId))?.name || lineCenterId}
                </p>
              ) : (
                <p className="muted">센터를 먼저 선택하세요.</p>
              )}
            </div>
            <form className="form-grid" onSubmit={handleCreateLine}>
              <input
                className="input"
                list="line-name-options"
                value={lineForm.name}
                onChange={(event) =>
                  setLineForm({ ...lineForm, name: event.target.value })
                }
                placeholder="라인 이름"
              />
              <datalist id="line-name-options">
                <option value="Line A" />
                <option value="Line B" />
                <option value="Line C" />
                <option value="Line D" />
              </datalist>
              <input
                className="input"
                list="line-type-options"
                value={lineForm.type}
                onChange={(event) =>
                  setLineForm({ ...lineForm, type: event.target.value })
                }
                placeholder="라인 타입"
              />
              <datalist id="line-type-options">
                <option value="MAIN" />
                <option value="SUB" />
                <option value="SORT" />
                <option value="TRANSFER" />
              </datalist>
              <input
                className="input"
                value={lineForm.status}
                onChange={(event) =>
                  setLineForm({ ...lineForm, status: event.target.value })
                }
                placeholder="상태"
              />
              <input
                className="input"
                type="number"
                value={lineForm.rail_length_m}
                onChange={(event) =>
                  setLineForm({ ...lineForm, rail_length_m: event.target.value })
                }
                placeholder="레일 길이 (m)"
                required
              />
              <input
                className="input"
                type="number"
                value={lineForm.section_count}
                onChange={(event) =>
                  setLineForm({ ...lineForm, section_count: event.target.value })
                }
                placeholder="섹션 개수"
                required
              />
              <button className="button" type="submit" disabled={!lineCenterId}>
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
              <select
                className="input"
                value={sectionLineId}
                onChange={(event) => setSectionLineId(event.target.value)}
              >
                <option value="">Line ID to list sections</option>
                {(linesState.data || []).map((line) => {
                  const lineId = resolveLineId(line);
                  if (lineId === null) {
                    return null;
                  }
                  return (
                    <option key={lineId} value={lineId}>
                      {line.name || "Line"} ({lineId})
                    </option>
                  );
                })}
              </select>
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
              <select
                className="input"
                value={sectionForm.line_id}
                onChange={(event) =>
                  setSectionForm({ ...sectionForm, line_id: event.target.value })
                }
                required
              >
                <option value="">Line ID</option>
                {(linesState.data || []).map((line) => {
                  const lineId = resolveLineId(line);
                  if (lineId === null) {
                    return null;
                  }
                  return (
                    <option key={lineId} value={lineId}>
                      {line.name || "Line"} ({lineId})
                    </option>
                  );
                })}
              </select>
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
              <button className="button" type="submit" disabled={!lineCenterId}>
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
              <select
                className="input"
                value={sensorLineId}
                onChange={(event) => setSensorLineId(event.target.value)}
              >
                <option value="">Line ID to list sensors</option>
                {(linesState.data || []).map((line) => {
                  const lineId = resolveLineId(line);
                  if (lineId === null) {
                    return null;
                  }
                  return (
                    <option key={lineId} value={lineId}>
                      {line.name || "Line"} ({lineId})
                    </option>
                  );
                })}
              </select>
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
              <button className="button" type="submit" disabled={!lineCenterId}>
                Create Sensor
              </button>
            </form>
          </SensorTab>
        </div>
      ) : null}
    </section>
  );
};

export default Settings;
