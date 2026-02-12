import { useTranslation } from "react-i18next";
import { TranslatedReading } from "./TranslatedReading";
import { ReadingSection } from "./ReadingSection";
import { NumerologyNumberDisplay } from "./NumerologyNumberDisplay";
import { PatternBadge } from "./PatternBadge";
import { ReadingHeader } from "./ReadingHeader";
import { ReadingFooter } from "./ReadingFooter";
import { EmptyState } from "@/components/common/EmptyState";
import type { ConsultationResult } from "@/types";

interface SummaryTabProps {
  result: ConsultationResult | null;
}

function ReadingSummary({
  result,
}: {
  result: Extract<ConsultationResult, { type: "reading" }>;
}) {
  const { t } = useTranslation();
  const { data } = result;

  // Detect element balance warnings: any element at 0 or dominant >3
  const balanceWarnings: string[] = [];
  if (data.fc60?.element_balance) {
    for (const [el, val] of Object.entries(data.fc60.element_balance)) {
      if (val === 0)
        balanceWarnings.push(`${el}: ${t("oracle.caution_missing")}`);
      if (val > 3)
        balanceWarnings.push(`${el}: ${t("oracle.caution_dominant")}`);
    }
  }

  return (
    <div className="space-y-4">
      {/* Section 1: Header */}
      <ReadingHeader
        userName={t("oracle.current_reading")}
        readingDate={data.generated_at}
        readingType="reading"
        confidence={data.fc60 ? data.fc60.energy_level / 10 : undefined}
      />

      {/* Section 2: Universal Address */}
      {data.fc60_extended && (
        <ReadingSection
          title={t("oracle.section_universal_address")}
          icon="\uD83C\uDF10"
        >
          <div className="space-y-2 pt-2">
            <p className="font-mono text-sm text-nps-text-bright">
              {data.fc60_extended.stamp}
            </p>
            <div className="flex gap-4 text-xs text-nps-text-dim flex-wrap">
              <span>
                {data.fc60_extended.weekday_name} &middot;{" "}
                {data.fc60_extended.weekday_planet}
              </span>
              <span>{data.fc60_extended.weekday_domain}</span>
            </div>
          </div>
        </ReadingSection>
      )}

      {/* Section 3: Core Identity */}
      {data.numerology && (
        <ReadingSection
          title={t("oracle.section_core_identity")}
          icon="\uD83D\uDD22"
        >
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 pt-2">
            <NumerologyNumberDisplay
              number={data.numerology.life_path}
              label={t("oracle.life_path")}
              meaning={data.numerology.interpretation || ""}
              size="md"
            />
            <NumerologyNumberDisplay
              number={data.numerology.day_vibration}
              label={t("oracle.day_vibration")}
              meaning=""
              size="sm"
            />
            <NumerologyNumberDisplay
              number={data.numerology.personal_year}
              label={t("oracle.personal_year")}
              meaning=""
              size="sm"
            />
          </div>
        </ReadingSection>
      )}

      {/* Section 4: Right Now */}
      {(data.fc60 || data.moon || data.ganzhi) && (
        <ReadingSection title={t("oracle.section_right_now")} icon="\u23F0">
          <div className="grid grid-cols-2 gap-3 pt-2 text-sm">
            {data.fc60 && (
              <div>
                <span className="text-xs text-nps-text-dim">
                  {t("oracle.element")}
                </span>
                <p className="text-nps-text">{data.fc60.element}</p>
              </div>
            )}
            {data.fc60 && (
              <div>
                <span className="text-xs text-nps-text-dim">
                  {t("oracle.energy")}
                </span>
                <p className="text-nps-text">{data.fc60.energy_level}</p>
              </div>
            )}
            {data.moon && (
              <div>
                <span className="text-xs text-nps-text-dim">
                  {t("oracle.details_moon_phase")}
                </span>
                <p className="text-nps-text">
                  {data.moon.emoji} {data.moon.phase_name} (
                  {data.moon.illumination}%)
                </p>
              </div>
            )}
            {data.ganzhi && (
              <div>
                <span className="text-xs text-nps-text-dim">
                  {t("oracle.details_chinese_cosmology")}
                </span>
                <p className="text-nps-text">
                  {data.ganzhi.year_animal} &middot; {data.ganzhi.stem_element}
                </p>
              </div>
            )}
          </div>
        </ReadingSection>
      )}

      {/* Section 5: Patterns */}
      <ReadingSection title={t("oracle.section_patterns")} icon="\uD83D\uDD17">
        <div className="flex gap-2 flex-wrap pt-2">
          {data.synchronicities && data.synchronicities.length > 0 ? (
            data.synchronicities.map((s, i) => (
              <PatternBadge key={i} pattern={s} priority="medium" />
            ))
          ) : (
            <p className="text-xs text-nps-text-dim">
              {t("oracle.no_patterns")}
            </p>
          )}
          {data.angel &&
            data.angel.matches.length > 0 &&
            data.angel.matches.map((m, i) => (
              <PatternBadge
                key={`angel-${i}`}
                pattern={String(m.number)}
                priority="high"
                description={m.meaning}
              />
            ))}
        </div>
      </ReadingSection>

      {/* Section 6: The Message (AI Interpretation) */}
      {data.ai_interpretation && (
        <ReadingSection title={t("oracle.section_message")} icon="\u2728">
          <div className="pt-2 bg-nps-oracle-accent/5 rounded p-3 -mx-1">
            <TranslatedReading reading={data.ai_interpretation} />
          </div>
        </ReadingSection>
      )}

      {/* Section 7: Today's Advice */}
      <ReadingSection title={t("oracle.section_advice")} icon="\uD83D\uDCA1">
        <div className="pt-2 border-s-2 border-nps-oracle-accent/30 ps-3">
          <TranslatedReading reading={data.summary} />
        </div>
      </ReadingSection>

      {/* Section 8: Caution (only if warnings) */}
      {balanceWarnings.length > 0 && (
        <ReadingSection
          title={t("oracle.section_caution")}
          icon="\u26A0\uFE0F"
          priority="high"
        >
          <div className="pt-2 space-y-1">
            {balanceWarnings.map((w, i) => (
              <p key={i} className="text-xs text-nps-warning">
                {w}
              </p>
            ))}
          </div>
        </ReadingSection>
      )}

      {/* Section 9: Footer */}
      <ReadingFooter
        confidence={data.fc60 ? data.fc60.energy_level / 10 : 0.5}
        generatedAt={data.generated_at}
      />
    </div>
  );
}

function QuestionSummary({
  result,
}: {
  result: Extract<ConsultationResult, { type: "question" }>;
}) {
  const { t } = useTranslation();
  const { data } = result;

  return (
    <div className="space-y-4">
      <ReadingHeader
        userName={data.question}
        readingDate={new Date().toISOString()}
        readingType="question"
        confidence={data.confidence ? data.confidence.score / 100 : undefined}
      />

      <ReadingSection title={t("oracle.section_core_identity")} icon="\u2753">
        <div className="pt-2 space-y-2">
          <NumerologyNumberDisplay
            number={data.question_number}
            label={t("oracle.question_number_label")}
            meaning={data.numerology_system}
            size="md"
          />
          <div className="flex gap-4 text-xs text-nps-text-dim">
            <span>
              {t("oracle.detected_script", { script: data.detected_script })}
            </span>
            {data.is_master_number && (
              <span className="text-nps-score-peak">
                {t("oracle.master_number_badge")}
              </span>
            )}
          </div>
        </div>
      </ReadingSection>

      {data.ai_interpretation && (
        <ReadingSection title={t("oracle.section_message")} icon="\u2728">
          <div className="pt-2">
            <TranslatedReading reading={data.ai_interpretation} />
          </div>
        </ReadingSection>
      )}

      {data.confidence && (
        <ReadingFooter confidence={data.confidence.score / 100} />
      )}
    </div>
  );
}

function NameSummary({
  result,
}: {
  result: Extract<ConsultationResult, { type: "name" }>;
}) {
  const { t } = useTranslation();
  const { data } = result;

  return (
    <div className="space-y-4">
      <ReadingHeader
        userName={data.name}
        readingDate={new Date().toISOString()}
        readingType="name"
        confidence={data.confidence ? data.confidence.score / 100 : undefined}
      />

      <ReadingSection
        title={t("oracle.section_core_identity")}
        icon="\uD83D\uDD22"
      >
        <div className="grid grid-cols-3 gap-4 pt-2">
          <NumerologyNumberDisplay
            number={data.expression}
            label={t("oracle.expression")}
            meaning=""
            size="md"
          />
          <NumerologyNumberDisplay
            number={data.soul_urge}
            label={t("oracle.soul_urge")}
            meaning=""
            size="md"
          />
          <NumerologyNumberDisplay
            number={data.personality}
            label={t("oracle.personality")}
            meaning=""
            size="md"
          />
        </div>
      </ReadingSection>

      {data.letter_breakdown && data.letter_breakdown.length > 0 && (
        <ReadingSection title={t("oracle.details_letters")} icon="\uD83D\uDD24">
          <table className="w-full text-xs mt-2">
            <thead>
              <tr className="text-nps-text-dim border-b border-nps-border">
                <th className="text-start py-1">{t("oracle.letter_column")}</th>
                <th className="text-end py-1">{t("oracle.details_value")}</th>
                <th className="text-end py-1">{t("oracle.element")}</th>
              </tr>
            </thead>
            <tbody>
              {data.letter_breakdown.map((l, i) => (
                <tr key={i} className="border-b border-nps-border/30">
                  <td className="py-1 text-nps-text">{l.letter}</td>
                  <td className="py-1 text-end text-nps-text">{l.value}</td>
                  <td className="py-1 text-end text-nps-text">{l.element}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </ReadingSection>
      )}

      {data.ai_interpretation && (
        <ReadingSection title={t("oracle.section_message")} icon="\u2728">
          <div className="pt-2">
            <TranslatedReading reading={data.ai_interpretation} />
          </div>
        </ReadingSection>
      )}

      {data.confidence && (
        <ReadingFooter confidence={data.confidence.score / 100} />
      )}
    </div>
  );
}

export function SummaryTab({ result }: SummaryTabProps) {
  const { t } = useTranslation();

  if (!result) {
    return (
      <EmptyState icon="readings" title={t("oracle.results_placeholder")} />
    );
  }

  if (result.type === "reading") {
    return <ReadingSummary result={result} />;
  }
  if (result.type === "question") {
    return <QuestionSummary result={result} />;
  }
  return <NameSummary result={result} />;
}
