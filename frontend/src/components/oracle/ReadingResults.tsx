import { useState, useRef } from "react";
import { useTranslation } from "react-i18next";
import { useArrowNavigation } from "@/hooks/useArrowNavigation";
import { SummaryTab } from "./SummaryTab";
import { DetailsTab } from "./DetailsTab";
import { ReadingHistory } from "./ReadingHistory";
import { ExportButton } from "./ExportButton";
import { ShareButton } from "./ShareButton";
import { HeartbeatDisplay } from "./HeartbeatDisplay";
import { LocationDisplay } from "./LocationDisplay";
import { ConfidenceMeter } from "./ConfidenceMeter";
import { ReadingFeedback } from "./ReadingFeedback";
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
  readingId?: number | null;
  heartbeat?: HeartbeatData | null;
  location?: LocationElementData | null;
  confidence?: ConfidenceData | null;
  boosts?: ConfidenceBoost[];
}

const TABS: ResultsTab[] = ["summary", "details", "history"];

export function ReadingResults({
  result,
  readingId,
  heartbeat,
  location,
  confidence,
  boosts = [],
}: ReadingResultsProps) {
  const { t } = useTranslation();
  const [activeTab, setActiveTab] = useState<ResultsTab>("summary");
  const tablistRef = useRef<HTMLDivElement>(null);
  const { handleKeyDown } = useArrowNavigation(tablistRef);

  const tabLabels: Record<ResultsTab, string> = {
    summary: t("oracle.tab_summary"),
    details: t("oracle.tab_details"),
    history: t("oracle.tab_history"),
  };

  return (
    <div className="space-y-3">
      {/* Tab bar + export */}
      <div className="flex items-center justify-between gap-2">
        <div
          ref={tablistRef}
          className="flex gap-1 overflow-x-auto"
          role="tablist"
          aria-label="Reading results"
          onKeyDown={handleKeyDown}
        >
          {TABS.map((tab) => (
            <button
              key={tab}
              type="button"
              role="tab"
              id={`tab-${tab}`}
              aria-selected={activeTab === tab}
              aria-controls={`tabpanel-${tab}`}
              tabIndex={activeTab === tab ? 0 : -1}
              onClick={() => setActiveTab(tab)}
              className={`px-3 py-1 min-h-[44px] sm:min-h-0 text-xs rounded transition-colors whitespace-nowrap ${
                activeTab === tab
                  ? "bg-nps-oracle-accent text-nps-bg font-medium"
                  : "text-nps-text-dim hover:text-nps-text"
              }`}
            >
              {tabLabels[tab]}
            </button>
          ))}
        </div>
        <div className="flex gap-2 export-actions">
          {result && <ShareButton result={result} />}
          <ExportButton result={result} />
        </div>
      </div>

      {/* Tab content — eagerly rendered, hidden via CSS, fade on show */}
      <div
        id="tabpanel-summary"
        role="tabpanel"
        aria-labelledby="tab-summary"
        aria-live={activeTab === "summary" ? "polite" : undefined}
        className={activeTab === "summary" ? "nps-animate-fade-in" : "hidden"}
      >
        {/* Confidence meter at top of summary */}
        {(confidence || boosts.length > 0) && (
          <div className="mb-3 p-3 bg-nps-bg-card border border-nps-border/30 rounded">
            <ConfidenceMeter confidence={confidence ?? null} boosts={boosts} />
          </div>
        )}
        <SummaryTab result={result} />
        {/* Feedback form — shown after a reading is generated */}
        {readingId && <ReadingFeedback readingId={readingId} />}
      </div>
      <div
        id="tabpanel-details"
        role="tabpanel"
        aria-labelledby="tab-details"
        aria-live={activeTab === "details" ? "polite" : undefined}
        className={activeTab === "details" ? "nps-animate-fade-in" : "hidden"}
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
        aria-live={activeTab === "history" ? "polite" : undefined}
        className={activeTab === "history" ? "nps-animate-fade-in" : "hidden"}
      >
        <ReadingHistory />
      </div>
    </div>
  );
}
