import { useState, useEffect } from "react";
import { Outlet, useLocation } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { PageTransition } from "./common/PageTransition";
import { Navigation } from "./Navigation";
import { LanguageToggle } from "./LanguageToggle";
import { ThemeToggle } from "./ThemeToggle";
import { MobileNav } from "./MobileNav";
import { SkipNavLink } from "./SkipNavLink";
import { OfflineBanner } from "./common/OfflineBanner";
import { ToastContainer } from "./common/Toast";
import { useWebSocketConnection } from "@/hooks/useWebSocket";

export function Layout() {
  const { t } = useTranslation();
  useWebSocketConnection();
  const location = useLocation();

  const [sidebarCollapsed, setSidebarCollapsed] = useState(() => {
    if (typeof window === "undefined") return false;
    return localStorage.getItem("nps_sidebar_collapsed") === "true";
  });
  const [drawerOpen, setDrawerOpen] = useState(false);

  useEffect(() => {
    localStorage.setItem("nps_sidebar_collapsed", String(sidebarCollapsed));
  }, [sidebarCollapsed]);

  return (
    <>
      <OfflineBanner />
      <div className="flex min-h-screen bg-[var(--nps-bg)]">
        <SkipNavLink />
        {/* Desktop sidebar — hidden below lg */}
        <aside
          className={`
          hidden lg:flex flex-col
          ${sidebarCollapsed ? "lg:w-16" : "lg:w-64"}
          bg-[var(--nps-bg-sidebar)] border-e border-[var(--nps-border)]
          transition-all duration-200
        `}
        >
          {/* Logo */}
          <div className="p-4 border-b border-[var(--nps-border)] flex items-center gap-2">
            <span className="text-xl font-bold text-[var(--nps-accent)]">
              NPS
            </span>
            {!sidebarCollapsed && (
              <span className="text-xs text-[var(--nps-text-dim)]">
                {t("layout.app_tagline")}
              </span>
            )}
          </div>

          {/* Navigation */}
          <Navigation collapsed={sidebarCollapsed} isAdmin={false} />

          {/* Collapse toggle */}
          <button
            onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
            className="flex items-center justify-center p-3 border-t border-[var(--nps-border)] text-[var(--nps-text-dim)] hover:text-[var(--nps-text)] transition-colors"
            aria-label={
              sidebarCollapsed
                ? t("layout.sidebar_expand")
                : t("layout.sidebar_collapse")
            }
          >
            <svg
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth={1.5}
              className={`transition-transform ${sidebarCollapsed ? "rotate-180 rtl:rotate-0" : "rtl:rotate-180"}`}
            >
              <polyline points="15 18 9 12 15 6" />
            </svg>
          </button>
        </aside>

        {/* Mobile drawer — visible below lg */}
        <MobileNav isOpen={drawerOpen} onClose={() => setDrawerOpen(false)} />

        {/* Main area */}
        <div className="flex-1 flex flex-col min-w-0">
          {/* Top bar */}
          <header className="h-14 bg-[var(--nps-bg-card)] border-b border-[var(--nps-border)] flex items-center justify-between px-4">
            {/* Mobile hamburger — visible below lg */}
            <button
              onClick={() => setDrawerOpen(true)}
              className="lg:hidden flex items-center justify-center min-w-[44px] min-h-[44px] text-[var(--nps-text-dim)] hover:text-[var(--nps-text)]"
              aria-label={t("layout.mobile_menu")}
            >
              <svg
                width="20"
                height="20"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth={1.5}
              >
                <line x1="3" y1="6" x2="21" y2="6" />
                <line x1="3" y1="12" x2="21" y2="12" />
                <line x1="3" y1="18" x2="21" y2="18" />
              </svg>
            </button>

            <div className="hidden lg:block" />

            {/* Right toggles — hidden on mobile (they're in drawer) */}
            <div className="hidden lg:flex items-center gap-2">
              <LanguageToggle />
              <ThemeToggle />
            </div>

            {/* NPS logo on mobile header right side */}
            <span className="lg:hidden text-sm font-bold text-[var(--nps-accent)]">
              NPS
            </span>
          </header>

          {/* Content */}
          <main
            id="main-content"
            className="flex-1 p-4 lg:p-6 overflow-auto"
            tabIndex={-1}
          >
            <PageTransition locationKey={location.key}>
              <Outlet />
            </PageTransition>
          </main>

          {/* Footer */}
          <footer className="px-4 py-2 border-t border-[var(--nps-border)] text-center text-xs text-[var(--nps-text-dim)]">
            {t("layout.footer_copyright")} &middot; {t("layout.version")}
          </footer>
        </div>
      </div>
      <ToastContainer />
    </>
  );
}
