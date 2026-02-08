import { Outlet, NavLink } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { LanguageToggle } from "./LanguageToggle";

const navItems = [
  { path: "/dashboard", labelKey: "nav.dashboard" },
  { path: "/scanner", labelKey: "nav.scanner" },
  { path: "/oracle", labelKey: "nav.oracle" },
  { path: "/vault", labelKey: "nav.vault" },
  { path: "/learning", labelKey: "nav.learning" },
  { path: "/settings", labelKey: "nav.settings" },
];

export function Layout() {
  const { t } = useTranslation();

  return (
    <div className="flex min-h-screen bg-nps-bg">
      {/* Sidebar */}
      <nav className="w-64 border-r rtl:border-r-0 rtl:border-l border-nps-border bg-nps-bg-card flex flex-col">
        <div className="p-4 border-b border-nps-border flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-nps-gold">NPS V4</h1>
            <p className="text-xs text-nps-text-dim">
              Numerology Puzzle Solver
            </p>
          </div>
          <LanguageToggle />
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
              {t(item.labelKey)}
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
