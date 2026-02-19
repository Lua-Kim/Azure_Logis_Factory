import { useState, useEffect } from "react";
import { useFilters } from "../context/FilterContext.jsx";
import { getLineStatus } from "../services/metricsService.js";

const FilterBar = () => {
  const {
    window,
    centerId,
    lineId,
    refreshMs,
    wsEnabled,
    setWindow,
    setCenterId,
    setLineId,
    setRefreshMs,
    setWsEnabled
  } = useFilters();

  const [lineList, setLineList] = useState([]);
  const [centerList, setCenterList] = useState([]);

  useEffect(() => {
    getLineStatus().then(data => {
      if (Array.isArray(data)) {
        setLineList(data);
        const uniqueCenters = [...new Set(data.map(l => l.center_id))];
        setCenterList(uniqueCenters);
      }
    });
  }, []);

  const filteredLines = centerId ? lineList.filter(l => l.center_id === Number(centerId)) : lineList;

  return (
    <div className="filter-bar">
      <label className="filter-item">
        Window
        <select
          className="input"
          value={window}
          onChange={(event) => setWindow(event.target.value)}
        >
          <option value="5m">5m</option>
          <option value="1h">1h</option>
          <option value="24h">24h</option>
        </select>
      </label>
      <label className="filter-item">
        Center ID
        <select
          className="input"
          value={centerId}
          onChange={(event) => {
            setCenterId(event.target.value);
            setLineId(""); // Reset line ID when center changes
          }}
        >
          <option value="">All Centers</option>
          {centerList.map(cid => (
            <option key={cid} value={cid}>{cid}</option>
          ))}
        </select>
      </label>
      <label className="filter-item">
        Line ID
        <select
          className="input"
          value={lineId}
          onChange={(event) => setLineId(event.target.value)}
        >
          <option value="">All Lines</option>
          {filteredLines.map(line => (
            <option key={line.id} value={line.id}>{line.name}</option>
          ))}
        </select>
      </label>
      <label className="filter-item">
        Refresh
        <select
          className="input"
          value={refreshMs}
          onChange={(event) => setRefreshMs(Number(event.target.value))}
        >
          <option value={0}>Off</option>
          <option value={5000}>5s</option>
          <option value={15000}>15s</option>
        </select>
      </label>
      <label className="filter-item">
        Live WS
        <input
          className="toggle"
          type="checkbox"
          checked={wsEnabled}
          onChange={(event) => setWsEnabled(event.target.checked)}
        />
      </label>
    </div>
  );
};

export default FilterBar;
