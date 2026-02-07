import { Outlet, NavLink } from "react-router-dom";

const navItems = [
  { path: "/dashboard", label: "Dashboard", icon: "grid" },
  { path: "/scanner", label: "Scanner", icon: "search" },
  { path: "/oracle", label: "Oracle", icon: "sparkles" },
  { path: "/vault", label: "Vault", icon: "lock" },
  { path: "/learning", label: "Learning", icon: "brain" },
  { path: "/settings", label: "Settings", icon: "cog" },
];

export function Layout() {
  return (
    <div className="flex min-h-screen bg-nps-bg">
      {/* Sidebar */}
      <nav className="w-64 border-r border-nps-border bg-nps-bg-card flex flex-col">
        <div className="p-4 border-b border-nps-border">
          <h1 className="text-xl font-bold text-nps-gold">NPS V4</h1>
          <p className="text-xs text-nps-text-dim">Numerology Puzzle Solver</p>
        </div>
        <div className="flex-1 py-4">
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `block px-4 py-2 mx-2 rounded text-sm ${
                  isActive
                    ? "bg-nps-bg-button text-nps-text-bright"
                    : "text-nps-text-dim hover:bg-nps-bg-hover hover:text-nps-text"
                }`
              }
            >
              {item.label}
            </NavLink>
          ))}
        </div>
        {/* TODO: Health status indicator */}
        {/* TODO: User info / logout */}
      </nav>

      {/* Main content */}
      <main className="flex-1 p-6 overflow-auto">
        <Outlet />
      </main>
    </div>
  );
}
