import { useState } from "react";
import { useTranslation } from "react-i18next";
import type { OracleUser, OracleUserCreate } from "@/types";

interface UserFormProps {
  user?: OracleUser;
  onSubmit: (data: OracleUserCreate) => void;
  onCancel: () => void;
  onDelete?: () => void;
  isSubmitting?: boolean;
  serverError?: string | null;
}

interface FormErrors {
  name?: string;
  birthday?: string;
  mother_name?: string;
}

function validate(
  data: OracleUserCreate,
  t: (key: string) => string,
): FormErrors {
  const errors: FormErrors = {};
  if (!data.name || data.name.trim().length < 2) {
    errors.name = t("oracle.error_name_required");
  }
  if (!data.birthday) {
    errors.birthday = t("oracle.error_birthday_required");
  } else if (new Date(data.birthday) > new Date()) {
    errors.birthday = t("oracle.error_birthday_future");
  }
  if (!data.mother_name || data.mother_name.trim().length < 2) {
    errors.mother_name = t("oracle.error_mother_name_required");
  }
  return errors;
}

export function UserForm({
  user,
  onSubmit,
  onCancel,
  onDelete,
  isSubmitting,
  serverError,
}: UserFormProps) {
  const { t } = useTranslation();
  const isEdit = !!user;

  const [form, setForm] = useState<OracleUserCreate>({
    name: user?.name ?? "",
    name_persian: user?.name_persian ?? "",
    birthday: user?.birthday ?? "",
    mother_name: user?.mother_name ?? "",
    mother_name_persian: user?.mother_name_persian ?? "",
    country: user?.country ?? "",
    city: user?.city ?? "",
  });

  const [errors, setErrors] = useState<FormErrors>({});
  const [confirmDelete, setConfirmDelete] = useState(false);

  function handleChange(field: keyof OracleUserCreate, value: string) {
    setForm((prev) => ({ ...prev, [field]: value }));
    if (errors[field as keyof FormErrors]) {
      setErrors((prev) => ({ ...prev, [field]: undefined }));
    }
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const validationErrors = validate(form, t);
    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors);
      return;
    }
    onSubmit(form);
  }

  return (
    <div
      className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4"
      role="dialog"
      aria-modal="true"
      aria-label={isEdit ? t("oracle.edit_profile") : t("oracle.new_profile")}
      onClick={onCancel}
    >
      <div
        className="bg-nps-bg-card border border-nps-oracle-border rounded-lg p-6 w-full max-w-md max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <h3 className="text-lg font-semibold text-nps-oracle-accent mb-4">
          {isEdit ? t("oracle.edit_profile") : t("oracle.new_profile")}
        </h3>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Name */}
          <Field
            label={t("oracle.field_name")}
            value={form.name}
            onChange={(v) => handleChange("name", v)}
            error={errors.name}
            required
          />

          {/* Persian Name */}
          <Field
            label={t("oracle.field_name_persian")}
            value={form.name_persian ?? ""}
            onChange={(v) => handleChange("name_persian", v)}
            dir="rtl"
          />

          {/* Birthday */}
          <Field
            label={t("oracle.field_birthday")}
            value={form.birthday}
            onChange={(v) => handleChange("birthday", v)}
            error={errors.birthday}
            type="date"
            required
          />

          {/* Mother's Name */}
          <Field
            label={t("oracle.field_mother_name")}
            value={form.mother_name}
            onChange={(v) => handleChange("mother_name", v)}
            error={errors.mother_name}
            required
          />

          {/* Mother's Persian Name */}
          <Field
            label={t("oracle.field_mother_name_persian")}
            value={form.mother_name_persian ?? ""}
            onChange={(v) => handleChange("mother_name_persian", v)}
            dir="rtl"
          />

          {/* Country */}
          <Field
            label={t("oracle.field_country")}
            value={form.country ?? ""}
            onChange={(v) => handleChange("country", v)}
          />

          {/* City */}
          <Field
            label={t("oracle.field_city")}
            value={form.city ?? ""}
            onChange={(v) => handleChange("city", v)}
          />

          {/* Server error */}
          {serverError && (
            <p
              className="text-nps-error text-sm bg-nps-error/10 border border-nps-error/30 rounded px-3 py-2"
              role="alert"
            >
              {serverError}
            </p>
          )}

          {/* Buttons */}
          <div className="flex items-center gap-3 pt-2">
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-4 py-2 text-sm bg-nps-oracle-accent text-nps-bg font-medium rounded hover:bg-nps-oracle-accent/80 transition-colors disabled:opacity-50"
            >
              {isSubmitting
                ? t("common.loading")
                : isEdit
                  ? t("common.save")
                  : t("oracle.add_new_profile")}
            </button>

            <button
              type="button"
              onClick={onCancel}
              className="px-4 py-2 text-sm text-nps-text-dim border border-nps-border rounded hover:text-nps-text transition-colors"
            >
              {t("common.cancel")}
            </button>

            {isEdit && onDelete && (
              <button
                type="button"
                onClick={() => {
                  if (confirmDelete) {
                    onDelete();
                  } else {
                    setConfirmDelete(true);
                  }
                }}
                className={`ml-auto px-4 py-2 text-sm rounded transition-colors ${
                  confirmDelete
                    ? "bg-nps-bg-danger text-white"
                    : "text-nps-error border border-nps-error/30 hover:border-nps-error"
                }`}
              >
                {confirmDelete
                  ? t("oracle.delete_confirm")
                  : t("oracle.delete_profile")}
              </button>
            )}
          </div>
        </form>
      </div>
    </div>
  );
}

function Field({
  label,
  value,
  onChange,
  error,
  type = "text",
  dir,
  required,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  error?: string;
  type?: string;
  dir?: string;
  required?: boolean;
}) {
  const fieldId = label.toLowerCase().replace(/[^a-z0-9]/g, "-");
  const errorId = `${fieldId}-error`;

  return (
    <div>
      <label htmlFor={fieldId} className="block text-sm text-nps-text-dim mb-1">
        {label}
        {required && <span className="text-nps-error ml-1">*</span>}
      </label>
      <input
        id={fieldId}
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        dir={dir}
        aria-required={required}
        aria-invalid={!!error}
        aria-describedby={error ? errorId : undefined}
        className={`w-full bg-nps-bg-input border rounded px-3 py-2 text-sm text-nps-text focus:outline-none focus:border-nps-oracle-accent ${
          error ? "border-nps-error" : "border-nps-border"
        }`}
      />
      {error && (
        <p id={errorId} className="text-nps-error text-xs mt-1" role="alert">
          {error}
        </p>
      )}
    </div>
  );
}
