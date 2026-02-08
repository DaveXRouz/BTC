import { useState } from "react";
import { useTranslation } from "react-i18next";
import { SummaryTab } from "./SummaryTab";
import { DetailsTab } from "./DetailsTab";
import { ReadingHistory } from "./ReadingHistory";
import { ExportButton } from "./ExportButton";
import type { ConsultationResult, ResultsTab } from "@/types";

interface ReadingResultsProps {
  result: ConsultationResult | null;
}

const TABS: ResultsTab[] = ["summary", "details", "history"];

export function ReadingResults({ result }: ReadingResultsProps) {
  const { t } = useTranslation();
  const [activeTab, setActiveTab] = useState<ResultsTab>("summary");

  const tabLabels: Record<ResultsTab, string> = {
    summary: t("oracle.tab_summary"),
    details: t("oracle.tab_details"),
    history: t("oracle.tab_history"),
  };

  return (
    <div className="space-y-3">
      {/* Tab bar + export */}
      <div className="flex items-center justify-between">
        <div className="flex gap-1" role="tablist" aria-label="Reading results">
          {TABS.map((tab) => (
            <button
              key={tab}
              type="button"
              role="tab"
              id={`tab-${tab}`}
              aria-selected={activeTab === tab}
              aria-controls={`tabpanel-${tab}`}
              onClick={() => setActiveTab(tab)}
              className={`px-3 py-1 text-xs rounded transition-colors ${
                activeTab === tab
                  ? "bg-nps-oracle-accent text-nps-bg font-medium"
                  : "text-nps-text-dim hover:text-nps-text"
              }`}
            >
              {tabLabels[tab]}
            </button>
          ))}
        </div>
        <ExportButton result={result} />
      </div>

      {/* Tab content — eagerly rendered, hidden via CSS */}
      <div
        id="tabpanel-summary"
        role="tabpanel"
        aria-labelledby="tab-summary"
        className={activeTab === "summary" ? "" : "hidden"}
      >
        <SummaryTab result={result} />
      </div>
      <div
        id="tabpanel-details"
        role="tabpanel"
        aria-labelledby="tab-details"
        className={activeTab === "details" ? "" : "hidden"}
      >
        <DetailsTab result={result} />
      </div>
      <div
        id="tabpanel-history"
        role="tabpanel"
        aria-labelledby="tab-history"
        className={activeTab === "history" ? "" : "hidden"}
      >
        <ReadingHistory />
      </div>
    </div>
  );
}
