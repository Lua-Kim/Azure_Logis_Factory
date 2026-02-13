import { useFilters } from "../context/FilterContext.jsx";

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
        <input
          className="input"
          value={centerId}
          onChange={(event) => setCenterId(event.target.value)}
          placeholder="e.g. 1"
        />
      </label>
      <label className="filter-item">
        Line ID
        <input
          className="input"
          value={lineId}
          onChange={(event) => setLineId(event.target.value)}
          placeholder="e.g. 10"
        />
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
