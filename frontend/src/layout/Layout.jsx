import { NavLink, Outlet } from "react-router-dom";

const navItems = [
  { to: "/", label: "HQ Dashboard" },
  { to: "/centers", label: "Centers" },
  { to: "/bottlenecks", label: "Bottlenecks" },
  { to: "/costs", label: "Cost and Loss" },
  { to: "/performance", label: "Performance" },
  { to: "/sensors", label: "Sensors" },
  { to: "/kpi", label: "KPI Report" },
  { to: "/settings", label: "Settings" }
];

const Layout = () => (
  <div className="app-shell">
    <header className="app-header">
      <h1>Azure Logistics Dashboard</h1>
      <span>FastAPI + Vite</span>
    </header>
    <div className="app-body">
      <nav className="app-nav">
        <div className="nav-list">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                isActive ? "nav-link active" : "nav-link"
              }
            >
              {item.label}
            </NavLink>
          ))}
        </div>
      </nav>
      <main className="app-content">
        <Outlet />
      </main>
    </div>
  </div>
);

export default Layout;
