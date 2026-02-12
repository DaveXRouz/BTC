import { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import {
  useReadingHistory,
  useDeleteReading,
  useToggleFavorite,
  useReadingStats,
} from "@/hooks/useOracleReadings";
import { ReadingCard } from "./ReadingCard";
import { ReadingDetail } from "./ReadingDetail";
import { LoadingSkeleton } from "@/components/common/LoadingSkeleton";
import { EmptyState } from "@/components/common/EmptyState";
import type { StoredReading } from "@/types";

const PAGE_SIZE = 12;

type FilterType =
  | ""
  | "reading"
  | "time"
  | "question"
  | "name"
  | "daily"
  | "multi_user";

export function ReadingHistory() {
  const { t } = useTranslation();
  const [filter, setFilter] = useState<FilterType>("");
  const [page, setPage] = useState(0);
  const [searchInput, setSearchInput] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [favoritesOnly, setFavoritesOnly] = useState(false);
  const [selectedReading, setSelectedReading] = useState<StoredReading | null>(
    null,
  );

  // Debounce search input
  useEffect(() => {
    const timer = setTimeout(() => {
      setSearchQuery(searchInput);
      setPage(0);
    }, 300);
    return () => clearTimeout(timer);
  }, [searchInput]);

  const { data, isLoading, isError, refetch } = useReadingHistory({
    limit: PAGE_SIZE,
    offset: page * PAGE_SIZE,
    sign_type: filter || undefined,
    search: searchQuery || undefined,
    date_from: dateFrom || undefined,
    date_to: dateTo || undefined,
    is_favorite: favoritesOnly ? true : undefined,
  });

  const { data: stats } = useReadingStats();
  const deleteMutation = useDeleteReading();
  const favoriteMutation = useToggleFavorite();

  const filters: { key: FilterType; label: string }[] = [
    { key: "", label: t("oracle.filter_all") },
    { key: "time", label: t("oracle.filter_time") },
    { key: "question", label: t("oracle.filter_question") },
    { key: "name", label: t("oracle.filter_name") },
    { key: "daily", label: t("oracle.filter_daily") },
    { key: "multi_user", label: t("oracle.filter_multi") },
  ];

  function handleFilterChange(key: FilterType) {
    setFilter(key);
    setPage(0);
    setSelectedReading(null);
  }

  function handleDelete(id: number) {
    deleteMutation.mutate(id);
    if (selectedReading?.id === id) setSelectedReading(null);
  }

  function handleToggleFavorite(id: number) {
    favoriteMutation.mutate(id);
  }

  function handleSelectReading(id: number) {
    const reading = data?.readings.find((r) => r.id === id);
    if (reading) setSelectedReading(reading);
  }

  const totalPages = data ? Math.ceil(data.total / PAGE_SIZE) : 0;

  if (isError) {
    return (
      <div className="text-center py-4">
        <p className="text-xs text-nps-error mb-2">
          {t("oracle.error_history")}
        </p>
        <button
          onClick={() => refetch()}
          className="text-xs text-nps-accent hover:underline"
        >
          {t("common.retry")}
        </button>
      </div>
    );
  }

  // Detail view
  if (selectedReading) {
    return (
      <ReadingDetail
        reading={selectedReading}
        onClose={() => setSelectedReading(null)}
        onToggleFavorite={handleToggleFavorite}
        onDelete={handleDelete}
      />
    );
  }

  return (
    <div className="space-y-3">
      {/* Stats bar */}
      {stats && (
        <div className="flex gap-4 text-[10px] text-nps-text-dim">
          <span>
            {t("oracle.stats_total", { count: stats.total_readings })}
          </span>
          <span>
            {t("oracle.stats_favorites", { count: stats.favorites_count })}
          </span>
        </div>
      )}

      {/* Search bar */}
      <div className="flex gap-2">
        <input
          type="text"
          value={searchInput}
          onChange={(e) => setSearchInput(e.target.value)}
          placeholder={t("oracle.search_placeholder")}
          className="flex-1 px-2 py-1 text-xs bg-nps-bg-input border border-nps-border rounded text-nps-text placeholder-nps-text-dim focus:outline-none focus:border-nps-oracle-accent"
        />
        <button
          type="button"
          onClick={() => setFavoritesOnly(!favoritesOnly)}
          className={`px-2 py-1 text-xs rounded border transition-colors ${
            favoritesOnly
              ? "border-amber-500 text-amber-400 bg-amber-500/10"
              : "border-nps-border text-nps-text-dim hover:text-nps-text"
          }`}
          title={t("oracle.filter_favorites")}
        >
          {favoritesOnly ? "\u2605" : "\u2606"}
        </button>
      </div>

      {/* Date range filters */}
      <div className="flex gap-2">
        <input
          type="date"
          value={dateFrom}
          onChange={(e) => {
            setDateFrom(e.target.value);
            setPage(0);
          }}
          className="px-2 py-1 text-[10px] bg-nps-bg-input border border-nps-border rounded text-nps-text focus:outline-none focus:border-nps-oracle-accent"
        />
        <span className="text-xs text-nps-text-dim self-center">
          {t("oracle.date_to_label")}
        </span>
        <input
          type="date"
          value={dateTo}
          onChange={(e) => {
            setDateTo(e.target.value);
            setPage(0);
          }}
          className="px-2 py-1 text-[10px] bg-nps-bg-input border border-nps-border rounded text-nps-text focus:outline-none focus:border-nps-oracle-accent"
        />
      </div>

      {/* Filter chips */}
      <div
        role="tablist"
        aria-label={t("a11y.filter_readings")}
        className="flex gap-2 flex-wrap"
      >
        {filters.map((f) => (
          <button
            key={f.key}
            type="button"
            role="tab"
            aria-selected={filter === f.key}
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
      {isLoading && <LoadingSkeleton variant="list" count={5} />}

      {/* Empty */}
      {data && data.readings.length === 0 && (
        <EmptyState icon="readings" title={t("oracle.history_empty")} />
      )}

      {/* Card grid */}
      {data && data.readings.length > 0 && (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
            {data.readings.map((reading) => (
              <ReadingCard
                key={reading.id}
                reading={reading}
                onSelect={handleSelectReading}
                onToggleFavorite={handleToggleFavorite}
                onDelete={handleDelete}
              />
            ))}
          </div>

          {/* Pagination */}
          <div className="flex items-center justify-between text-xs">
            <span className="text-nps-text-dim">
              {t("oracle.history_count", { count: data.total })}
            </span>
            {totalPages > 1 && (
              <div className="flex items-center gap-1">
                <button
                  type="button"
                  disabled={page === 0}
                  onClick={() => setPage((p) => p - 1)}
                  className="px-2 py-1 bg-nps-bg-input text-nps-text-dim rounded disabled:opacity-30 hover:text-nps-text transition-colors"
                >
                  &lsaquo;
                </button>
                <span className="text-nps-text-dim px-2">
                  {t("oracle.page_indicator", {
                    current: page + 1,
                    total: totalPages,
                  })}
                </span>
                <button
                  type="button"
                  disabled={page >= totalPages - 1}
                  onClick={() => setPage((p) => p + 1)}
                  className="px-2 py-1 bg-nps-bg-input text-nps-text-dim rounded disabled:opacity-30 hover:text-nps-text transition-colors"
                >
                  &rsaquo;
                </button>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}
