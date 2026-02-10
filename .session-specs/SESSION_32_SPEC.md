# SESSION 32 SPEC — Export & Share

**Block:** Features & Integration (Sessions 32-37)
**Estimated Duration:** 5 hours
**Complexity:** Medium-High
**Dependencies:** Session 21 (reading results display)

---

## TL;DR

- Rewrite `ExportButton.tsx` from a basic TXT/JSON exporter into a full export & share menu with PDF, image (PNG), text, and share-link options
- Create `exportReading.ts` utility module using **jsPDF** for PDF generation and **html2canvas** for image capture — both render Persian text correctly
- Build a public share API (`api/app/routers/share.py`) that generates unique share tokens for readings and serves them without auth
- Add Open Graph meta tags on the share page so shared links preview correctly on social platforms (Telegram, WhatsApp, Twitter)
- Frontend share page at `/share/:token` renders a read-only reading card accessible to anyone

---

## OBJECTIVES

1. **PDF export** — Generate a multi-page PDF of a full reading (all sections, FC60 stamp, patterns, AI interpretation) with correct Persian RTL rendering when locale is FA
2. **Image export** — Capture the reading results card as a high-resolution PNG using html2canvas
3. **Text export** — Produce a formatted plain-text summary suitable for pasting into messengers (already partially exists — enhance with all sections)
4. **Share link** — Generate a unique URL (`/share/<token>`) that displays the reading publicly without authentication, read-only
5. **Social preview** — Open Graph `<meta>` tags on shared reading pages so links show a preview card (title, summary, image)
6. **Persian correctness** — PDF and image exports render Persian text RTL with correct font embedding; share page inherits i18n locale

---

## PREREQUISITES

- [ ] Session 21 complete — `ReadingResults.tsx`, `SummaryTab.tsx`, `DetailsTab.tsx` exist and render readings
- [ ] Oracle reading endpoints functional — `GET /api/oracle/readings/:id` returns `StoredReadingResponse`
- [ ] Frontend builds without errors

**Verification:**

```bash
# ReadingResults exists and is non-trivial
wc -l frontend/src/components/oracle/ReadingResults.tsx
# Expected: ≥ 50 lines

# ExportButton exists (will be rewritten)
wc -l frontend/src/components/oracle/ExportButton.tsx
# Expected: ≥ 40 lines

# API reading endpoint exists
grep -n "readings/{reading_id}" api/app/routers/oracle.py
# Expected: route definition found

# Frontend builds
cd frontend && npx tsc --noEmit
# Expected: no errors
```

---

## FILES TO CREATE

| File                                                                | Purpose                                                                                                |
| ------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| `frontend/src/utils/exportReading.ts`                               | Export utilities: `exportAsPdf()`, `exportAsImage()`, `formatAsText()` (enhanced), `copyToClipboard()` |
| `frontend/src/utils/shareReading.ts`                                | Share utilities: `createShareLink()`, `getShareUrl()`                                                  |
| `frontend/src/pages/SharedReading.tsx`                              | Public share page — read-only reading view, no auth required                                           |
| `frontend/src/components/oracle/ExportShareMenu.tsx`                | Dropdown menu component with export/share options                                                      |
| `frontend/src/components/oracle/__tests__/ExportShareMenu.test.tsx` | Tests for the export/share menu                                                                        |
| `frontend/src/components/oracle/__tests__/SharedReading.test.tsx`   | Tests for the share page                                                                               |
| `api/app/routers/share.py`                                          | Public share endpoints: `POST /share` (create), `GET /share/:token` (view)                             |
| `api/app/models/share.py`                                           | Pydantic models: `ShareLinkCreate`, `ShareLinkResponse`, `SharedReadingResponse`                       |
| `api/app/orm/share_link.py`                                         | ORM model for `oracle_share_links` table                                                               |
| `database/migrations/012_share_links.sql`                           | Migration: `oracle_share_links` table                                                                  |
| `database/migrations/012_share_links_rollback.sql`                  | Rollback migration                                                                                     |
| `api/tests/test_share.py`                                           | Backend tests for share endpoints                                                                      |

---

## FILES TO MODIFY

| File                                                | What Changes                                                                                 |
| --------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| `frontend/src/components/oracle/ExportButton.tsx`   | REWRITE — replace with `ExportShareMenu` import or inline the new dropdown                   |
| `frontend/src/components/oracle/ReadingResults.tsx` | Replace `<ExportButton>` with `<ExportShareMenu>`, pass reading ID for share link generation |
| `frontend/src/services/api.ts`                      | Add `share` namespace: `share.create()`, `share.get()`                                       |
| `frontend/src/types/index.ts`                       | Add `ShareLink`, `SharedReadingData` types                                                   |
| `frontend/src/App.tsx`                              | Add `/share/:token` route (outside `<Layout>`, no sidebar)                                   |
| `frontend/src/locales/en.json`                      | Add ~15 export/share i18n keys                                                               |
| `frontend/src/locales/fa.json`                      | Add matching Persian translations                                                            |
| `frontend/package.json`                             | Add `jspdf` and `html2canvas` dependencies                                                   |
| `api/app/main.py`                                   | Add `share.router` with prefix `/api/share`                                                  |

---

## FILES TO DELETE

None.

---

## IMPLEMENTATION PHASES

### Phase 1: Database & Backend — Share Links (45 min)

**Tasks:**

1. Create migration `database/migrations/012_share_links.sql`:

   ```sql
   CREATE TABLE IF NOT EXISTS oracle_share_links (
       id BIGSERIAL PRIMARY KEY,
       token VARCHAR(32) UNIQUE NOT NULL,        -- random hex token
       reading_id BIGINT NOT NULL REFERENCES oracle_readings(id) ON DELETE CASCADE,
       created_by_user_id INTEGER REFERENCES oracle_users(id),
       expires_at TIMESTAMPTZ,                    -- NULL = never expires
       view_count INTEGER NOT NULL DEFAULT 0,
       is_active BOOLEAN NOT NULL DEFAULT TRUE,
       created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
   );
   CREATE INDEX idx_share_links_token ON oracle_share_links(token);
   CREATE INDEX idx_share_links_reading_id ON oracle_share_links(reading_id);
   ```

2. Create rollback migration `database/migrations/012_share_links_rollback.sql`:

   ```sql
   DROP TABLE IF EXISTS oracle_share_links;
   ```

3. Create ORM model `api/app/orm/share_link.py`:

   ```python
   class ShareLink(Base):
       __tablename__ = "oracle_share_links"
       id: Mapped[int]           # BIGSERIAL PK
       token: Mapped[str]        # VARCHAR(32) UNIQUE
       reading_id: Mapped[int]   # FK oracle_readings
       created_by_user_id: Mapped[int | None]
       expires_at: Mapped[datetime | None]
       view_count: Mapped[int]   # default 0
       is_active: Mapped[bool]   # default True
       created_at: Mapped[datetime]
   ```

4. Create Pydantic models `api/app/models/share.py`:

   ```python
   class ShareLinkCreate(BaseModel):
       reading_id: int
       expires_in_days: int | None = None  # None = permanent

   class ShareLinkResponse(BaseModel):
       token: str
       url: str              # full share URL
       expires_at: str | None
       created_at: str

   class SharedReadingResponse(BaseModel):
       reading: StoredReadingResponse
       shared_at: str
       view_count: int
   ```

5. Create share router `api/app/routers/share.py`:
   - `POST /api/share` — Auth required. Creates share link for a reading. Generates random 32-char hex token via `secrets.token_hex(16)`. Returns token + URL.
   - `GET /api/share/{token}` — **No auth required.** Looks up share link by token, increments `view_count`, returns reading data. Returns 404 if token invalid/expired/deactivated.
   - `DELETE /api/share/{token}` — Auth required. Deactivates a share link (sets `is_active = False`).

6. Register router in `api/app/main.py`:
   ```python
   from app.routers import share
   app.include_router(share.router, prefix="/api/share", tags=["share"])
   ```

**Code Pattern — Share Router:**

```python
import secrets
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

router = APIRouter()

@router.post("", response_model=ShareLinkResponse)
def create_share_link(
    body: ShareLinkCreate,
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    # Verify reading exists
    reading = db.query(OracleReading).filter_by(id=body.reading_id).first()
    if not reading:
        raise HTTPException(status_code=404, detail="Reading not found")

    token = secrets.token_hex(16)
    expires_at = None
    if body.expires_in_days:
        expires_at = datetime.now(timezone.utc) + timedelta(days=body.expires_in_days)

    link = ShareLink(token=token, reading_id=body.reading_id, ...)
    db.add(link)
    db.commit()
    return ShareLinkResponse(token=token, url=f"/share/{token}", ...)

@router.get("/{token}", response_model=SharedReadingResponse)
def get_shared_reading(token: str, db: Session = Depends(get_db)):
    # NO AUTH — public endpoint
    link = db.query(ShareLink).filter_by(token=token, is_active=True).first()
    if not link:
        raise HTTPException(status_code=404, detail="Share link not found")
    if link.expires_at and link.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=410, detail="Share link expired")
    link.view_count += 1
    db.commit()
    # Return reading data
    ...
```

#### STOP Checkpoint 1

- [ ] Migration file exists at `database/migrations/012_share_links.sql`
- [ ] ORM model imports without error
- [ ] Pydantic models validate correctly
- [ ] Share router registered in main app

```bash
grep "share" api/app/main.py
# Expected: include_router line for share

python3 -c "from app.orm.share_link import ShareLink; print('OK')"
# Expected: OK

python3 -c "from app.models.share import ShareLinkCreate, ShareLinkResponse, SharedReadingResponse; print('OK')"
# Expected: OK
```

---

### Phase 2: Frontend Types, API Client & Dependencies (30 min)

**Tasks:**

1. Install frontend dependencies:

   ```bash
   cd frontend && npm install jspdf html2canvas
   npm install --save-dev @types/html2canvas
   ```

2. Add TypeScript types to `frontend/src/types/index.ts`:

   ```typescript
   // ─── Share ───
   export interface ShareLink {
     token: string;
     url: string;
     expires_at: string | null;
     created_at: string;
   }

   export interface SharedReadingData {
     reading: StoredReading;
     shared_at: string;
     view_count: number;
   }

   export type ExportFormat = "pdf" | "image" | "text" | "json";
   ```

3. Add `share` namespace to `frontend/src/services/api.ts`:

   ```typescript
   // ─── Share ───
   export const share = {
     create: (readingId: number, expiresInDays?: number) =>
       request<import("@/types").ShareLink>("/share", {
         method: "POST",
         body: JSON.stringify({
           reading_id: readingId,
           expires_in_days: expiresInDays,
         }),
       }),
     get: (token: string) =>
       request<import("@/types").SharedReadingData>(`/share/${token}`),
     revoke: (token: string) =>
       request<void>(`/share/${token}`, { method: "DELETE" }),
   };
   ```

4. Add i18n keys to `frontend/src/locales/en.json` under `"oracle"`:

   ```json
   "export_pdf": "Export PDF",
   "export_image": "Export Image",
   "export_text": "Export Text",
   "export_json": "Export JSON",
   "share_link": "Share Link",
   "share_copy": "Copy Link",
   "share_copied": "Link copied!",
   "share_create": "Create Share Link",
   "share_creating": "Creating...",
   "share_error": "Failed to create share link",
   "share_expires": "Expires in {{days}} days",
   "share_permanent": "Permanent link",
   "share_views": "{{count}} views",
   "shared_reading_title": "NPS Oracle Reading",
   "shared_reading_footer": "Generated by NPS Oracle"
   ```

5. Add matching Persian keys to `frontend/src/locales/fa.json`.

#### STOP Checkpoint 2

- [ ] `jspdf` and `html2canvas` appear in `package.json` dependencies
- [ ] Types compile without error
- [ ] API client has share namespace

```bash
grep "jspdf" frontend/package.json
# Expected: found

grep "html2canvas" frontend/package.json
# Expected: found

cd frontend && npx tsc --noEmit
# Expected: no errors
```

---

### Phase 3: Export Utilities (60 min)

**Tasks:**

1. Create `frontend/src/utils/exportReading.ts` with four export functions:

**`formatAsText(result: ConsultationResult): string`**

- Enhanced version of existing `formatAsText` from `ExportButton.tsx`
- Include ALL sections: FC60 data, numerology, zodiac, moon, angel numbers, chaldean, ganzhi, FC60 extended, synchronicities, AI interpretation
- Format as clean, readable plain text with section headers
- Include NPS branding footer

**`exportAsPdf(elementId: string, filename: string, locale: string): Promise<void>`**

- Use `jsPDF` to generate PDF from reading content
- Strategy: Capture the reading card element via `html2canvas`, then add the canvas image to jsPDF
- This approach preserves styling, RTL layout, and Persian fonts without needing manual PDF layout
- Set PDF metadata (title, author, creation date)
- For Persian (FA locale): ensure `direction: rtl` is preserved by html2canvas capturing the rendered DOM

**`exportAsImage(elementId: string, filename: string): Promise<void>`**

- Use `html2canvas` to capture the reading card DOM element
- Scale factor 2x for high-resolution output
- Convert canvas to PNG blob
- Trigger download via `downloadBlob()` helper

**`copyToClipboard(text: string): Promise<boolean>`**

- Use `navigator.clipboard.writeText()` with fallback to `document.execCommand('copy')`
- Return success/failure boolean

**Code Pattern:**

```typescript
import jsPDF from "jspdf";
import html2canvas from "html2canvas";

export async function exportAsPdf(
  elementId: string,
  filename: string,
  locale: string,
): Promise<void> {
  const element = document.getElementById(elementId);
  if (!element) throw new Error(`Element #${elementId} not found`);

  const canvas = await html2canvas(element, {
    scale: 2,
    useCORS: true,
    logging: false,
  });

  const imgData = canvas.toDataURL("image/png");
  const pdf = new jsPDF({
    orientation: "portrait",
    unit: "mm",
    format: "a4",
  });

  const pageWidth = pdf.internal.pageSize.getWidth();
  const pageHeight = pdf.internal.pageSize.getHeight();
  const imgWidth = pageWidth - 20; // 10mm margins
  const imgHeight = (canvas.height * imgWidth) / canvas.width;

  // Multi-page support if content is tall
  let yOffset = 10;
  let remainingHeight = imgHeight;

  while (remainingHeight > 0) {
    pdf.addImage(imgData, "PNG", 10, yOffset, imgWidth, imgHeight);
    remainingHeight -= pageHeight - 20;
    if (remainingHeight > 0) {
      pdf.addPage();
      yOffset = -(imgHeight - remainingHeight) + 10;
    }
  }

  pdf.save(filename);
}
```

2. Create `frontend/src/utils/shareReading.ts`:

   ```typescript
   import { share } from "@/services/api";
   import type { ShareLink } from "@/types";

   export async function createShareLink(
     readingId: number,
     expiresInDays?: number,
   ): Promise<ShareLink> {
     return share.create(readingId, expiresInDays);
   }

   export function getShareUrl(token: string): string {
     return `${window.location.origin}/share/${token}`;
   }
   ```

#### STOP Checkpoint 3

- [ ] `exportReading.ts` compiles without error
- [ ] `shareReading.ts` compiles without error
- [ ] All four export functions have correct signatures

```bash
cd frontend && npx tsc --noEmit
# Expected: no errors

grep -c "export async function\|export function" frontend/src/utils/exportReading.ts
# Expected: ≥ 4
```

---

### Phase 4: ExportShareMenu Component (60 min)

**Tasks:**

1. Create `frontend/src/components/oracle/ExportShareMenu.tsx`:
   - Dropdown button that opens a menu with export + share options
   - Props: `result: ConsultationResult | null`, `readingId: number | null`, `readingCardRef: string` (element ID for html2canvas)
   - Menu items:
     - Export PDF (calls `exportAsPdf`)
     - Export Image (calls `exportAsImage`)
     - Export Text (calls `formatAsText` + `downloadBlob`)
     - Export JSON (existing behavior)
     - Divider
     - Share Link (calls API to create share link, shows copy button)
   - Loading states for PDF/Image generation (can take 1-2 seconds)
   - Copy-to-clipboard feedback ("Copied!" for 2 seconds)
   - Error handling for each export type
   - i18n: all labels use `t()` keys

**Code Pattern:**

```typescript
interface ExportShareMenuProps {
  result: ConsultationResult | null;
  readingId: number | null;
  readingCardId: string;  // DOM element ID for capture
}

export function ExportShareMenu({ result, readingId, readingCardId }: ExportShareMenuProps) {
  const { t, i18n } = useTranslation();
  const [menuOpen, setMenuOpen] = useState(false);
  const [shareLink, setShareLink] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [loading, setLoading] = useState<ExportFormat | null>(null);

  if (!result) return null;

  async function handleExportPdf() {
    setLoading("pdf");
    try {
      const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
      await exportAsPdf(readingCardId, `oracle-reading-${timestamp}.pdf`, i18n.language);
    } catch { /* error handling */ }
    finally { setLoading(null); }
  }

  // ... similar handlers for image, text, json, share

  return (
    <div className="relative">
      <button onClick={() => setMenuOpen(!menuOpen)} ...>
        {t("oracle.export_text")} ▾
      </button>
      {menuOpen && (
        <div className="absolute right-0 top-full mt-1 bg-nps-bg-card border ...">
          {/* Menu items */}
        </div>
      )}
    </div>
  );
}
```

2. Update `frontend/src/components/oracle/ReadingResults.tsx`:
   - Replace `<ExportButton result={result} />` with `<ExportShareMenu result={result} readingId={readingId} readingCardId="reading-card" />`
   - Add `id="reading-card"` to the tab content wrapper so html2canvas can capture it
   - Pass `readingId` down from parent (Oracle page needs to provide this after a reading is stored)

3. Rewrite `frontend/src/components/oracle/ExportButton.tsx`:
   - Either delete its contents and re-export from `ExportShareMenu`, or keep as a thin wrapper
   - The old `formatAsText` and `downloadBlob` helpers move to `exportReading.ts`

#### STOP Checkpoint 4

- [ ] `ExportShareMenu` renders with all menu items
- [ ] `ReadingResults` uses `ExportShareMenu` instead of old `ExportButton`
- [ ] Dropdown opens and closes correctly
- [ ] No TypeScript errors

```bash
cd frontend && npx tsc --noEmit
# Expected: no errors

grep "ExportShareMenu" frontend/src/components/oracle/ReadingResults.tsx
# Expected: import and usage found
```

---

### Phase 5: Public Share Page (45 min)

**Tasks:**

1. Create `frontend/src/pages/SharedReading.tsx`:
   - Route: `/share/:token`
   - Fetches reading data from `GET /api/share/:token` (no auth)
   - Renders a read-only version of the reading card
   - Shows NPS branding header + "Generated by NPS Oracle" footer
   - Includes Open Graph meta tags via `document.title` and dynamic `<meta>` tag injection
   - Handles loading, error (invalid token), and expired states
   - Supports i18n — detects language from reading data or defaults to EN
   - No sidebar, no navigation — standalone page

**Code Pattern:**

```typescript
import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { share } from "@/services/api";
import type { SharedReadingData } from "@/types";

export function SharedReading() {
  const { token } = useParams<{ token: string }>();
  const { t } = useTranslation();
  const [data, setData] = useState<SharedReadingData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!token) return;
    share.get(token)
      .then(setData)
      .catch(() => setError("Reading not found or link expired"))
      .finally(() => setLoading(false));
  }, [token]);

  // Set Open Graph meta tags dynamically
  useEffect(() => {
    if (!data) return;
    document.title = `${t("oracle.shared_reading_title")} - NPS`;
    // Set og:title, og:description meta tags
    setMetaTag("og:title", t("oracle.shared_reading_title"));
    setMetaTag("og:description", data.reading.ai_interpretation || "Oracle Reading");
    setMetaTag("og:type", "article");
  }, [data, t]);

  if (loading) return <LoadingSpinner />;
  if (error) return <ErrorCard message={error} />;
  if (!data) return null;

  return (
    <div className="min-h-screen bg-nps-bg p-6 max-w-2xl mx-auto">
      <header className="text-center mb-6">
        <h1 className="text-xl font-bold text-nps-oracle-accent">NPS Oracle</h1>
        <p className="text-xs text-nps-text-dim">{t("oracle.shared_reading_footer")}</p>
      </header>
      {/* Render read-only reading sections */}
      <ReadOnlyReading reading={data.reading} />
      <footer className="text-center mt-8 text-xs text-nps-text-dim">
        <p>{t("oracle.shared_reading_footer")}</p>
        <p>{t("oracle.share_views", { count: data.view_count })}</p>
      </footer>
    </div>
  );
}

function setMetaTag(property: string, content: string) {
  let meta = document.querySelector(`meta[property="${property}"]`);
  if (!meta) {
    meta = document.createElement("meta");
    meta.setAttribute("property", property);
    document.head.appendChild(meta);
  }
  meta.setAttribute("content", content);
}
```

2. Update `frontend/src/App.tsx` — add share route **outside** the Layout wrapper:

   ```tsx
   import { SharedReading } from "./pages/SharedReading";

   export default function App() {
     // ...
     return (
       <Routes>
         {/* Public share page — no layout/sidebar */}
         <Route path="/share/:token" element={<SharedReading />} />

         {/* Main app with layout */}
         <Route element={<Layout />}>
           <Route path="/" element={<Navigate to="/dashboard" replace />} />
           {/* ... existing routes ... */}
         </Route>
       </Routes>
     );
   }
   ```

3. The `SharedReading` page should include a "Read-only" reading view. Reuse `SummaryTab` and `DetailsTab` in read-only mode by passing the stored reading's `reading_result` parsed as a `ConsultationResult`. Add a small helper to convert `StoredReading` → `ConsultationResult`.

#### STOP Checkpoint 5

- [ ] `/share/:token` route exists in App.tsx
- [ ] SharedReading page compiles
- [ ] Page renders outside Layout (no sidebar)
- [ ] Error state renders for invalid token

```bash
grep "share/:token" frontend/src/App.tsx
# Expected: route definition found

cd frontend && npx tsc --noEmit
# Expected: no errors
```

---

### Phase 6: Persian Support & Edge Cases (30 min)

**Tasks:**

1. **PDF Persian rendering** — The html2canvas approach captures the already-rendered DOM, so Persian RTL text is preserved as-is. Verify by:
   - Switching locale to FA
   - Generating a reading
   - Exporting as PDF
   - Checking that text is right-to-left and font renders correctly
   - If `html2canvas` has issues with the Vazirmatn web font, add `html2canvas` option: `{ allowTaint: true, useCORS: true }` and ensure the font is loaded before capture via `document.fonts.ready`

2. **Image Persian rendering** — Same approach as PDF. The `html2canvas` capture preserves RTL and Persian glyphs.

3. **Text export Persian** — When locale is FA, `formatAsText()` should:
   - Use Persian section headers
   - Include both Persian and English names for numerology values
   - Add a Persian reading footer

4. **Share link edge cases:**
   - Expired links return HTTP 410 (Gone) — frontend shows "This link has expired" message
   - Deactivated links return HTTP 404 — frontend shows "Reading not found"
   - Share link for a deleted reading returns 404 (CASCADE delete handles DB)
   - Rate limit share link creation: max 10 per reading (prevent spam)

5. **Accessibility:**
   - Export menu is keyboard navigable (arrow keys, Enter, Escape to close)
   - Share link dialog has proper ARIA labels
   - Loading states announced to screen readers via `aria-live="polite"`

#### STOP Checkpoint 6

- [ ] PDF export renders Persian text correctly
- [ ] Image export renders Persian text correctly
- [ ] Text export uses localized section headers
- [ ] Expired share links show appropriate error
- [ ] Export menu is keyboard accessible

```bash
cd frontend && npx tsc --noEmit
# Expected: no errors
```

---

### Phase 7: Tests (60 min)

**Tasks:**

**Backend tests** — Create `api/tests/test_share.py`:

1. `test_create_share_link_success` — POST `/api/share` with valid reading ID → 200, returns token
2. `test_create_share_link_reading_not_found` — POST with invalid reading ID → 404
3. `test_get_shared_reading_success` — GET `/api/share/{token}` → 200, returns reading data, view_count incremented
4. `test_get_shared_reading_expired` — GET expired token → 410
5. `test_get_shared_reading_invalid_token` — GET invalid token → 404
6. `test_get_shared_reading_deactivated` — GET deactivated link → 404
7. `test_revoke_share_link` — DELETE `/api/share/{token}` → 200, link deactivated
8. `test_create_share_link_no_auth` — POST without auth → 401
9. `test_get_shared_reading_no_auth_required` — GET shared reading without auth → 200 (public)
10. `test_share_link_view_count_increments` — GET same token twice → view_count == 2

**Frontend tests** — Create `frontend/src/components/oracle/__tests__/ExportShareMenu.test.tsx`:

1. `renders nothing when result is null` — No menu rendered
2. `renders export menu button when result exists` — Button visible
3. `opens dropdown on click` — Menu items appear
4. `calls formatAsText for text export` — Mock + verify
5. `shows share link creation button` — Verify button present
6. `copies share link to clipboard` — Mock clipboard API
7. `shows loading state during PDF export` — Loading indicator visible
8. `handles export error gracefully` — Error message shown
9. `closes menu on outside click` — Menu dismissed
10. `keyboard navigation works` — Escape closes menu

**Frontend tests** — Create `frontend/src/components/oracle/__tests__/SharedReading.test.tsx`:

1. `renders loading state initially` — Spinner visible
2. `renders reading data on success` — Reading sections visible
3. `renders error for invalid token` — Error message shown
4. `renders outside Layout (no sidebar)` — No nav elements
5. `sets document title with reading info` — Title updated

#### STOP Checkpoint 7 (FINAL)

- [ ] All backend tests pass
- [ ] All frontend tests pass
- [ ] No TypeScript errors
- [ ] No lint errors

```bash
# Backend tests
cd api && python3 -m pytest tests/test_share.py -v
# Expected: 10 tests pass

# Frontend tests
cd frontend && npx vitest run --reporter=verbose
# Expected: all tests pass

# Type check
cd frontend && npx tsc --noEmit
# Expected: no errors

# Lint
cd frontend && npx eslint src/ --ext .ts,.tsx --quiet
# Expected: no errors
```

---

## TESTS TO WRITE

### Backend (`api/tests/test_share.py`)

| #   | Test                                       | Verifies                               |
| --- | ------------------------------------------ | -------------------------------------- |
| 1   | `test_create_share_link_success`           | POST creates share link, returns token |
| 2   | `test_create_share_link_reading_not_found` | 404 for invalid reading                |
| 3   | `test_get_shared_reading_success`          | Public GET returns reading data        |
| 4   | `test_get_shared_reading_expired`          | 410 for expired link                   |
| 5   | `test_get_shared_reading_invalid_token`    | 404 for bad token                      |
| 6   | `test_get_shared_reading_deactivated`      | 404 for deactivated link               |
| 7   | `test_revoke_share_link`                   | DELETE deactivates link                |
| 8   | `test_create_share_link_no_auth`           | 401 without auth                       |
| 9   | `test_get_shared_reading_no_auth_required` | Public access works                    |
| 10  | `test_share_link_view_count_increments`    | View counter works                     |

### Frontend (`frontend/src/components/oracle/__tests__/ExportShareMenu.test.tsx`)

| #   | Test                                  | Verifies              |
| --- | ------------------------------------- | --------------------- |
| 11  | `renders nothing when result is null` | Null guard works      |
| 12  | `renders export menu button`          | Button present        |
| 13  | `opens dropdown on click`             | Menu items visible    |
| 14  | `calls formatAsText for text export`  | Text export works     |
| 15  | `shows share link button`             | Share option present  |
| 16  | `copies share link to clipboard`      | Clipboard integration |
| 17  | `shows loading during PDF export`     | Loading state         |
| 18  | `handles export error`                | Error feedback        |
| 19  | `closes menu on outside click`        | Click-away dismiss    |
| 20  | `keyboard navigation`                 | Escape closes menu    |

### Frontend (`frontend/src/components/oracle/__tests__/SharedReading.test.tsx`)

| #   | Test                              | Verifies           |
| --- | --------------------------------- | ------------------ |
| 21  | `renders loading state`           | Spinner on load    |
| 22  | `renders reading data on success` | Full reading shown |
| 23  | `renders error for invalid token` | Error message      |
| 24  | `renders outside Layout`          | No sidebar         |
| 25  | `sets document title`             | OG metadata        |

---

## ACCEPTANCE CRITERIA

| #   | Criterion                          | Verify                                                                                           |
| --- | ---------------------------------- | ------------------------------------------------------------------------------------------------ |
| 1   | PDF export downloads a valid PDF   | Open exported file in PDF viewer — all sections present                                          |
| 2   | Image export downloads a PNG       | Open exported file — reading card captured clearly                                               |
| 3   | Text export downloads a .txt       | Open file — all sections, clean formatting                                                       |
| 4   | JSON export works (existing)       | Download and parse — valid JSON                                                                  |
| 5   | Share link creates successfully    | `curl -X POST /api/share -d '{"reading_id": 1}' -H "Authorization: Bearer ..."` → 200 with token |
| 6   | Share link loads publicly          | `curl /api/share/{token}` (no auth header) → 200 with reading data                               |
| 7   | Expired share returns 410          | Create with `expires_in_days: 0`, wait, request → 410                                            |
| 8   | Persian PDF renders RTL            | Switch to FA locale, export PDF, verify Persian text is RTL                                      |
| 9   | Persian image renders RTL          | Switch to FA locale, export image, verify                                                        |
| 10  | Share page renders without sidebar | Navigate to `/share/{token}` — no nav, standalone page                                           |
| 11  | OG meta tags present on share page | View source of `/share/{token}` — `og:title`, `og:description` meta tags                         |
| 12  | All 25 tests pass                  | `cd api && pytest tests/test_share.py -v && cd ../frontend && npx vitest run`                    |
| 13  | No TypeScript errors               | `cd frontend && npx tsc --noEmit`                                                                |
| 14  | Share link revocation works        | DELETE `/api/share/{token}` → subsequent GET returns 404                                         |

**Verify all at once:**

```bash
cd api && python3 -m pytest tests/test_share.py -v && \
cd ../frontend && npx tsc --noEmit && npx vitest run --reporter=verbose
```

---

## ERROR SCENARIOS

### Scenario 1: html2canvas fails to capture element

**Problem:** `html2canvas` throws if the target element has cross-origin images, iframes, or certain CSS properties.
**Fix:**

1. Wrap `html2canvas` calls in try/catch
2. Show user-friendly error: "PDF export failed — try refreshing the page"
3. Fallback: offer text export as alternative
4. Ensure no cross-origin images in reading card (use data URIs or same-origin assets only)
5. Set `html2canvas({ allowTaint: true, useCORS: true })` for maximum compatibility

### Scenario 2: Share link creation fails (DB constraint violation)

**Problem:** Token collision (extremely unlikely with `secrets.token_hex(16)` = 32 chars, 2^128 possibilities) or FK violation if reading was deleted between check and insert.
**Fix:**

1. Catch `IntegrityError` in share router
2. On token collision: retry with new token (max 3 attempts)
3. On FK violation: return 404 "Reading no longer exists"
4. Frontend shows error toast: "Could not create share link — please try again"

### Scenario 3: jsPDF not loaded (bundle issue)

**Problem:** `jsPDF` is a large library (~300KB). If code-split chunk fails to load, the import will throw.
**Fix:**

1. Use dynamic import: `const jsPDF = (await import("jspdf")).default`
2. Catch import error and show: "PDF export unavailable — check your internet connection"
3. Consider adding jsPDF to a separate chunk via Vite manual chunks config for better caching

---

## HANDOFF

**Created:**

- `frontend/src/utils/exportReading.ts` — Export utilities (PDF, image, text, clipboard)
- `frontend/src/utils/shareReading.ts` — Share link helpers
- `frontend/src/pages/SharedReading.tsx` — Public share page
- `frontend/src/components/oracle/ExportShareMenu.tsx` — Export/share dropdown menu
- `api/app/routers/share.py` — Share endpoints (create, view, revoke)
- `api/app/models/share.py` — Share Pydantic models
- `api/app/orm/share_link.py` — ShareLink ORM model
- `database/migrations/012_share_links.sql` — Share links table
- `database/migrations/012_share_links_rollback.sql` — Rollback
- `api/tests/test_share.py` — 10 backend tests
- `frontend/src/components/oracle/__tests__/ExportShareMenu.test.tsx` — 10 frontend tests
- `frontend/src/components/oracle/__tests__/SharedReading.test.tsx` — 5 frontend tests

**Modified:**

- `frontend/src/components/oracle/ExportButton.tsx` — Rewritten or replaced by ExportShareMenu
- `frontend/src/components/oracle/ReadingResults.tsx` — Uses ExportShareMenu, adds `id="reading-card"` for capture
- `frontend/src/services/api.ts` — Added `share` namespace
- `frontend/src/types/index.ts` — Added `ShareLink`, `SharedReadingData`, `ExportFormat` types
- `frontend/src/App.tsx` — Added `/share/:token` route outside Layout
- `frontend/src/locales/en.json` — Added ~15 export/share i18n keys
- `frontend/src/locales/fa.json` — Added matching Persian translations
- `frontend/package.json` — Added `jspdf`, `html2canvas` dependencies
- `api/app/main.py` — Registered share router

**Deleted:** None

**Next session (Session 33) needs:**

- Share endpoints working (Session 33's Telegram bot may use share links to send reading summaries to users)
- Export utilities available (Telegram bot can reuse `formatAsText()` for reading text output)
- `oracle_share_links` table exists in database
