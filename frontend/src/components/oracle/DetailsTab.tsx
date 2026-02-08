import { useState } from "react";
import { useTranslation } from "react-i18next";
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
        <DetailSection title="FC60 Stamp">
          <DataRow label="Stamp" value={fc60_extended.stamp} />
          <DataRow label="Weekday" value={fc60_extended.weekday_name} />
          <DataRow label="Planet" value={fc60_extended.weekday_planet} />
          <DataRow label="Domain" value={fc60_extended.weekday_domain} />
        </DetailSection>
      )}

      {numerology && (
        <DetailSection title={t("oracle.details_numerology")}>
          <DataRow label={t("oracle.life_path")} value={numerology.life_path} />
          <DataRow
            label={t("oracle.day_vibration")}
            value={numerology.day_vibration}
          />
          <DataRow
            label={t("oracle.personal_year")}
            value={numerology.personal_year}
          />
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
        <DetailSection title="Moon Phase">
          <DataRow label="Phase" value={`${moon.emoji} ${moon.phase_name}`} />
          <DataRow label="Illumination" value={`${moon.illumination}%`} />
          <DataRow label="Age" value={`${moon.age_days} days`} />
          <DataRow label="Energy" value={moon.meaning} />
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
        <DetailSection title="Chinese Cosmology">
          <DataRow label="Year" value={ganzhi.year_name} />
          <DataRow label="Year Animal" value={ganzhi.year_animal} />
          <DataRow label="Element" value={ganzhi.stem_element} />
          <DataRow label="Polarity" value={ganzhi.stem_polarity} />
          {ganzhi.hour_animal && (
            <DataRow label="Hour Animal" value={ganzhi.hour_animal} />
          )}
          {ganzhi.hour_branch && (
            <DataRow label="Hour Branch" value={ganzhi.hour_branch} />
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
        <DetailSection title="Angel Numbers">
          {angel.matches.map((m, i) => (
            <DataRow key={i} label={String(m.number)} value={m.meaning} />
          ))}
        </DetailSection>
      )}

      {chaldean && (
        <DetailSection title="Chaldean Numerology">
          <DataRow label="Value" value={chaldean.value} />
          <DataRow label="Meaning" value={chaldean.meaning} />
          <DataRow label="Letters" value={chaldean.letter_values} />
        </DetailSection>
      )}

      {synchronicities && synchronicities.length > 0 && (
        <DetailSection title="Synchronicities">
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
  const { sign_number, answer, interpretation, confidence } = result.data;

  return (
    <div className="space-y-2">
      <DataRow label={t("oracle.sign_number")} value={sign_number} />
      <DataRow label={t("oracle.answer")} value={answer} />
      <DataRow
        label={t("oracle.confidence")}
        value={`${Math.round(confidence * 100)}%`}
      />
      <div className="mt-2 text-xs text-nps-text">{interpretation}</div>
    </div>
  );
}

function NameDetails({
  result,
}: {
  result: Extract<ConsultationResult, { type: "name" }>;
}) {
  const { t } = useTranslation();
  const { destiny_number, soul_urge, personality, letters, interpretation } =
    result.data;

  return (
    <div className="space-y-3">
      <div className="space-y-1">
        <DataRow label={t("oracle.destiny")} value={destiny_number} />
        <DataRow label={t("oracle.soul_urge")} value={soul_urge} />
        <DataRow label={t("oracle.personality")} value={personality} />
      </div>

      <DetailSection title={t("oracle.details_letters")}>
        <table className="w-full text-xs mt-1">
          <thead>
            <tr className="text-nps-text-dim border-b border-nps-border">
              <th className="text-left py-1">Letter</th>
              <th className="text-right py-1">Value</th>
              <th className="text-right py-1">{t("oracle.element")}</th>
            </tr>
          </thead>
          <tbody>
            {letters.map((l, i) => (
              <tr key={i} className="border-b border-nps-border/30">
                <td className="py-1 text-nps-text">{l.letter}</td>
                <td className="py-1 text-right text-nps-text">{l.value}</td>
                <td className="py-1 text-right text-nps-text">{l.element}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </DetailSection>

      <div className="text-xs text-nps-text">{interpretation}</div>
    </div>
  );
}

export function DetailsTab({ result }: DetailsTabProps) {
  const { t } = useTranslation();

  if (!result) {
    return (
      <p className="text-nps-text-dim text-sm">
        {t("oracle.details_placeholder")}
      </p>
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
