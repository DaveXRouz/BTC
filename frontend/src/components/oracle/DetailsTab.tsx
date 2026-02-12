import { useState } from "react";
import { useTranslation } from "react-i18next";
import { NumerologyNumberDisplay } from "./NumerologyNumberDisplay";
import { EmptyState } from "@/components/common/EmptyState";
import type { ConsultationResult } from "@/types";

interface DetailsTabProps {
  result: ConsultationResult | null;
}

function DetailSection({
  title,
  defaultOpen = false,
  children,
}: {
  title: string;
  defaultOpen?: boolean;
  children: React.ReactNode;
}) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="border border-nps-border rounded">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        aria-expanded={open}
        className="w-full flex items-center justify-between px-3 py-2 text-sm font-medium text-nps-text hover:bg-nps-bg-input transition-colors"
      >
        {title}
        <span className="text-nps-text-dim">{open ? "\u25B2" : "\u25BC"}</span>
      </button>
      {open && (
        <div className="px-3 pb-3 border-t border-nps-border">{children}</div>
      )}
    </div>
  );
}

function DataRow({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex justify-between py-1 text-xs">
      <span className="text-nps-text-dim">{label}</span>
      <span className="text-nps-text">{value}</span>
    </div>
  );
}

function ReadingDetails({
  result,
}: {
  result: Extract<ConsultationResult, { type: "reading" }>;
}) {
  const { t } = useTranslation();
  const {
    fc60,
    numerology,
    zodiac,
    chinese,
    moon,
    angel,
    chaldean,
    ganzhi,
    fc60_extended,
    synchronicities,
  } = result.data;

  return (
    <div className="space-y-3">
      {fc60 && (
        <DetailSection title={t("oracle.details_fc60")} defaultOpen>
          <DataRow label={t("oracle.cycle")} value={fc60.cycle} />
          <DataRow label={t("oracle.element")} value={fc60.element} />
          <DataRow label={t("oracle.polarity")} value={fc60.polarity} />
          <DataRow label={t("oracle.stem")} value={fc60.stem} />
          <DataRow label={t("oracle.branch")} value={fc60.branch} />
          <DataRow label={t("oracle.energy")} value={fc60.energy_level} />
          <DataRow
            label={t("oracle.element_balance")}
            value={
              <span className="flex gap-1">
                {Object.entries(fc60.element_balance).map(([el, val]) => (
                  <span key={el} className="text-nps-text-dim">
                    {el}:{val}
                  </span>
                ))}
              </span>
            }
          />
        </DetailSection>
      )}

      {fc60_extended && (
        <DetailSection title={t("oracle.fc60_stamp")}>
          <DataRow
            label={t("oracle.details_stamp")}
            value={fc60_extended.stamp}
          />
          <DataRow
            label={t("oracle.fc60_weekday")}
            value={fc60_extended.weekday_name}
          />
          <DataRow
            label={t("oracle.details_planet")}
            value={fc60_extended.weekday_planet}
          />
          <DataRow
            label={t("oracle.details_domain")}
            value={fc60_extended.weekday_domain}
          />
        </DetailSection>
      )}

      {numerology && (
        <DetailSection title={t("oracle.details_numerology")}>
          <div className="grid grid-cols-3 gap-3 py-2">
            <NumerologyNumberDisplay
              number={numerology.life_path}
              label={t("oracle.life_path")}
              meaning=""
              size="sm"
            />
            <NumerologyNumberDisplay
              number={numerology.day_vibration}
              label={t("oracle.day_vibration")}
              meaning=""
              size="sm"
            />
            <NumerologyNumberDisplay
              number={numerology.personal_year}
              label={t("oracle.personal_year")}
              meaning=""
              size="sm"
            />
          </div>
          <DataRow
            label={t("oracle.personal_month")}
            value={numerology.personal_month}
          />
          <DataRow
            label={t("oracle.personal_day")}
            value={numerology.personal_day}
          />
        </DetailSection>
      )}

      {moon && (
        <DetailSection title={t("oracle.details_moon_phase")}>
          <DataRow
            label={t("oracle.details_phase")}
            value={`${moon.emoji} ${moon.phase_name}`}
          />
          <DataRow
            label={t("oracle.details_illumination")}
            value={`${moon.illumination}%`}
          />
          <DataRow
            label={t("oracle.details_age")}
            value={`${moon.age_days} ${t("oracle.cosmic.days")}`}
          />
          <DataRow label={t("oracle.energy")} value={moon.meaning} />
        </DetailSection>
      )}

      {zodiac && Object.keys(zodiac).length > 0 && (
        <DetailSection title={t("oracle.details_zodiac")}>
          {Object.entries(zodiac).map(([key, val]) => (
            <DataRow key={key} label={key} value={val} />
          ))}
        </DetailSection>
      )}

      {ganzhi && (
        <DetailSection title={t("oracle.details_chinese_cosmology")}>
          <DataRow label={t("oracle.details_year")} value={ganzhi.year_name} />
          <DataRow
            label={t("oracle.details_year_animal")}
            value={ganzhi.year_animal}
          />
          <DataRow label={t("oracle.element")} value={ganzhi.stem_element} />
          <DataRow label={t("oracle.polarity")} value={ganzhi.stem_polarity} />
          {ganzhi.hour_animal && (
            <DataRow
              label={t("oracle.details_hour_animal")}
              value={ganzhi.hour_animal}
            />
          )}
          {ganzhi.hour_branch && (
            <DataRow
              label={t("oracle.details_hour_branch")}
              value={ganzhi.hour_branch}
            />
          )}
        </DetailSection>
      )}

      {chinese && Object.keys(chinese).length > 0 && !ganzhi && (
        <DetailSection title={t("oracle.details_chinese")}>
          {Object.entries(chinese).map(([key, val]) => (
            <DataRow key={key} label={key} value={val} />
          ))}
        </DetailSection>
      )}

      {angel && angel.matches.length > 0 && (
        <DetailSection title={t("oracle.details_angel_numbers")}>
          {angel.matches.map((m, i) => (
            <DataRow key={i} label={String(m.number)} value={m.meaning} />
          ))}
        </DetailSection>
      )}

      {chaldean && (
        <DetailSection title={t("oracle.details_chaldean")}>
          <DataRow label={t("oracle.details_value")} value={chaldean.value} />
          <DataRow
            label={t("oracle.details_meaning")}
            value={chaldean.meaning}
          />
          <DataRow
            label={t("oracle.details_letters")}
            value={chaldean.letter_values}
          />
        </DetailSection>
      )}

      {synchronicities && synchronicities.length > 0 && (
        <DetailSection title={t("oracle.details_synchronicities")}>
          {synchronicities.map((s, i) => (
            <div key={i} className="py-1 text-xs text-nps-text">
              {s}
            </div>
          ))}
        </DetailSection>
      )}
    </div>
  );
}

function QuestionDetails({
  result,
}: {
  result: Extract<ConsultationResult, { type: "question" }>;
}) {
  const { t } = useTranslation();
  const {
    question_number,
    detected_script,
    numerology_system,
    raw_letter_sum,
    is_master_number,
    confidence,
    ai_interpretation,
  } = result.data;

  return (
    <div className="space-y-2">
      <DataRow
        label={t("oracle.question_number_label")}
        value={question_number}
      />
      <DataRow label={t("oracle.detected_script")} value={detected_script} />
      <DataRow
        label={t("oracle.numerology_system")}
        value={numerology_system}
      />
      <DataRow label={t("oracle.details_raw_sum")} value={raw_letter_sum} />
      {is_master_number && (
        <DataRow label={t("oracle.master_number_badge")} value="Yes" />
      )}
      {confidence && (
        <DataRow
          label={t("oracle.confidence")}
          value={`${confidence.score}% (${confidence.level})`}
        />
      )}
      {ai_interpretation && (
        <div className="mt-2 text-xs text-nps-text">{ai_interpretation}</div>
      )}
    </div>
  );
}

function NameDetails({
  result,
}: {
  result: Extract<ConsultationResult, { type: "name" }>;
}) {
  const { t } = useTranslation();
  const {
    expression,
    soul_urge,
    personality,
    letter_breakdown,
    ai_interpretation,
  } = result.data;

  return (
    <div className="space-y-3">
      <div className="space-y-1">
        <DataRow label={t("oracle.expression")} value={expression} />
        <DataRow label={t("oracle.soul_urge")} value={soul_urge} />
        <DataRow label={t("oracle.personality")} value={personality} />
      </div>

      <DetailSection title={t("oracle.details_letters")}>
        <table className="w-full text-xs mt-1">
          <thead>
            <tr className="text-nps-text-dim border-b border-nps-border">
              <th className="text-start py-1">{t("oracle.letter_column")}</th>
              <th className="text-end py-1">{t("oracle.details_value")}</th>
              <th className="text-end py-1">{t("oracle.element")}</th>
            </tr>
          </thead>
          <tbody>
            {letter_breakdown.map(
              (
                l: { letter: string; value: number; element: string },
                i: number,
              ) => (
                <tr key={i} className="border-b border-nps-border/30">
                  <td className="py-1 text-nps-text">{l.letter}</td>
                  <td className="py-1 text-end text-nps-text">{l.value}</td>
                  <td className="py-1 text-end text-nps-text">{l.element}</td>
                </tr>
              ),
            )}
          </tbody>
        </table>
      </DetailSection>

      {ai_interpretation && (
        <div className="text-xs text-nps-text">{ai_interpretation}</div>
      )}
    </div>
  );
}

export function DetailsTab({ result }: DetailsTabProps) {
  const { t } = useTranslation();

  if (!result) {
    return (
      <EmptyState icon="readings" title={t("oracle.details_placeholder")} />
    );
  }

  switch (result.type) {
    case "reading":
      return <ReadingDetails result={result} />;
    case "question":
      return <QuestionDetails result={result} />;
    case "name":
      return <NameDetails result={result} />;
  }
}
