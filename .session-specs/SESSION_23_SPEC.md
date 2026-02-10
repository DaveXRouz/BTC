# SESSION 23 SPEC — Settings Page

> **Block:** Frontend Core (Sessions 19-25)
> **Session:** 23 of 45
> **Duration:** ~4 hours
> **Complexity:** Medium
> **Dependencies:** Session 19 (layout/navigation), Session 2 (auth system)
> **Spec version:** 1.0
> **Created:** 2026-02-10

---

## TL;DR

- Rewrite `Settings.tsx` placeholder (currently 27 lines of TODOs) into a full settings page with 5 collapsible sections
- Create section components: `ProfileSection.tsx`, `PreferencesSection.tsx`, `OracleSettingsSection.tsx`, `ApiKeySection.tsx`, `AboutSection.tsx`
- Create `api/app/routers/settings.py` with endpoints for reading/writing user preferences (`oracle_settings` table)
- Create database migration `015_user_settings.sql` for `oracle_settings` key-value table
- Wire existing auth API key endpoints (`/auth/api-keys`) into the frontend `ApiKeySection` with masked display, reveal, copy, and regenerate
- Add ~25 i18n keys for settings in both EN and FA

---

## Objectives

1. **Settings page structure** — Rewrite `frontend/src/pages/Settings.tsx` with 5 collapsible sections: Profile, Preferences, Oracle Settings, API Keys, About
2. **User preferences backend** — Create `oracle_settings` table and `api/app/routers/settings.py` with GET/PUT endpoints for user preference persistence
3. **Profile section** — Allow editing display name and password change (uses existing auth system from `api/app/routers/auth.py`)
4. **Preferences section** — Locale selector (EN/FA), theme toggle (dark/light stub), default timezone, default numerology system
5. **API key management** — Frontend component wired to existing `POST/GET/DELETE /auth/api-keys` endpoints with masked display, one-click copy, reveal toggle, and regenerate with confirmation
6. **About section** — Static display of app version, framework version, credits, and links

---

## Prerequisites

### Required Sessions Complete

| Session | What It Provides                                   | Verify Command                                                               |
| ------- | -------------------------------------------------- | ---------------------------------------------------------------------------- |
| 19      | Layout with sidebar navigation + `/settings` route | Open `http://localhost:5173/settings` — page loads in Layout                 |
| 2       | Auth system: JWT login, API key CRUD endpoints     | `curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/auth/api-keys` |

### Infrastructure

- PostgreSQL running with `users` and `api_keys` tables
- API server running on port 8000
- Frontend dev server running on port 5173

### Verify Existing Code

```bash
# Settings page exists (placeholder)
cat frontend/src/pages/Settings.tsx | head -5
# Expected: "export function Settings()"

# Auth API key endpoints exist
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/auth/api-keys | python3 -m json.tool
# Expected: Array of API key objects

# App route exists
grep "settings" frontend/src/App.tsx
# Expected: <Route path="/settings" element={<Settings />} />
```

---

## Files to Create

| #   | Path                                                                | Purpose                                    | Est. Lines |
| --- | ------------------------------------------------------------------- | ------------------------------------------ | ---------- |
| 1   | `database/migrations/015_user_settings.sql`                         | Create `oracle_settings` key-value table   | ~30        |
| 2   | `database/migrations/015_user_settings_rollback.sql`                | Rollback migration                         | ~5         |
| 3   | `api/app/routers/settings.py`                                       | GET/PUT settings endpoints                 | ~80        |
| 4   | `api/app/models/settings.py`                                        | Pydantic request/response models           | ~30        |
| 5   | `api/app/orm/oracle_settings.py`                                    | SQLAlchemy ORM model                       | ~20        |
| 6   | `frontend/src/components/settings/ProfileSection.tsx`               | Profile editing (name, password change)    | ~120       |
| 7   | `frontend/src/components/settings/PreferencesSection.tsx`           | Locale, theme, timezone, numerology system | ~100       |
| 8   | `frontend/src/components/settings/OracleSettingsSection.tsx`        | Default reading type, auto-daily toggle    | ~80        |
| 9   | `frontend/src/components/settings/ApiKeySection.tsx`                | API key display, copy, reveal, regenerate  | ~150       |
| 10  | `frontend/src/components/settings/AboutSection.tsx`                 | App info, version, credits                 | ~50        |
| 11  | `frontend/src/components/settings/SettingsSection.tsx`              | Reusable collapsible section wrapper       | ~40        |
| 12  | `frontend/src/hooks/useSettings.ts`                                 | React Query hooks for settings CRUD        | ~50        |
| 13  | `frontend/src/components/settings/__tests__/Settings.test.tsx`      | Full settings page tests                   | ~150       |
| 14  | `frontend/src/components/settings/__tests__/ApiKeySection.test.tsx` | API key management tests                   | ~100       |

---

## Files to Modify

| #   | Path                              | What Changes                                        | Est. Delta         |
| --- | --------------------------------- | --------------------------------------------------- | ------------------ |
| 1   | `frontend/src/pages/Settings.tsx` | REWRITE: placeholder → full 5-section settings page | ~80 (full rewrite) |
| 2   | `frontend/src/services/api.ts`    | Add `settings` and expand `auth` API methods        | +30 lines          |
| 3   | `frontend/src/types/index.ts`     | Add `UserSettings`, `ApiKeyDisplay` interfaces      | +25 lines          |
| 4   | `frontend/src/locales/en.json`    | Add ~25 settings-related i18n keys                  | +25 lines          |
| 5   | `frontend/src/locales/fa.json`    | Add matching Persian translations                   | +25 lines          |
| 6   | `api/app/routers/__init__.py`     | Register settings router                            | +2 lines           |

---

## Files to Delete

None.

---

## Implementation Phases

### Phase 1: Database Migration + ORM (~20 min)

**Goal:** Create `oracle_settings` table for user preference persistence.

#### 1a: Create `database/migrations/015_user_settings.sql`

```sql
-- Migration 015: User settings (preferences persistence)
-- Key-value store per user for flexible settings storage

CREATE TABLE IF NOT EXISTS oracle_settings (
    id BIGSERIAL PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    setting_key VARCHAR(100) NOT NULL,
    setting_value TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_oracle_settings_user_key UNIQUE (user_id, setting_key)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_oracle_settings_user_id ON oracle_settings(user_id);

-- Trigger for updated_at
CREATE OR REPLACE FUNCTION oracle_settings_update_timestamp() RETURNS trigger AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_oracle_settings_updated
    BEFORE UPDATE ON oracle_settings
    FOR EACH ROW EXECUTE FUNCTION oracle_settings_update_timestamp();

COMMENT ON TABLE oracle_settings IS 'Per-user key-value settings storage';
COMMENT ON COLUMN oracle_settings.setting_key IS 'Setting name: locale, theme, default_reading_type, timezone, numerology_system, auto_daily';
```

**Design decisions:**

- Key-value store (not columnar) for flexibility — new settings can be added without migrations
- `UNIQUE(user_id, setting_key)` constraint enables `INSERT ... ON CONFLICT ... DO UPDATE` (upsert)
- Valid keys: `locale`, `theme`, `default_reading_type`, `timezone`, `numerology_system`, `auto_daily`

#### 1b: Create `database/migrations/015_user_settings_rollback.sql`

```sql
DROP TRIGGER IF EXISTS trg_oracle_settings_updated ON oracle_settings;
DROP FUNCTION IF EXISTS oracle_settings_update_timestamp();
DROP TABLE IF EXISTS oracle_settings;
```

#### 1c: Create `api/app/orm/oracle_settings.py`

```python
class OracleSettings(Base):
    __tablename__ = "oracle_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    setting_key: Mapped[str] = mapped_column(String(100), nullable=False)
    setting_value: Mapped[str] = mapped_column(Text, default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
```

#### STOP Checkpoint 1

```bash
# Run migration
psql -U nps -d nps -f database/migrations/015_user_settings.sql

# Verify table exists
psql -U nps -d nps -c "SELECT column_name, data_type FROM information_schema.columns WHERE table_name='oracle_settings';"
# Expected: 6 rows (id, user_id, setting_key, setting_value, created_at, updated_at)

# Verify unique constraint
psql -U nps -d nps -c "SELECT constraint_name FROM information_schema.table_constraints WHERE table_name='oracle_settings' AND constraint_type='UNIQUE';"
# Expected: uq_oracle_settings_user_key

# Verify ORM imports
cd api && python3 -c "from app.orm.oracle_settings import OracleSettings; print('ORM OK')"
```

**Do NOT proceed to Phase 2 until all checks pass.**

---

### Phase 2: Settings API (~30 min)

**Goal:** Create backend endpoints for reading and writing user settings.

#### 2a: Create `api/app/models/settings.py`

```python
from pydantic import BaseModel

VALID_SETTING_KEYS = {
    "locale",              # "en" or "fa"
    "theme",               # "dark" or "light"
    "default_reading_type", # "time", "name", "question", "daily"
    "timezone",            # e.g. "Asia/Tehran", "UTC"
    "numerology_system",   # "pythagorean", "chaldean", "abjad"
    "auto_daily",          # "true" or "false"
}

class SettingUpdate(BaseModel):
    key: str
    value: str

class SettingsResponse(BaseModel):
    settings: dict[str, str]  # key -> value map

class SettingsBulkUpdate(BaseModel):
    settings: dict[str, str]  # key -> value map (upsert all)
```

#### 2b: Create `api/app/routers/settings.py`

Two endpoints:

**`GET /settings`** — Returns all settings for the authenticated user as a key-value dict.

```python
@router.get("/settings", response_model=SettingsResponse)
def get_settings(
    _user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user_id = _user.get("user_id")
    if not user_id:
        return SettingsResponse(settings={})
    rows = db.query(OracleSettings).filter(OracleSettings.user_id == user_id).all()
    return SettingsResponse(settings={r.setting_key: r.setting_value for r in rows})
```

**`PUT /settings`** — Upserts multiple settings at once.

```python
@router.put("/settings", response_model=SettingsResponse)
def update_settings(
    body: SettingsBulkUpdate,
    _user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user_id = _user.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")

    for key, value in body.settings.items():
        if key not in VALID_SETTING_KEYS:
            raise HTTPException(status_code=400, detail=f"Invalid setting key: {key}")

        existing = db.query(OracleSettings).filter(
            OracleSettings.user_id == user_id,
            OracleSettings.setting_key == key,
        ).first()

        if existing:
            existing.setting_value = value
        else:
            db.add(OracleSettings(user_id=user_id, setting_key=key, setting_value=value))

    db.commit()
    # Return updated settings
    rows = db.query(OracleSettings).filter(OracleSettings.user_id == user_id).all()
    return SettingsResponse(settings={r.setting_key: r.setting_value for r in rows})
```

#### 2c: Register router in `api/app/routers/__init__.py`

Add `settings` router with prefix `/settings` and tag `settings`.

**Important route ordering note:** The existing `api/app/routers/auth.py` already handles `/auth/api-keys` endpoints. The settings router is a separate namespace at `/settings`. No conflicts.

#### STOP Checkpoint 2

```bash
# Start API
make dev-api &

# Get settings (should return empty for new user)
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/settings | python3 -m json.tool
# Expected: {"settings": {}}

# Set a preference
curl -X PUT -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"settings": {"locale": "fa", "theme": "dark"}}' \
  http://localhost:8000/settings | python3 -m json.tool
# Expected: {"settings": {"locale": "fa", "theme": "dark"}}

# Read back
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/settings | python3 -m json.tool
# Expected: {"settings": {"locale": "fa", "theme": "dark"}}

# Invalid key rejected
curl -X PUT -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"settings": {"invalid_key": "test"}}' \
  http://localhost:8000/settings -w "\n%{http_code}"
# Expected: 400
```

**Do NOT proceed to Phase 3 until all endpoint tests pass.**

---

### Phase 3: Frontend Types + API Client + Hooks (~20 min)

**Goal:** Wire frontend to settings and auth API.

#### 3a: Update `frontend/src/types/index.ts`

Add new interfaces:

```typescript
// ─── Settings ───

export interface UserSettings {
  locale: string; // "en" | "fa"
  theme: string; // "dark" | "light"
  default_reading_type: string; // "time" | "name" | "question" | "daily"
  timezone: string; // e.g. "Asia/Tehran"
  numerology_system: string; // "pythagorean" | "chaldean" | "abjad"
  auto_daily: string; // "true" | "false"
}

export interface SettingsResponse {
  settings: Record<string, string>;
}

export interface ApiKeyDisplay {
  id: string;
  name: string;
  scopes: string[];
  created_at: string;
  expires_at: string | null;
  last_used: string | null;
  is_active: boolean;
  key?: string; // Only returned on creation
}
```

#### 3b: Update `frontend/src/services/api.ts`

Add `settings` namespace and expand `auth`:

```typescript
// ─── Settings ───

export const settings = {
  get: () => request<SettingsResponse>("/settings"),
  update: (data: Record<string, string>) =>
    request<SettingsResponse>("/settings", {
      method: "PUT",
      body: JSON.stringify({ settings: data }),
    }),
};

// ─── Auth (expand existing if needed) ───

export const auth = {
  login: (username: string, password: string) =>
    request<{ access_token: string; token_type: string; expires_in: number }>(
      "/auth/login",
      { method: "POST", body: JSON.stringify({ username, password }) },
    ),
  apiKeys: {
    list: () => request<ApiKeyDisplay[]>("/auth/api-keys"),
    create: (name: string, scopes?: string[], expires_in_days?: number) =>
      request<ApiKeyDisplay>("/auth/api-keys", {
        method: "POST",
        body: JSON.stringify({ name, scopes: scopes ?? [], expires_in_days }),
      }),
    revoke: (keyId: string) =>
      request<{ detail: string }>(`/auth/api-keys/${keyId}`, {
        method: "DELETE",
      }),
  },
  changePassword: (currentPassword: string, newPassword: string) =>
    request<{ detail: string }>("/auth/change-password", {
      method: "POST",
      body: JSON.stringify({
        current_password: currentPassword,
        new_password: newPassword,
      }),
    }),
};
```

**Note on `changePassword`:** This endpoint may not exist yet. The spec should create a stub that returns 501 if the endpoint doesn't exist in the current auth router. Session 2 (auth hardening) should have this — if not, add it to `api/app/routers/auth.py` in Phase 4.

#### 3c: Create `frontend/src/hooks/useSettings.ts`

```typescript
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { settings as settingsApi, auth } from "@/services/api";

const SETTINGS_KEY = ["userSettings"] as const;
const API_KEYS_KEY = ["apiKeys"] as const;

export function useSettings() {
  return useQuery({
    queryKey: SETTINGS_KEY,
    queryFn: () => settingsApi.get(),
  });
}

export function useUpdateSettings() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: Record<string, string>) => settingsApi.update(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: SETTINGS_KEY }),
  });
}

export function useApiKeys() {
  return useQuery({
    queryKey: API_KEYS_KEY,
    queryFn: () => auth.apiKeys.list(),
  });
}

export function useCreateApiKey() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (params: {
      name: string;
      scopes?: string[];
      expires_in_days?: number;
    }) =>
      auth.apiKeys.create(params.name, params.scopes, params.expires_in_days),
    onSuccess: () => qc.invalidateQueries({ queryKey: API_KEYS_KEY }),
  });
}

export function useRevokeApiKey() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (keyId: string) => auth.apiKeys.revoke(keyId),
    onSuccess: () => qc.invalidateQueries({ queryKey: API_KEYS_KEY }),
  });
}
```

#### STOP Checkpoint 3

```bash
# TypeScript compiles
cd frontend && npx tsc --noEmit 2>&1 | tail -10
# Expected: no errors
```

**Do NOT proceed to Phase 4 until TypeScript compiles cleanly.**

---

### Phase 4: Reusable Section Wrapper + Settings Page Shell (~20 min)

**Goal:** Create the collapsible section pattern and wire the Settings page.

#### 4a: Create `frontend/src/components/settings/SettingsSection.tsx`

Reusable collapsible section wrapper:

```typescript
interface SettingsSectionProps {
  title: string;
  description?: string;
  defaultOpen?: boolean;
  children: React.ReactNode;
}
```

**Implementation:**

- Header row: title text + chevron icon (rotates on open/close)
- Click header to toggle `isOpen` state
- Content area: animate height with CSS `max-height` transition or `hidden` class
- `defaultOpen` prop controls initial state (default: `false`, first section `true`)
- Tailwind classes: `bg-nps-bg-card border border-nps-border rounded-lg`
- All text via `useTranslation()`

#### 4b: Rewrite `frontend/src/pages/Settings.tsx`

Replace the 27-line placeholder with the full settings page:

```typescript
import { useTranslation } from "react-i18next";
import { SettingsSection } from "@/components/settings/SettingsSection";
import { ProfileSection } from "@/components/settings/ProfileSection";
import { PreferencesSection } from "@/components/settings/PreferencesSection";
import { OracleSettingsSection } from "@/components/settings/OracleSettingsSection";
import { ApiKeySection } from "@/components/settings/ApiKeySection";
import { AboutSection } from "@/components/settings/AboutSection";

export function Settings() {
  const { t } = useTranslation();

  return (
    <div className="space-y-4 max-w-3xl">
      <h2 className="text-xl font-bold text-nps-text-bright">
        {t("settings.title")}
      </h2>

      <SettingsSection title={t("settings.profile")} description={t("settings.profile_desc")} defaultOpen>
        <ProfileSection />
      </SettingsSection>

      <SettingsSection title={t("settings.preferences")} description={t("settings.preferences_desc")}>
        <PreferencesSection />
      </SettingsSection>

      <SettingsSection title={t("settings.oracle")} description={t("settings.oracle_desc")}>
        <OracleSettingsSection />
      </SettingsSection>

      <SettingsSection title={t("settings.api_keys")} description={t("settings.api_keys_desc")}>
        <ApiKeySection />
      </SettingsSection>

      <SettingsSection title={t("settings.about")} description={t("settings.about_desc")}>
        <AboutSection />
      </SettingsSection>
    </div>
  );
}
```

#### STOP Checkpoint 4

```bash
# Frontend compiles
cd frontend && npx tsc --noEmit 2>&1 | tail -10

# Dev server runs without errors
cd frontend && npm run dev &
# Open http://localhost:5173/settings
# Expected: 5 collapsible sections visible (content may be empty stubs)
```

**Do NOT proceed to Phase 5 until page renders with all 5 sections.**

---

### Phase 5: Section Components (~80 min)

**Goal:** Implement all 5 settings section components.

#### 5a: `ProfileSection.tsx` (~25 min)

**Fields:**

- Display name (read-only text showing current username, with "Edit" stub note)
- Password change form:
  - Current password (password input)
  - New password (password input, min 8 chars)
  - Confirm new password
  - "Change Password" button
- Success/error messages

**Behavior:**

- On password change submit: call `auth.changePassword(current, new)`
- Validate: new password >= 8 chars, confirm matches new
- Show success toast or error message
- If change-password endpoint doesn't exist (501): show "Password change not yet available" message

**Note:** If `POST /auth/change-password` endpoint does NOT exist in `api/app/routers/auth.py`, add it in this session:

```python
@router.post("/change-password")
def change_password(
    request: ChangePasswordRequest,  # {current_password, new_password}
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    # Verify current password, update hash, return success
```

This is a minimal addition to the existing auth router — not a new file.

#### 5b: `PreferencesSection.tsx` (~20 min)

**Fields:**

- **Language selector:** Two buttons (EN / FA) — currently handled by `LanguageToggle` component in sidebar, but should also be controllable here. On change: update i18n language AND save to settings API.
- **Theme:** Two buttons (Dark / Light) — save preference. Apply will be a future session (26+). For now, just persist the choice.
- **Timezone:** Dropdown with common timezones (UTC, Asia/Tehran, Europe/London, America/New_York, etc.) or a text input. Default: browser timezone via `Intl.DateTimeFormat().resolvedOptions().timeZone`.
- **Numerology system:** Three options — Pythagorean (default), Chaldean, Abjad. Radio or segmented control.

**Behavior:**

- Load current settings via `useSettings()` hook
- On any change: call `useUpdateSettings()` with the changed key-value
- Auto-save on change (no explicit save button) — debounce 500ms
- Show "Saved" confirmation briefly after each save

#### 5c: `OracleSettingsSection.tsx` (~15 min)

**Fields:**

- **Default reading type:** Dropdown — Time, Name, Question, Daily. Controls which tab is pre-selected on the Oracle page.
- **Auto-daily toggle:** Checkbox/switch — when enabled, automatically generates a daily reading each day.

**Behavior:**

- Load from settings API
- Auto-save on change
- These are informational preferences — they don't trigger any immediate backend action

#### 5d: `ApiKeySection.tsx` (~30 min)

This is the most complex section. It wires to the **existing** endpoints in `api/app/routers/auth.py`:

- `GET /auth/api-keys` — list keys
- `POST /auth/api-keys` — create new key
- `DELETE /auth/api-keys/{key_id}` — revoke key

**Layout:**

```
┌──────────────────────────────────────────────────────┐
│ API Keys                                              │
│                                                       │
│ Your API keys allow programmatic access to NPS.       │
│                                                       │
│ ┌──────────────────────────────────────────────────┐ │
│ │ my-bot-key               Created: 2026-01-15     │ │
│ │ nps_••••••••••••••••     Last used: 2 days ago   │ │
│ │ [Reveal] [Copy] [Revoke]                         │ │
│ └──────────────────────────────────────────────────┘ │
│                                                       │
│ [+ Create New API Key]                                │
│                                                       │
│ ── Create Key Form (shown when + clicked) ──          │
│ Name: [____________]                                  │
│ Expires: [Never ▼]   [30 days] [90 days] [1 year]   │
│ [Create]  [Cancel]                                    │
│                                                       │
│ ⚠️ NEW KEY (shown once after creation):                │
│ nps_abc123xyz789...                                   │
│ [Copy to clipboard]                                   │
│ This key will not be shown again.                     │
└──────────────────────────────────────────────────────┘
```

**Behavior:**

- **List:** Fetch via `useApiKeys()`. Display each key with name, masked hash prefix, created date, last used date.
- **Reveal:** Not possible for existing keys (hash stored, not plaintext). Show tooltip: "Keys cannot be revealed after creation."
- **Copy:** Only available for newly created key (before page navigation). Uses `navigator.clipboard.writeText()`.
- **Create:** Form with name input + expiration dropdown. On submit: call `useCreateApiKey()`. Show the returned `key` field prominently with copy button and warning "This key will not be shown again."
- **Revoke:** Click → confirmation dialog ("Revoke this key? This cannot be undone.") → call `useRevokeApiKey()`.
- **Empty state:** "No API keys yet. Create one to integrate with Telegram or external services."

#### 5e: `AboutSection.tsx` (~10 min)

**Content (static):**

- App name: NPS (Numerology Puzzle Solver)
- App version: Read from `package.json` version or hardcoded `0.1.0`
- Framework: FC60 Numerology AI Framework
- Framework version: `1.0.0`
- Author: Dave (DaveXRouz)
- Repository link: `https://github.com/DaveXRouz/NPS`
- Credits: Built with React, FastAPI, PostgreSQL, Anthropic Claude API
- License: Private

Render as a simple definition list or key-value grid.

#### STOP Checkpoint 5

```bash
# Frontend compiles
cd frontend && npx tsc --noEmit 2>&1 | tail -10

# Dev server renders all sections
cd frontend && npm run dev &
# Open http://localhost:5173/settings

# Manual checks:
# 1. Profile section: password change form visible
# 2. Preferences: language selector, theme toggle, timezone dropdown, numerology system
# 3. Oracle settings: reading type dropdown, auto-daily toggle
# 4. API keys: list existing keys, create new key form
# 5. About: app info displayed
# 6. All sections collapse/expand
# 7. Changing language here also changes sidebar language
# 8. Settings persist after page refresh (check API call in Network tab)
```

**Do NOT proceed to Phase 6 until all 5 sections render and basic interactions work.**

---

### Phase 6: i18n (~15 min)

**Goal:** Add all settings i18n keys in both English and Persian.

#### 6a: Update `frontend/src/locales/en.json`

Add/expand under `"settings"`:

```json
{
  "settings": {
    "title": "Settings",
    "profile": "Profile",
    "profile_desc": "Manage your account information",
    "preferences": "Preferences",
    "preferences_desc": "Language, theme, and display options",
    "oracle": "Oracle Settings",
    "oracle_desc": "Default reading preferences",
    "api_keys": "API Keys",
    "api_keys_desc": "Manage programmatic access to NPS",
    "about": "About",
    "about_desc": "Application information and credits",
    "display_name": "Display Name",
    "change_password": "Change Password",
    "current_password": "Current Password",
    "new_password": "New Password",
    "confirm_password": "Confirm New Password",
    "password_changed": "Password changed successfully",
    "password_mismatch": "Passwords do not match",
    "password_too_short": "Password must be at least 8 characters",
    "password_wrong": "Current password is incorrect",
    "language": "Language",
    "theme": "Theme",
    "theme_dark": "Dark",
    "theme_light": "Light",
    "timezone": "Timezone",
    "numerology_system": "Numerology System",
    "numerology_pythagorean": "Pythagorean",
    "numerology_chaldean": "Chaldean",
    "numerology_abjad": "Abjad",
    "default_reading_type": "Default Reading Type",
    "auto_daily": "Auto-generate daily reading",
    "auto_daily_desc": "Automatically create a reading each day",
    "saved": "Saved",
    "api_key_name": "Key Name",
    "api_key_create": "Create New API Key",
    "api_key_expires": "Expires",
    "api_key_never": "Never",
    "api_key_30_days": "30 days",
    "api_key_90_days": "90 days",
    "api_key_1_year": "1 year",
    "api_key_created": "API key created",
    "api_key_warning": "This key will not be shown again. Copy it now.",
    "api_key_copy": "Copy",
    "api_key_copied": "Copied!",
    "api_key_revoke": "Revoke",
    "api_key_revoke_confirm": "Revoke this key? This cannot be undone.",
    "api_key_revoked": "API key revoked",
    "api_key_empty": "No API keys yet. Create one to integrate with Telegram or external services.",
    "api_key_last_used": "Last used",
    "api_key_created_at": "Created",
    "api_key_no_reveal": "Keys cannot be revealed after creation",
    "about_app": "NPS — Numerology Puzzle Solver",
    "about_version": "Version",
    "about_framework": "Framework",
    "about_author": "Author",
    "about_repo": "Repository",
    "about_credits": "Credits"
  }
}
```

#### 6b: Update `frontend/src/locales/fa.json`

Add matching Persian translations under `"settings"`:

```json
{
  "settings": {
    "title": "\u062a\u0646\u0638\u06cc\u0645\u0627\u062a",
    "profile": "\u067e\u0631\u0648\u0641\u0627\u06cc\u0644",
    "profile_desc": "\u0645\u062f\u06cc\u0631\u06cc\u062a \u0627\u0637\u0644\u0627\u0639\u0627\u062a \u062d\u0633\u0627\u0628 \u06a9\u0627\u0631\u0628\u0631\u06cc",
    "preferences": "\u062a\u0631\u062c\u06cc\u062d\u0627\u062a",
    "preferences_desc": "\u0632\u0628\u0627\u0646\u060c \u067e\u0648\u0633\u062a\u0647 \u0648 \u06af\u0632\u06cc\u0646\u0647\u200c\u0647\u0627\u06cc \u0646\u0645\u0627\u06cc\u0634",
    "oracle": "\u062a\u0646\u0638\u06cc\u0645\u0627\u062a \u0627\u0648\u0631\u0627\u06a9\u0644",
    "oracle_desc": "\u062a\u0631\u062c\u06cc\u062d\u0627\u062a \u067e\u06cc\u0634\u200c\u0641\u0631\u0636 \u062e\u0648\u0627\u0646\u0634",
    "api_keys": "\u06a9\u0644\u06cc\u062f\u0647\u0627\u06cc API",
    "api_keys_desc": "\u0645\u062f\u06cc\u0631\u06cc\u062a \u062f\u0633\u062a\u0631\u0633\u06cc \u0628\u0631\u0646\u0627\u0645\u0647\u200c\u0627\u06cc \u0628\u0647 NPS",
    "about": "\u062f\u0631\u0628\u0627\u0631\u0647",
    "about_desc": "\u0627\u0637\u0644\u0627\u0639\u0627\u062a \u0628\u0631\u0646\u0627\u0645\u0647 \u0648 \u0627\u0639\u062a\u0628\u0627\u0631\u0627\u062a",
    "display_name": "\u0646\u0627\u0645 \u0646\u0645\u0627\u06cc\u0634\u06cc",
    "change_password": "\u062a\u063a\u06cc\u06cc\u0631 \u0631\u0645\u0632 \u0639\u0628\u0648\u0631",
    "current_password": "\u0631\u0645\u0632 \u0639\u0628\u0648\u0631 \u0641\u0639\u0644\u06cc",
    "new_password": "\u0631\u0645\u0632 \u0639\u0628\u0648\u0631 \u062c\u062f\u06cc\u062f",
    "confirm_password": "\u062a\u0627\u06cc\u06cc\u062f \u0631\u0645\u0632 \u0639\u0628\u0648\u0631 \u062c\u062f\u06cc\u062f",
    "password_changed": "\u0631\u0645\u0632 \u0639\u0628\u0648\u0631 \u0628\u0627 \u0645\u0648\u0641\u0642\u06cc\u062a \u062a\u063a\u06cc\u06cc\u0631 \u06a9\u0631\u062f",
    "password_mismatch": "\u0631\u0645\u0632\u0647\u0627\u06cc \u0639\u0628\u0648\u0631 \u0645\u0637\u0627\u0628\u0642\u062a \u0646\u062f\u0627\u0631\u0646\u062f",
    "password_too_short": "\u0631\u0645\u0632 \u0639\u0628\u0648\u0631 \u0628\u0627\u06cc\u062f \u062d\u062f\u0627\u0642\u0644 \u06f8 \u06a9\u0627\u0631\u0627\u06a9\u062a\u0631 \u0628\u0627\u0634\u062f",
    "password_wrong": "\u0631\u0645\u0632 \u0639\u0628\u0648\u0631 \u0641\u0639\u0644\u06cc \u0646\u0627\u062f\u0631\u0633\u062a \u0627\u0633\u062a",
    "language": "\u0632\u0628\u0627\u0646",
    "theme": "\u067e\u0648\u0633\u062a\u0647",
    "theme_dark": "\u062a\u0627\u0631\u06cc\u06a9",
    "theme_light": "\u0631\u0648\u0634\u0646",
    "timezone": "\u0645\u0646\u0637\u0642\u0647 \u0632\u0645\u0627\u0646\u06cc",
    "numerology_system": "\u0633\u06cc\u0633\u062a\u0645 \u0639\u062f\u062f\u0634\u0646\u0627\u0633\u06cc",
    "numerology_pythagorean": "\u0641\u06cc\u062b\u0627\u063a\u0648\u0631\u0633\u06cc",
    "numerology_chaldean": "\u06a9\u0644\u062f\u0627\u0646\u06cc",
    "numerology_abjad": "\u0627\u0628\u062c\u062f",
    "default_reading_type": "\u0646\u0648\u0639 \u062e\u0648\u0627\u0646\u0634 \u067e\u06cc\u0634\u200c\u0641\u0631\u0636",
    "auto_daily": "\u062a\u0648\u0644\u06cc\u062f \u062e\u0648\u062f\u06a9\u0627\u0631 \u062e\u0648\u0627\u0646\u0634 \u0631\u0648\u0632\u0627\u0646\u0647",
    "auto_daily_desc": "\u0647\u0631 \u0631\u0648\u0632 \u0628\u0647 \u0637\u0648\u0631 \u062e\u0648\u062f\u06a9\u0627\u0631 \u06cc\u06a9 \u062e\u0648\u0627\u0646\u0634 \u0627\u06cc\u062c\u0627\u062f \u06a9\u0646\u06cc\u062f",
    "saved": "\u0630\u062e\u06cc\u0631\u0647 \u0634\u062f",
    "api_key_name": "\u0646\u0627\u0645 \u06a9\u0644\u06cc\u062f",
    "api_key_create": "\u0627\u06cc\u062c\u0627\u062f \u06a9\u0644\u06cc\u062f API \u062c\u062f\u06cc\u062f",
    "api_key_expires": "\u0627\u0646\u0642\u0636\u0627",
    "api_key_never": "\u0647\u0631\u06af\u0632",
    "api_key_30_days": "\u06f3\u06f0 \u0631\u0648\u0632",
    "api_key_90_days": "\u06f9\u06f0 \u0631\u0648\u0632",
    "api_key_1_year": "\u06f1 \u0633\u0627\u0644",
    "api_key_created": "\u06a9\u0644\u06cc\u062f API \u0627\u06cc\u062c\u0627\u062f \u0634\u062f",
    "api_key_warning": "\u0627\u06cc\u0646 \u06a9\u0644\u06cc\u062f \u062f\u0648\u0628\u0627\u0631\u0647 \u0646\u0645\u0627\u06cc\u0634 \u062f\u0627\u062f\u0647 \u0646\u0645\u06cc\u200c\u0634\u0648\u062f. \u0627\u06a9\u0646\u0648\u0646 \u06a9\u067e\u06cc \u06a9\u0646\u06cc\u062f.",
    "api_key_copy": "\u06a9\u067e\u06cc",
    "api_key_copied": "\u06a9\u067e\u06cc \u0634\u062f!",
    "api_key_revoke": "\u0644\u063a\u0648",
    "api_key_revoke_confirm": "\u0627\u06cc\u0646 \u06a9\u0644\u06cc\u062f \u0644\u063a\u0648 \u0634\u0648\u062f\u061f \u0627\u06cc\u0646 \u0639\u0645\u0644 \u0642\u0627\u0628\u0644 \u0628\u0627\u0632\u06af\u0634\u062a \u0646\u06cc\u0633\u062a.",
    "api_key_revoked": "\u06a9\u0644\u06cc\u062f API \u0644\u063a\u0648 \u0634\u062f",
    "api_key_empty": "\u0647\u0646\u0648\u0632 \u06a9\u0644\u06cc\u062f API \u0646\u062f\u0627\u0631\u06cc\u062f. \u0628\u0631\u0627\u06cc \u0627\u062a\u0635\u0627\u0644 \u0628\u0627 \u062a\u0644\u06af\u0631\u0627\u0645 \u06cc\u0627 \u0633\u0631\u0648\u06cc\u0633\u200c\u0647\u0627\u06cc \u062e\u0627\u0631\u062c\u06cc \u06cc\u06a9\u06cc \u0628\u0633\u0627\u0632\u06cc\u062f.",
    "api_key_last_used": "\u0622\u062e\u0631\u06cc\u0646 \u0627\u0633\u062a\u0641\u0627\u062f\u0647",
    "api_key_created_at": "\u0627\u06cc\u062c\u0627\u062f \u0634\u062f\u0647",
    "api_key_no_reveal": "\u06a9\u0644\u06cc\u062f\u0647\u0627 \u067e\u0633 \u0627\u0632 \u0627\u06cc\u062c\u0627\u062f \u0642\u0627\u0628\u0644 \u0646\u0645\u0627\u06cc\u0634 \u0646\u06cc\u0633\u062a\u0646\u062f",
    "about_app": "NPS \u2014 \u062d\u0644\u200c\u06a9\u0646\u0646\u062f\u0647 \u067e\u0627\u0632\u0644 \u0639\u062f\u062f\u0634\u0646\u0627\u0633\u06cc",
    "about_version": "\u0646\u0633\u062e\u0647",
    "about_framework": "\u0686\u0627\u0631\u0686\u0648\u0628",
    "about_author": "\u0646\u0648\u06cc\u0633\u0646\u062f\u0647",
    "about_repo": "\u0645\u062e\u0632\u0646",
    "about_credits": "\u0627\u0639\u062a\u0628\u0627\u0631\u0627\u062a"
  }
}
```

#### STOP Checkpoint 6

```bash
# Verify no missing keys (compare key counts)
cd frontend && python3 -c "
import json
en = json.load(open('src/locales/en.json'))
fa = json.load(open('src/locales/fa.json'))
en_keys = set(en.get('settings', {}).keys())
fa_keys = set(fa.get('settings', {}).keys())
missing = en_keys - fa_keys
extra = fa_keys - en_keys
print(f'EN settings keys: {len(en_keys)}')
print(f'FA settings keys: {len(fa_keys)}')
if missing: print(f'Missing in FA: {missing}')
if extra: print(f'Extra in FA: {extra}')
if not missing and not extra: print('All keys match!')
"

# Switch to FA in browser, verify settings page renders in Persian
```

**Do NOT proceed to Phase 7 until all i18n keys match between EN and FA.**

---

### Phase 7: Tests (~40 min)

**Goal:** Write 15 tests covering all settings functionality.

#### Backend Tests: `api/tests/test_settings.py` (5 tests)

| #   | Test Name                        | What It Verifies                                              |
| --- | -------------------------------- | ------------------------------------------------------------- |
| 1   | `test_get_settings_empty`        | GET /settings returns empty dict for new user                 |
| 2   | `test_update_settings`           | PUT /settings with valid keys saves and returns updated dict  |
| 3   | `test_get_settings_after_update` | GET /settings returns previously saved values                 |
| 4   | `test_invalid_setting_key`       | PUT /settings with unknown key returns 400                    |
| 5   | `test_upsert_settings`           | PUT /settings updates existing key without creating duplicate |

**Test structure:**

```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
HEADERS = {"Authorization": "Bearer test-key"}

def test_get_settings_empty():
    resp = client.get("/settings", headers=HEADERS)
    assert resp.status_code == 200
    assert resp.json()["settings"] == {} or isinstance(resp.json()["settings"], dict)

def test_update_settings():
    resp = client.put("/settings", headers=HEADERS, json={"settings": {"locale": "fa", "theme": "dark"}})
    assert resp.status_code == 200
    data = resp.json()["settings"]
    assert data["locale"] == "fa"
    assert data["theme"] == "dark"

def test_invalid_setting_key():
    resp = client.put("/settings", headers=HEADERS, json={"settings": {"bad_key": "value"}})
    assert resp.status_code == 400
```

#### Frontend Tests: 10 tests across 2 files

**`frontend/src/components/settings/__tests__/Settings.test.tsx` (6 tests):**

| #   | Test Name                                     | What It Verifies                               |
| --- | --------------------------------------------- | ---------------------------------------------- |
| 6   | `renders all 5 settings sections`             | All section headers visible                    |
| 7   | `sections collapse and expand`                | Click header toggles content visibility        |
| 8   | `profile section shows password form`         | Password inputs and submit button present      |
| 9   | `preferences section shows language selector` | EN/FA buttons visible                          |
| 10  | `oracle settings shows reading type dropdown` | Dropdown with time/name/question/daily options |
| 11  | `about section shows app info`                | App name and version displayed                 |

**`frontend/src/components/settings/__tests__/ApiKeySection.test.tsx` (4 tests):**

| #   | Test Name                               | What It Verifies                          |
| --- | --------------------------------------- | ----------------------------------------- |
| 12  | `renders empty state when no keys`      | Empty message shown when API returns []   |
| 13  | `renders existing API keys`             | Key name, created date shown for each key |
| 14  | `create key form shows on button click` | Name input and expiration dropdown appear |
| 15  | `revoke key fires with confirmation`    | Click revoke → confirm → delete called    |

#### STOP Checkpoint 7 (FINAL)

```bash
# Backend tests
cd api && python3 -m pytest tests/test_settings.py -v
# Expected: 5 passed

# Frontend tests — Settings
cd frontend && npx vitest run src/components/settings/__tests__/Settings.test.tsx
# Expected: 6 passed

# Frontend tests — ApiKeySection
cd frontend && npx vitest run src/components/settings/__tests__/ApiKeySection.test.tsx
# Expected: 4 passed

# Full test suite still passes
cd api && python3 -m pytest tests/ -v --tb=short
cd frontend && npx vitest run
```

**All 15 tests must pass before marking session complete.**

---

## Acceptance Criteria

| #   | Criterion                                             | Verify Command                                                                                                                                                               |
| --- | ----------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | `oracle_settings` table exists with unique constraint | `psql -U nps -d nps -c "SELECT constraint_name FROM information_schema.table_constraints WHERE table_name='oracle_settings' AND constraint_type='UNIQUE';"`                  |
| 2   | GET /settings returns user preferences                | `curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/settings \| python3 -m json.tool`                                                                              |
| 3   | PUT /settings persists preferences                    | `curl -X PUT -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d '{"settings":{"locale":"fa"}}' http://localhost:8000/settings \| python3 -m json.tool` |
| 4   | Invalid setting key returns 400                       | `curl -X PUT -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d '{"settings":{"bad":"val"}}' http://localhost:8000/settings -w "\n%{http_code}"` (400) |
| 5   | Settings page renders all 5 sections                  | Visual: `/settings` shows Profile, Preferences, Oracle, API Keys, About                                                                                                      |
| 6   | Sections collapse/expand                              | Visual: click section header toggles content                                                                                                                                 |
| 7   | Language change in preferences works                  | Visual: select FA in preferences → page switches to Persian                                                                                                                  |
| 8   | Settings persist across page refresh                  | Visual: set preference → refresh → preference restored                                                                                                                       |
| 9   | API key list displays existing keys                   | Visual: API Keys section shows keys with names and dates                                                                                                                     |
| 10  | API key creation shows key once                       | Visual: create key → key displayed → warning shown                                                                                                                           |
| 11  | API key revocation works                              | Visual: revoke → confirm → key disappears from list                                                                                                                          |
| 12  | i18n complete EN + FA                                 | Visual: switch language, all settings strings translated                                                                                                                     |
| 13  | 15 tests pass                                         | See STOP Checkpoint 7 commands                                                                                                                                               |

---

## Error Scenarios

### Error 1: Settings API returns 401 (not authenticated)

**Symptoms:** Settings page shows empty sections, Network tab shows 401 on /settings.

**Root Cause:** User is not authenticated (no JWT token in localStorage), or token expired.

**Recovery steps:**

1. Check `localStorage.getItem("nps_token")` in browser console — should have a valid JWT
2. If empty: user needs to log in first. Add a check in `useSettings()` to skip the query when no token exists:
   ```typescript
   enabled: !!localStorage.getItem("nps_token"),
   ```
3. If expired: implement token refresh or redirect to login page
4. For development: use legacy API key auth (`VITE_API_KEY` in `.env`)

### Error 2: Settings router not registered (404 on /settings)

**Symptoms:** All settings API calls return 404.

**Root Cause:** The settings router was not added to `api/app/routers/__init__.py` or `api/app/main.py`.

**Recovery steps:**

1. Check router registration: `grep -r "settings" api/app/routers/__init__.py api/app/main.py`
2. If missing, add: `app.include_router(settings_router, prefix="/settings", tags=["settings"])`
3. Restart API server: `make dev-api`
4. Verify: `curl http://localhost:8000/docs | grep settings` — should show settings endpoints in Swagger

### Error 3: API key creation returns 500 (missing users table FK)

**Symptoms:** Creating an API key via the settings page fails with 500 Internal Server Error.

**Root Cause:** The `api_keys.user_id` references `users.id`, but the current user context from legacy auth has `user_id=None`.

**Recovery steps:**

1. Check auth type: the legacy auth fallback sets `user_id=None` (see `api/app/middleware/auth.py` line 174-182)
2. If using legacy auth: the `POST /auth/api-keys` endpoint tries to set `user_id=user.get("user_id")` which is None → FK violation
3. Fix: ensure user is authenticated via JWT (not legacy key) before creating API keys
4. Or: make `api_keys.user_id` nullable in the ORM and allow orphan keys for legacy auth

---

## Handoff to Session 24

Session 24 ("Translation Service & i18n Completion") receives from Session 23:

### Database

- `oracle_settings` table with key-value user preferences
- Updated trigger for `updated_at` auto-update

### API

- `GET /settings` — Read all user preferences
- `PUT /settings` — Upsert user preferences (validates keys)
- Existing: `GET/POST/DELETE /auth/api-keys` — API key CRUD (unchanged, now wired to frontend)

### Frontend

- `frontend/src/pages/Settings.tsx` — Full settings page with 5 collapsible sections
- `frontend/src/components/settings/ProfileSection.tsx` — Profile editing + password change
- `frontend/src/components/settings/PreferencesSection.tsx` — Language, theme, timezone, numerology system
- `frontend/src/components/settings/OracleSettingsSection.tsx` — Default reading type, auto-daily
- `frontend/src/components/settings/ApiKeySection.tsx` — API key management UI
- `frontend/src/components/settings/AboutSection.tsx` — Static app info
- `frontend/src/components/settings/SettingsSection.tsx` — Reusable collapsible wrapper
- `frontend/src/hooks/useSettings.ts` — Settings + API key React Query hooks
- i18n keys: ~25 new settings keys in both EN and FA

### What Session 24 Extends

- Session 24 will **audit all `.tsx` files** for hardcoded strings and replace them with `t()` calls
- Session 24 will **complete** `en.json` and `fa.json` with ALL remaining keys across ALL pages
- The `PreferencesSection` locale selector from Session 23 will be the primary way users switch languages
- Session 24 may add Persian numeral formatting (`persianFormatter.ts`) and Jalali date formatting

---

## Reference: Current File State Summary

| File                                 | Current Lines | Current State                                         | Session 23 Action                                 |
| ------------------------------------ | ------------- | ----------------------------------------------------- | ------------------------------------------------- |
| `frontend/src/pages/Settings.tsx`    | 27            | Placeholder with TODOs                                | FULL REWRITE                                      |
| `frontend/src/services/api.ts`       | 192           | No settings or auth.apiKeys namespace                 | Add settings + auth sections                      |
| `frontend/src/types/index.ts`        | 411           | No settings types                                     | Add UserSettings, ApiKeyDisplay, SettingsResponse |
| `frontend/src/locales/en.json`       | 190           | 4 settings keys (title, telegram, security, language) | Add ~25 new keys                                  |
| `frontend/src/locales/fa.json`       | 190           | 4 matching Persian keys                               | Add ~25 new keys                                  |
| `frontend/src/App.tsx`               | 35            | Route `/settings` exists → Settings component         | No change                                         |
| `frontend/src/components/Layout.tsx` | 58            | Sidebar with Settings nav link                        | No change                                         |
| `api/app/routers/auth.py`            | 154           | Login, API key CRUD (create/list/revoke)              | Possibly add change-password endpoint             |
| `api/app/orm/user.py`                | 25            | User model (id, username, password_hash, role)        | No change                                         |
| `api/app/orm/api_key.py`             | 35            | APIKey model (id, user_id, key_hash, name, scopes)    | No change                                         |
| `api/app/models/auth.py`             | 35            | LoginRequest, TokenResponse, APIKeyCreate/Response    | No change                                         |
| `api/app/config.py`                  | 81            | Settings with all env vars                            | No change                                         |
