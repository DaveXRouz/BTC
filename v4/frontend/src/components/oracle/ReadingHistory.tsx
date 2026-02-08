import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useReadingHistory } from "@/hooks/useOracleReadings";

const PAGE_SIZE = 20;

type FilterType = "" | "reading" | "question" | "name";

export function ReadingHistory() {
  const { t } = useTranslation();
  const [filter, setFilter] = useState<FilterType>("");
  const [offset, setOffset] = useState(0);
  const [expandedId, setExpandedId] = useState<number | null>(null);

  const { data, isLoading, isError } = useReadingHistory({
    limit: PAGE_SIZE,
    offset,
    sign_type: filter || undefined,
  });

  const filters: { key: FilterType; label: string }[] = [
    { key: "", label: t("oracle.filter_all") },
    { key: "reading", label: t("oracle.filter_reading") },
    { key: "question", label: t("oracle.filter_question") },
    { key: "name", label: t("oracle.filter_name") },
  ];

  function handleFilterChange(key: FilterType) {
    setFilter(key);
    setOffset(0);
    setExpandedId(null);
  }

  if (isError) {
    return (
      <p className="text-xs text-nps-bg-danger">{t("oracle.error_history")}</p>
    );
  }

  return (
    <div className="space-y-3">
      {/* Filter chips */}
      <div className="flex gap-2">
        {filters.map((f) => (
          <button
            key={f.key}
            type="button"
            onClick={() => handleFilterChange(f.key)}
            className={`px-2 py-0.5 text-xs rounded transition-colors ${
              filter === f.key
                ? "bg-nps-oracle-accent text-nps-bg"
                : "bg-nps-bg-input text-nps-text-dim hover:text-nps-text"
            }`}
          >
            {f.label}
          </button>
        ))}
      </div>

      {/* Loading */}
      {isLoading && (
        <p className="text-xs text-nps-text-dim">{t("common.loading")}</p>
      )}

      {/* Empty */}
      {data && data.readings.length === 0 && (
        <p className="text-xs text-nps-text-dim">{t("oracle.history_empty")}</p>
      )}

      {/* History items */}
      {data && data.readings.length > 0 && (
        <>
          <div className="space-y-1">
            {data.readings.map((reading) => (
              <div
                key={reading.id}
                className="border border-nps-border rounded"
              >
                <button
                  type="button"
                  onClick={() =>
                    setExpandedId(expandedId === reading.id ? null : reading.id)
                  }
                  className="w-full flex items-center gap-2 px-3 py-2 text-left hover:bg-nps-bg-input transition-colors"
                >
                  <span className="px-1.5 py-0.5 text-[10px] rounded bg-nps-bg-input text-nps-text-dim">
                    {reading.sign_type}
                  </span>
                  <span className="flex-1 text-xs text-nps-text truncate">
                    {(reading.question || reading.sign_value || "").slice(
                      0,
                      50,
                    )}
                  </span>
                  <span className="text-[10px] text-nps-text-dim whitespace-nowrap">
                    {new Date(reading.created_at).toLocaleDateString()}
                  </span>
                </button>
                {expandedId === reading.id && (
                  <div className="px-3 pb-2 border-t border-nps-border text-xs text-nps-text space-y-1">
                    {reading.ai_interpretation && (
                      <p>{reading.ai_interpretation}</p>
                    )}
                    {reading.reading_result && (
                      <pre className="text-[10px] text-nps-text-dim overflow-x-auto">
                        {JSON.stringify(reading.reading_result, null, 2)}
                      </pre>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* Footer: count + load more */}
          <div className="flex items-center justify-between text-xs">
            <span className="text-nps-text-dim">
              {t("oracle.history_count", { count: data.total })}
            </span>
            {offset + PAGE_SIZE < data.total && (
              <button
                type="button"
                onClick={() => setOffset((prev) => prev + PAGE_SIZE)}
                className="px-2 py-1 text-xs bg-nps-bg-input text-nps-text-dim hover:text-nps-text rounded transition-colors"
              >
                {t("oracle.load_more")}
              </button>
            )}
          </div>
        </>
      )}
    </div>
  );
}
