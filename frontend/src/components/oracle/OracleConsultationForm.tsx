import { useState } from "react";
import { useTranslation } from "react-i18next";
import type { SignData, LocationData, ConsultationResult } from "@/types";
import { validateSign } from "@/utils/signValidators";
import { oracle } from "@/services/api";
import type { NumerologySystem } from "@/utils/scriptDetector";
import { PersianKeyboard } from "./PersianKeyboard";
import { CalendarPicker } from "./CalendarPicker";
import { SignTypeSelector } from "./SignTypeSelector";
import { LocationSelector } from "./LocationSelector";
import { NumerologySystemSelector } from "./NumerologySystemSelector";
import { HeartbeatInput } from "./HeartbeatInput";

interface OracleConsultationFormProps {
  userId: number;
  userName: string;
  onResult: (result: ConsultationResult) => void;
}

export function OracleConsultationForm({
  userId: _userId,
  userName,
  onResult,
}: OracleConsultationFormProps) {
  const { t } = useTranslation();

  const [question, setQuestion] = useState("");
  const [date, setDate] = useState("");
  const [sign, setSign] = useState<SignData>({ type: "time", value: "" });
  const [location, setLocation] = useState<LocationData | null>(null);
  const [showKeyboard, setShowKeyboard] = useState(false);
  const [signError, setSignError] = useState<string | undefined>();
  const [numerologySystem, setNumerologySystem] =
    useState<NumerologySystem>("auto");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [consultationBpm, setConsultationBpm] = useState<number | null>(null);

  function handleKeyboardChar(char: string) {
    setQuestion((prev) => prev + char);
  }

  function handleKeyboardBackspace() {
    setQuestion((prev) => prev.slice(0, -1));
  }

  function handleSignChange(data: SignData) {
    setSign(data);
    if (signError) setSignError(undefined);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();

    // Validate sign
    const result = validateSign(sign);
    if (!result.valid) {
      setSignError(result.error ? t(result.error) : undefined);
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      if (question.trim()) {
        const data = await oracle.question(question);
        onResult({ type: "question", data });
      } else {
        const data = await oracle.reading(date || undefined);
        onResult({ type: "reading", data });
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : t("oracle.error_submit"));
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <p className="text-xs text-nps-text-dim">
        {t("oracle.consulting_for", { name: userName })}
      </p>

      {/* Question with keyboard toggle */}
      <div className="relative">
        <label className="block text-sm text-nps-text-dim mb-1">
          {t("oracle.question_label")}
        </label>
        <div className="relative">
          <textarea
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder={t("oracle.question_placeholder")}
            dir="rtl"
            rows={3}
            className="w-full bg-nps-bg-input border border-nps-border rounded px-3 py-2 text-sm text-nps-text focus:outline-none focus:border-nps-oracle-accent resize-none pr-10"
          />
          <button
            type="button"
            onClick={() => setShowKeyboard(!showKeyboard)}
            className="absolute top-2 right-2 w-7 h-7 flex items-center justify-center text-nps-text-dim hover:text-nps-oracle-accent transition-colors rounded"
            aria-label={t("oracle.keyboard_toggle")}
            title={t("oracle.keyboard_persian")}
          >
            ⌨
          </button>
        </div>
        {showKeyboard && (
          <PersianKeyboard
            onCharacterClick={handleKeyboardChar}
            onBackspace={handleKeyboardBackspace}
            onClose={() => setShowKeyboard(false)}
          />
        )}
      </div>

      {/* Date picker */}
      <CalendarPicker
        value={date}
        onChange={setDate}
        label={t("oracle.date_label")}
      />

      {/* Sign type selector */}
      <SignTypeSelector
        value={sign}
        onChange={handleSignChange}
        error={signError}
      />

      {/* Numerology system selector */}
      <NumerologySystemSelector
        value={numerologySystem}
        onChange={setNumerologySystem}
        userName={userName}
      />

      {/* Location selector */}
      <LocationSelector value={location} onChange={setLocation} />

      {/* Advanced Options — expandable */}
      <div className="border border-nps-border/30 rounded">
        <button
          type="button"
          onClick={() => setShowAdvanced(!showAdvanced)}
          className="w-full flex items-center justify-between px-3 py-2 text-xs text-nps-text-dim hover:text-nps-text transition-colors"
          aria-expanded={showAdvanced}
          data-testid="advanced-options-toggle"
        >
          <span>{t("oracle.advanced_options")}</span>
          <span className="text-[10px]">{showAdvanced ? "▲" : "▼"}</span>
        </button>
        {showAdvanced && (
          <div
            className="px-3 pb-3 space-y-2"
            data-testid="advanced-options-content"
          >
            <p className="text-[10px] text-nps-text-dim">
              {t("oracle.advanced_options_hint")}
            </p>
            <HeartbeatInput
              value={consultationBpm}
              onChange={setConsultationBpm}
            />
          </div>
        )}
      </div>

      {/* Submit */}
      <button
        type="submit"
        disabled={isSubmitting}
        aria-busy={isSubmitting}
        className="w-full px-4 py-2 text-sm bg-nps-oracle-accent text-nps-bg font-medium rounded hover:bg-nps-oracle-accent/80 transition-colors disabled:opacity-50"
      >
        {isSubmitting ? t("common.loading") : t("oracle.submit_reading")}
      </button>

      <div aria-live="polite">
        {error && (
          <p className="text-xs text-nps-bg-danger" role="alert">
            {error}
          </p>
        )}
      </div>
    </form>
  );
}
