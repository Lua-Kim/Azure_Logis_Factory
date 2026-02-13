import { useMemo } from "react";
import { useParams } from "react-router-dom";
import useAsync from "../hooks/useAsync.js";
import usePolling from "../hooks/usePolling.js";
import { useFilters } from "../context/FilterContext.jsx";
import {
  getKpi,
  getLineStatus,
  getRecentEvents
} from "../services/metricsService.js";
import Charts from "../components/dashboard/Charts.jsx";
import EventTable from "../components/dashboard/EventTable.jsx";
import KPIHeader from "../components/dashboard/KPIHeader.jsx";
import LineStatusTable from "../components/dashboard/LineStatusTable.jsx";

const DashboardCenter = () => {
  const { centerId } = useParams();
  const centerNumericId = centerId ? Number(centerId) : null;

  const { refreshMs, window } = useFilters();
  const lineState = useAsync(() => getLineStatus(), []);
  const kpiState = useAsync(() => getKpi(window, 50), [window]);
  const eventState = useAsync(() => getRecentEvents(50), []);

  usePolling(lineState.run, refreshMs);
  usePolling(() => kpiState.run(), refreshMs);
  usePolling(eventState.run, refreshMs);

  const centerKpi = useMemo(
    () =>
      (kpiState.data || []).filter(
        (item) => !centerNumericId || item.center_id === centerNumericId
      ),
    [kpiState.data, centerNumericId]
  );

  const centerEvents = useMemo(
    () =>
      (eventState.data || []).filter(
        (item) => !centerNumericId || item.center_id === centerNumericId
      ),
    [eventState.data, centerNumericId]
  );

  return (
    <section className="page">
      <p>Center-specific KPI and line status placeholder.</p>
      <div className="card-grid">
        <div className="card">
          <h2>Line Status Snapshot</h2>
          {lineState.loading ? (
            <p className="muted">Loading line status...</p>
          ) : lineState.error ? (
            <p className="error">Failed to load line status.</p>
          ) : (
            <ul className="placeholder-list">
              {(lineState.data || []).map((line) => (
                <li key={line.line_id}>
                  line {line.line_id} | {line.current_status}
                </li>
              ))}
            </ul>
          )}
        </div>
        <div className="card">
          <h2>Recent KPI</h2>
          {kpiState.loading ? (
            <p className="muted">Loading KPI...</p>
          ) : kpiState.error ? (
            <p className="error">Failed to load KPI.</p>
          ) : centerKpi.length ? (
            <ul className="placeholder-list">
              {centerKpi.slice(0, 10).map((item) => (
                <li key={`${item.window_end}-${item.line_id}`}>
                  {new Date(item.window_end).toLocaleTimeString()} | line
                  {" "}{item.line_id} | throughput {item.throughput_count}
                </li>
              ))}
            </ul>
          ) : (
            <p className="muted">No KPI data.</p>
          )}
        </div>
      </div>
      <div className="card">
        <h2>Recent Events</h2>
        {eventState.loading ? (
          <p className="muted">Loading events...</p>
        ) : eventState.error ? (
          <p className="error">Failed to load events.</p>
        ) : centerEvents.length ? (
          <ul className="placeholder-list">
            {centerEvents.slice(0, 12).map((event) => (
              <li key={event.event_id}>
                {event.event_type_code} | line {event.line_id} | section
                {" "}{event.section_id}
              </li>
            ))}
          </ul>
        ) : (
          <p className="muted">No events.</p>
        )}
      </div>
      <div className="module-grid">
        <KPIHeader
          subtitle="Center KPI summary"
          stats={[
            { label: "Center ID", value: centerId || "-" },
            { label: "KPI Rows", value: centerKpi.length },
            { label: "Events", value: centerEvents.length }
          ]}
        />
        <LineStatusTable items={lineState.data || []} />
        <EventTable items={centerEvents} />
        <Charts />
      </div>
    </section>
  );
};

export default DashboardCenter;
