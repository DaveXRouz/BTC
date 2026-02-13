import { lazy, Suspense, useEffect } from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Layout } from "./components/Layout";
import { ErrorBoundary } from "./components/common/ErrorBoundary";
import { PageLoadingFallback } from "./components/common/PageLoadingFallback";
import "./styles/rtl.css";
import "./styles/animations.css";

const Dashboard = lazy(() => import("./pages/Dashboard"));
const Oracle = lazy(() => import("./pages/Oracle"));
const ReadingHistory = lazy(() => import("./pages/ReadingHistory"));
const Settings = lazy(() => import("./pages/Settings"));
const Admin = lazy(() => import("./pages/Admin"));
const AdminUsers = lazy(() => import("./pages/AdminUsers"));
const AdminProfiles = lazy(() => import("./pages/AdminProfiles"));
const Scanner = lazy(() => import("./pages/Scanner"));
const SharedReading = lazy(() => import("./pages/SharedReading"));
const AdminMonitoring = lazy(() => import("./pages/AdminMonitoring"));

export default function App() {
  const { i18n } = useTranslation();

  useEffect(() => {
    const dir = i18n.language === "fa" ? "rtl" : "ltr";
    document.documentElement.dir = dir;
    document.documentElement.lang = i18n.language;
  }, [i18n.language]);

  return (
    <Suspense fallback={<PageLoadingFallback />}>
      <Routes>
        {/* Public share page — no layout/sidebar */}
        <Route
          path="/share/:token"
          element={
            <ErrorBoundary>
              <SharedReading />
            </ErrorBoundary>
          }
        />

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
                <Admin />
              </ErrorBoundary>
            }
          >
            <Route index element={<Navigate to="/admin/users" replace />} />
            <Route path="users" element={<AdminUsers />} />
            <Route path="profiles" element={<AdminProfiles />} />
            <Route path="monitoring" element={<AdminMonitoring />} />
          </Route>
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
