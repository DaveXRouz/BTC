import { useTranslation } from "react-i18next";
import type { ConsultationResult } from "@/types";

interface ExportButtonProps {
  result: ConsultationResult | null;
}

function formatAsText(result: ConsultationResult): string {
  const lines: string[] = [`Oracle ${result.type} reading`, ""];
  switch (result.type) {
    case "reading":
      lines.push(`Summary: ${result.data.summary}`);
      if (result.data.fc60) {
        lines.push(`Element: ${result.data.fc60.element}`);
        lines.push(`Energy: ${result.data.fc60.energy_level}`);
      }
      if (result.data.numerology) {
        lines.push(`Life Path: ${result.data.numerology.life_path}`);
      }
      break;
    case "question":
      lines.push(`Question: ${result.data.question}`);
      lines.push(`Answer: ${result.data.answer}`);
      lines.push(`Confidence: ${Math.round(result.data.confidence * 100)}%`);
      lines.push(`Interpretation: ${result.data.interpretation}`);
      break;
    case "name":
      lines.push(`Name: ${result.data.name}`);
      lines.push(`Destiny: ${result.data.destiny_number}`);
      lines.push(`Soul Urge: ${result.data.soul_urge}`);
      lines.push(`Personality: ${result.data.personality}`);
      lines.push(`Interpretation: ${result.data.interpretation}`);
      break;
  }
  return lines.join("\n");
}

function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export function ExportButton({ result }: ExportButtonProps) {
  const { t } = useTranslation();

  if (!result) return null;

  const timestamp = new Date().toISOString().replace(/[:.]/g, "-");

  function handleExportTxt() {
    const text = formatAsText(result!);
    const blob = new Blob([text], { type: "text/plain" });
    downloadBlob(blob, `oracle-reading-${timestamp}.txt`);
  }

  function handleExportJson() {
    const json = JSON.stringify(result!.data, null, 2);
    const blob = new Blob([json], { type: "application/json" });
    downloadBlob(blob, `oracle-reading-${timestamp}.json`);
  }

  return (
    <div className="flex gap-2">
      <button
        type="button"
        onClick={handleExportTxt}
        className="px-2 py-1 text-xs bg-nps-bg-input text-nps-text-dim hover:text-nps-text rounded transition-colors"
      >
        {t("oracle.export_text")}
      </button>
      <button
        type="button"
        onClick={handleExportJson}
        className="px-2 py-1 text-xs bg-nps-bg-input text-nps-text-dim hover:text-nps-text rounded transition-colors"
      >
        {t("oracle.export_json")}
      </button>
    </div>
  );
}
