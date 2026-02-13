import { createContext, useContext, useMemo, useState } from "react";

const FilterContext = createContext(null);

const FilterProvider = ({ children }) => {
  const [window, setWindow] = useState("5m");
  const [centerId, setCenterId] = useState("");
  const [lineId, setLineId] = useState("");
  const [refreshMs, setRefreshMs] = useState(5000);
  const [wsEnabled, setWsEnabled] = useState(true);

  const value = useMemo(
    () => ({
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
    }),
    [window, centerId, lineId, refreshMs, wsEnabled]
  );

  return (
    <FilterContext.Provider value={value}>{children}</FilterContext.Provider>
  );
};

const useFilters = () => {
  const context = useContext(FilterContext);
  if (!context) {
    throw new Error("useFilters must be used within FilterProvider");
  }
  return context;
};

export { FilterProvider, useFilters };
