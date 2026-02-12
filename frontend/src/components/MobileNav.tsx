import { useEffect, useRef } from "react";
import { NavLink } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useDirection } from "@/hooks/useDirection";
import { LanguageToggle } from "./LanguageToggle";
import { ThemeToggle } from "./ThemeToggle";

interface NavItem {
  path: string;
  labelKey: string;
  disabled?: boolean;
}

const NAV_ITEMS: NavItem[] = [
  { path: "/dashboard", labelKey: "nav.dashboard" },
  { path: "/oracle", labelKey: "nav.oracle" },
  { path: "/history", labelKey: "nav.history" },
  { path: "/settings", labelKey: "nav.settings" },
  { path: "/scanner", labelKey: "nav.scanner", disabled: true },
];

interface MobileNavProps {
  isOpen: boolean;
  onClose: () => void;
}

export function MobileNav({ isOpen, onClose }: MobileNavProps) {
  const { t } = useTranslation();
  const { isRTL } = useDirection();
  const drawerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!isOpen) return;
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  // Trap focus within drawer when open
  useEffect(() => {
    if (isOpen && drawerRef.current) {
      const firstFocusable = drawerRef.current.querySelector<HTMLElement>(
        "a, button, [tabindex]:not([tabindex='-1'])",
      );
      firstFocusable?.focus();
    }
  }, [isOpen]);

  return (
    <>
      {/* Backdrop */}
      <div
        className={`fixed inset-0 bg-black/50 z-40 transition-opacity duration-200 ${
          isOpen ? "opacity-100" : "opacity-0 pointer-events-none"
        }`}
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Drawer */}
      <div
        ref={drawerRef}
        role="dialog"
        aria-modal="true"
        aria-label={t("accessibility.menu_toggle")}
        className={`fixed inset-y-0 z-50 w-[280px] max-w-[calc(100vw-56px)] bg-[var(--nps-bg-sidebar)] border-e border-[var(--nps-border)] flex flex-col transition-transform duration-200 ease-in-out ${
          isRTL ? "end-0" : "start-0"
        } ${
          isOpen
            ? "translate-x-0"
            : isRTL
              ? "translate-x-full"
              : "-translate-x-full"
        }`}
      >
        {/* Header */}
        <div className="p-4 border-b border-[var(--nps-border)] flex items-center justify-between">
          <span className="text-xl font-bold text-[var(--nps-accent)]">
            NPS
          </span>
          <button
            onClick={onClose}
            className="w-10 h-10 flex items-center justify-center text-[var(--nps-text-dim)] hover:text-[var(--nps-text)] rounded-lg transition-colors"
            aria-label={t("layout.mobile_menu_close")}
          >
            <svg
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth={1.5}
            >
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>

        {/* Navigation items */}
        <nav className="flex-1 py-4 overflow-y-auto" role="navigation">
          {NAV_ITEMS.map((item) => {
            if (item.disabled) {
              return (
                <div
                  key={item.path}
                  className="flex items-center gap-3 px-4 py-3 mx-2 rounded text-sm text-[var(--nps-text-dim)] cursor-not-allowed opacity-50 min-h-[44px]"
                  title={t("layout.coming_soon")}
                >
                  <span>{t(item.labelKey)}</span>
                </div>
              );
            }

            return (
              <NavLink
                key={item.path}
                to={item.path}
                onClick={onClose}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-4 py-3 mx-2 rounded text-sm transition-colors min-h-[44px] ${
                    isActive
                      ? "bg-[var(--nps-accent)]/10 text-[var(--nps-accent)] border-s-2 border-[var(--nps-accent)]"
                      : "text-[var(--nps-text-dim)] hover:bg-[var(--nps-bg-hover)] hover:text-[var(--nps-text)]"
                  }`
                }
              >
                <span>{t(item.labelKey)}</span>
              </NavLink>
            );
          })}
        </nav>

        {/* Footer toggles */}
        <div className="p-4 border-t border-[var(--nps-border)] flex items-center gap-2">
          <LanguageToggle />
          <ThemeToggle />
        </div>
      </div>
    </>
  );
}
