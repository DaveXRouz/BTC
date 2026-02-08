import { useEffect } from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Layout } from "./components/Layout";
import { Dashboard } from "./pages/Dashboard";
import { Scanner } from "./pages/Scanner";
import { Oracle } from "./pages/Oracle";
import { Vault } from "./pages/Vault";
import { Learning } from "./pages/Learning";
import { Settings } from "./pages/Settings";

export default function App() {
  const { i18n } = useTranslation();

  useEffect(() => {
    const dir = i18n.language === "fa" ? "rtl" : "ltr";
    document.documentElement.dir = dir;
    document.documentElement.lang = i18n.language;
  }, [i18n.language]);

  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/scanner" element={<Scanner />} />
        <Route path="/oracle" element={<Oracle />} />
        <Route path="/vault" element={<Vault />} />
        <Route path="/learning" element={<Learning />} />
        <Route path="/settings" element={<Settings />} />
      </Route>
    </Routes>
  );
}
