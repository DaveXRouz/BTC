import { lazy, Suspense, useEffect } from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Layout } from "./components/Layout";
import { ErrorBoundary } from "./components/common/ErrorBoundary";
import "./styles/rtl.css";

const Dashboard = lazy(() => import("./pages/Dashboard"));
const Oracle = lazy(() => import("./pages/Oracle"));
const ReadingHistory = lazy(() => import("./pages/ReadingHistory"));
const Settings = lazy(() => import("./pages/Settings"));
const AdminPanel = lazy(() => import("./pages/AdminPanel"));
const Scanner = lazy(() => import("./pages/Scanner"));

function LoadingSpinner() {
  return (
    <div className="flex items-center justify-center h-64">
      <div className="w-8 h-8 border-2 border-[var(--nps-accent)] border-t-transparent rounded-full animate-spin" />
    </div>
  );
}

export default function App() {
  const { i18n } = useTranslation();

  useEffect(() => {
    const dir = i18n.language === "fa" ? "rtl" : "ltr";
    document.documentElement.dir = dir;
    document.documentElement.lang = i18n.language;
  }, [i18n.language]);

  return (
    <Suspense fallback={<LoadingSpinner />}>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route
            path="/dashboard"
            element={
              <ErrorBoundary>
                <Dashboard />
              </ErrorBoundary>
            }
          />
          <Route
            path="/oracle"
            element={
              <ErrorBoundary>
                <Oracle />
              </ErrorBoundary>
            }
          />
          <Route
            path="/history"
            element={
              <ErrorBoundary>
                <ReadingHistory />
              </ErrorBoundary>
            }
          />
          <Route
            path="/settings"
            element={
              <ErrorBoundary>
                <Settings />
              </ErrorBoundary>
            }
          />
          <Route
            path="/admin"
            element={
              <ErrorBoundary>
                <AdminPanel />
              </ErrorBoundary>
            }
          />
          <Route
            path="/scanner"
            element={
              <ErrorBoundary>
                <Scanner />
              </ErrorBoundary>
            }
          />
        </Route>
      </Routes>
    </Suspense>
  );
}
