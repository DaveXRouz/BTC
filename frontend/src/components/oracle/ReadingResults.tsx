import { useState } from "react";
import { useTranslation } from "react-i18next";
import { SummaryTab } from "./SummaryTab";
import { DetailsTab } from "./DetailsTab";
import { ReadingHistory } from "./ReadingHistory";
import { ExportButton } from "./ExportButton";
import { HeartbeatDisplay } from "./HeartbeatDisplay";
import { LocationDisplay } from "./LocationDisplay";
import { ConfidenceMeter } from "./ConfidenceMeter";
import type {
  ConsultationResult,
  ResultsTab,
  HeartbeatData,
  LocationElementData,
  ConfidenceData,
  ConfidenceBoost,
} from "@/types";

interface ReadingResultsProps {
  result: ConsultationResult | null;
  heartbeat?: HeartbeatData | null;
  location?: LocationElementData | null;
  confidence?: ConfidenceData | null;
  boosts?: ConfidenceBoost[];
}

const TABS: ResultsTab[] = ["summary", "details", "history"];

export function ReadingResults({
  result,
  heartbeat,
  location,
  confidence,
  boosts = [],
}: ReadingResultsProps) {
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
        {/* Confidence meter at top of summary */}
        {(confidence || boosts.length > 0) && (
          <div className="mb-3 p-3 bg-nps-bg-card border border-nps-border/30 rounded">
            <ConfidenceMeter confidence={confidence ?? null} boosts={boosts} />
          </div>
        )}
        <SummaryTab result={result} />
      </div>
      <div
        id="tabpanel-details"
        role="tabpanel"
        aria-labelledby="tab-details"
        className={activeTab === "details" ? "" : "hidden"}
      >
        <DetailsTab result={result} />
        {/* Heartbeat display */}
        <div className="mt-3 p-3 bg-nps-bg-card border border-nps-border/30 rounded">
          <h4 className="text-xs font-medium text-nps-text-dim mb-2">
            {t("oracle.details_heartbeat")}
          </h4>
          <HeartbeatDisplay heartbeat={heartbeat ?? null} />
        </div>
        {/* Location element display */}
        <div className="mt-3 p-3 bg-nps-bg-card border border-nps-border/30 rounded">
          <h4 className="text-xs font-medium text-nps-text-dim mb-2">
            {t("oracle.details_location_element")}
          </h4>
          <LocationDisplay location={location ?? null} />
        </div>
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
