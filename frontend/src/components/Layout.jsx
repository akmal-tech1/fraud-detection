import { Link, NavLink, Outlet } from "react-router-dom";

// Sidebar navigation. Phase tags identify features that are still placeholders.
const navItems = [
  { to: "/dashboard", label: "Dashboard", end: true, phase: null },
  { to: "/analyze", label: "Analyze Transaction", end: false, phase: null },
  { to: "/batch", label: "Batch Analysis", end: false, phase: null },
  { to: "/history", label: "Transaction History", end: false, phase: null },
  { to: "/model", label: "Model Performance", end: false, phase: null },
  { to: "/about", label: "About & Documentation", end: false, phase: null },
  { to: "/login", label: "Sign in", end: false, phase: null },
];

export default function Layout() {
  return (
    <div className="layout">
      <aside className="sidebar">
        <Link className="sidebar-title sidebar-brand-link" to="/">
          Fraud Risk Detection
        </Link>
        <nav className="sidebar-nav" aria-label="Main navigation">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                `nav-item${isActive ? " nav-item-active" : ""}`
              }
            >
              <span className="nav-label">{item.label}</span>
              {item.phase ? (
                <span className="nav-phase">Phase {item.phase}</span>
              ) : null}
            </NavLink>
          ))}
        </nav>
        <p className="sidebar-footer">
          Educational demo — not connected to real banking.
        </p>
      </aside>
      <main className="content">
        <Outlet />
      </main>
    </div>
  );
}
