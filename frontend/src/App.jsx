import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { FilterProvider } from "./context/FilterContext.jsx";
import Layout from "./layout/Layout.jsx";
import BottleneckAnalytics from "./pages/BottleneckAnalytics.jsx";
import CenterList from "./pages/CenterList.jsx";
import DashboardCenter from "./pages/DashboardCenter.jsx";
import DashboardHQ from "./pages/DashboardHQ.jsx";
import KPIReport from "./pages/KPIReport.jsx";
import LineAnalytics from "./pages/LineAnalytics.jsx";
import PerformanceDashboard from "./pages/PerformanceDashboard.jsx";
import SensorMonitoring from "./pages/SensorMonitoring.jsx";
import Settings from "./pages/Settings.jsx";

const App = () => (
  <BrowserRouter>
    <FilterProvider>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<DashboardHQ />} />
          <Route path="centers" element={<CenterList />} />
          <Route path="centers/:centerId" element={<DashboardCenter />} />
          <Route path="lines/:lineId" element={<LineAnalytics />} />
          <Route path="bottlenecks" element={<BottleneckAnalytics />} />
          <Route path="kpi" element={<KPIReport />} />
          <Route path="performance" element={<PerformanceDashboard />} />
          <Route path="sensors" element={<SensorMonitoring />} />
          <Route path="settings" element={<Settings />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </FilterProvider>
  </BrowserRouter>
);

export default App;
