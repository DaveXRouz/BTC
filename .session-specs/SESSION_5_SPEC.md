# SESSION 5 SPEC — Location System Upgrade & Persian Keyboard Polish

**Block:** Foundation (Sessions 1-5)
**Estimated Duration:** 4-5 hours
**Complexity:** Medium-High
**Dependencies:** Session 1 (schema), Session 2 (auth), Session 3 (user API + ownership), Session 4 (profile form + validation UI)

---

## TL;DR

- Replace the hardcoded 10-country `COUNTRIES` constant with API-backed static JSON data (250+ countries, top cities per country, bilingual EN+FA names)
- Rewrite `LocationService` with 4 new methods: `get_countries()`, `get_cities()`, `get_timezone()`, `search_cities()` — all backed by static JSON with Nominatim as a fallback
- Add 3 new API endpoints: `GET /api/location/countries`, `GET /api/location/countries/{code}/cities`, `GET /api/location/timezone`
- Rewrite `LocationSelector.tsx` with searchable country dropdown, cascading city select, manual coordinate input, bilingual labels
- Polish `PersianKeyboard.tsx` with Shift key layer, better positioning, mobile touch support
- Add 6 new Pydantic models, 12+ API tests, 12+ frontend component tests

---

## OBJECTIVES

1. **Static bilingual location data** — 250+ countries and top cities with EN + FA names, coordinates, and timezones stored as JSON files loaded at API startup
2. **Location service upgrade** — 4 new methods that serve data from static JSON instantly, falling back to Nominatim only when the static data doesn't cover the query
3. **3 new location endpoints** — Countries list, cities-by-country, and timezone lookup — all fast (< 10ms) because they hit static data
4. **LocationSelector rewrite** — Searchable country dropdown (filterable by typing), cascading city select that updates when country changes, manual lat/lng input, auto-detect via browser geolocation
5. **Persian keyboard polish** — Shift key toggles between base and shifted character layers, smarter positioning relative to input field, mobile touch event handling
6. **Full test coverage** — 12+ API tests for new endpoints, 12+ frontend tests for LocationSelector and PersianKeyboard

---

## PREREQUISITES

- [ ] Session 4 complete — Profile form working with existing LocationSelector
- [ ] `api/app/services/location_service.py` exists (166 lines, 2 methods)
- [ ] `api/app/routers/location.py` exists (60 lines, 2 endpoints)
- [ ] `api/app/models/location.py` exists (24 lines, 2 models)
- [ ] `frontend/src/components/oracle/LocationSelector.tsx` exists (107 lines)
- [ ] `frontend/src/components/oracle/PersianKeyboard.tsx` exists (91 lines)
- [ ] `frontend/src/utils/persianKeyboardLayout.ts` exists (9 lines)
- [ ] `frontend/src/utils/geolocationHelpers.ts` exists (52 lines)
- Verification:
  ```bash
  test -f api/app/services/location_service.py && \
  test -f api/app/routers/location.py && \
  test -f api/app/models/location.py && \
  test -f frontend/src/components/oracle/LocationSelector.tsx && \
  test -f frontend/src/components/oracle/PersianKeyboard.tsx && \
  test -f frontend/src/utils/persianKeyboardLayout.ts && \
  test -f frontend/src/utils/geolocationHelpers.ts && \
  echo "Prerequisites OK"
  ```

---

## EXISTING CODE ANALYSIS

### What Already Works (Keep & Enhance)

**LocationService** in `api/app/services/location_service.py` (166 lines):

- `get_coordinates(city, country)` — Nominatim geocoding with rate limiting + caching
- `detect_location(ip)` — ipapi.co IP geolocation with caching
- Thread-safe caches with TTL (30 days for cities, 7 days for IP)
- Rate limiting: Nominatim 1 req/sec via `_nominatim_lock`
- `_get_timezone(lat, lon)` — Optional `timezonefinder` dependency

**Location router** in `api/app/routers/location.py` (60 lines):

- `GET /api/location/coordinates` — City geocoding (scope: `oracle:read`)
- `GET /api/location/detect` — IP detection (scope: `oracle:read`)

**Location models** in `api/app/models/location.py` (24 lines):

- `CoordinatesResponse` — city, country, lat, lon, timezone, cached
- `LocationDetectResponse` — ip, city, country, country_code, lat, lon, timezone, cached

**LocationSelector** in `frontend/src/components/oracle/LocationSelector.tsx` (107 lines):

- Auto-detect via browser geolocation
- Country select from hardcoded `COUNTRIES` (10 entries)
- City text input (free-form)
- Coordinates display

**PersianKeyboard** in `frontend/src/components/oracle/PersianKeyboard.tsx` (91 lines):

- 4-row character grid from `PERSIAN_ROWS`
- Space + Backspace bottom row
- Escape to close, backdrop click to close
- RTL direction

**geolocationHelpers** in `frontend/src/utils/geolocationHelpers.ts` (52 lines):

- `getCurrentPosition(timeout)` — Browser geolocation wrapper
- `COUNTRIES` — Hardcoded 10-country record with default coordinates

### What's Missing / Needs Upgrade

| Component               | Current State                                 | What Session 5 Adds                                                  |
| ----------------------- | --------------------------------------------- | -------------------------------------------------------------------- |
| Country data            | 10 hardcoded countries in frontend            | 250+ countries with EN+FA names from API                             |
| City data               | Free-form text input                          | Top cities per country from API, searchable                          |
| Timezone lookup         | Optional `timezonefinder` Python package      | Static timezone per country/city in JSON, no external dependency     |
| Location search         | Nominatim only (slow, rate-limited, external) | Static JSON first (instant), Nominatim fallback                      |
| Location endpoints      | 2 endpoints (coordinates, detect)             | 5 endpoints (+ countries, cities, timezone)                          |
| Location models         | 2 Pydantic models                             | 8 Pydantic models                                                    |
| LocationSelector UI     | Basic dropdown + text input                   | Searchable dropdown, cascading city, manual coords, bilingual labels |
| PersianKeyboard         | Single character layer only                   | Shift key toggles second layer (numbers, diacritics)                 |
| Keyboard positioning    | `absolute left-0 right-0 top-full`            | Smart positioning that avoids viewport overflow                      |
| Mobile keyboard         | Click events only                             | Touch events (`onTouchStart`) for mobile responsiveness              |
| Persian keyboard layout | 4 rows, 38 characters                         | 4 base rows + 4 shift rows (numbers, diacritics, punctuation)        |

---

## FILES TO CREATE

- `api/data/countries.json` — 250+ countries with EN name, FA name, ISO code, coordinates, timezone, phone code
- `api/data/cities_by_country.json` — Top 5-10 cities per country with EN name, FA name, coordinates

## FILES TO MODIFY

- `api/app/services/location_service.py` (166 lines) — REWRITE: add static data loading at module level, 4 new methods
- `api/app/routers/location.py` (60 lines) — MODIFY: add 3 new endpoints
- `api/app/models/location.py` (24 lines) — MODIFY: add 6 new Pydantic models
- `frontend/src/components/oracle/LocationSelector.tsx` (107 lines) — REWRITE: searchable country, cascading city, manual coordinates, bilingual
- `frontend/src/components/oracle/PersianKeyboard.tsx` (91 lines) — POLISH: Shift key, positioning, mobile touch
- `frontend/src/utils/persianKeyboardLayout.ts` (9 lines) — MODIFY: add shift character mappings
- `frontend/src/utils/geolocationHelpers.ts` (52 lines) — MODIFY: keep `getCurrentPosition`, remove `COUNTRIES` constant (replaced by API)
- `frontend/src/locales/en.json` — ADD new translation keys for location & keyboard
- `frontend/src/locales/fa.json` — ADD new translation keys for location & keyboard
- `api/tests/test_location.py` (254 lines) — ADD 12+ new tests for new endpoints and service methods

## FILES TO DELETE

- None

---

## IMPLEMENTATION PHASES

### Phase 1: Static Data Foundation (~60 min)

**Tasks:**

1. Create `api/data/countries.json` — a JSON array of 250+ country objects:

   ```json
   [
     {
       "code": "IR",
       "name_en": "Iran",
       "name_fa": "\u0627\u06cc\u0631\u0627\u0646",
       "latitude": 35.6892,
       "longitude": 51.389,
       "timezone": "Asia/Tehran",
       "timezone_offset_hours": 3,
       "timezone_offset_minutes": 30,
       "phone_code": "+98"
     },
     {
       "code": "US",
       "name_en": "United States",
       "name_fa": "\u0627\u06cc\u0627\u0644\u0627\u062a \u0645\u062a\u062d\u062f\u0647",
       "latitude": 38.8951,
       "longitude": -77.0364,
       "timezone": "America/New_York",
       "timezone_offset_hours": -5,
       "timezone_offset_minutes": 0,
       "phone_code": "+1"
     }
   ]
   ```

   **Coverage requirements:**
   - All 249 ISO 3166-1 alpha-2 countries
   - Persian name for every country (essential for RTL/FA locale)
   - Default coordinates point to capital city
   - Timezone is the capital/most-populated city's IANA timezone
   - `timezone_offset_hours` / `timezone_offset_minutes` for quick UTC offset (without needing tz database lookups)

2. Create `api/data/cities_by_country.json` — a JSON object keyed by ISO country code:

   ```json
   {
     "IR": [
       {
         "name_en": "Tehran",
         "name_fa": "\u062a\u0647\u0631\u0627\u0646",
         "latitude": 35.6892,
         "longitude": 51.389,
         "timezone": "Asia/Tehran"
       },
       {
         "name_en": "Isfahan",
         "name_fa": "\u0627\u0635\u0641\u0647\u0627\u0646",
         "latitude": 32.6546,
         "longitude": 51.668,
         "timezone": "Asia/Tehran"
       },
       {
         "name_en": "Shiraz",
         "name_fa": "\u0634\u06cc\u0631\u0627\u0632",
         "latitude": 29.5918,
         "longitude": 52.5837,
         "timezone": "Asia/Tehran"
       },
       {
         "name_en": "Mashhad",
         "name_fa": "\u0645\u0634\u0647\u062f",
         "latitude": 36.2605,
         "longitude": 59.6168,
         "timezone": "Asia/Tehran"
       },
       {
         "name_en": "Tabriz",
         "name_fa": "\u062a\u0628\u0631\u06cc\u0632",
         "latitude": 38.0962,
         "longitude": 46.2738,
         "timezone": "Asia/Tehran"
       }
     ],
     "US": [
       {
         "name_en": "New York",
         "name_fa": "\u0646\u06cc\u0648\u06cc\u0648\u0631\u06a9",
         "latitude": 40.7128,
         "longitude": -74.006,
         "timezone": "America/New_York"
       },
       {
         "name_en": "Los Angeles",
         "name_fa": "\u0644\u0633 \u0622\u0646\u062c\u0644\u0633",
         "latitude": 34.0522,
         "longitude": -118.2437,
         "timezone": "America/Los_Angeles"
       }
     ]
   }
   ```

   **Coverage requirements:**
   - Top 5-10 cities per country (by population)
   - Bilingual names (EN + FA) for all cities
   - Priority countries (IR, US, UK, DE, FR, TR, AE, CA, AU, IN, AF, IQ, PK, SA, EG) get 8-10 cities
   - Other countries get 3-5 cities
   - Each city has its own timezone (important for countries spanning multiple zones like US, RU, AU)

3. Load both JSON files at module level in `location_service.py` using `Path(__file__).resolve().parents[2] / "data"`:

   ```python
   from pathlib import Path
   import json

   _DATA_DIR = Path(__file__).resolve().parents[2] / "data"

   def _load_json(filename: str) -> Any:
       path = _DATA_DIR / filename
       with open(path, encoding="utf-8") as f:
           return json.load(f)

   _COUNTRIES: list[dict] = _load_json("countries.json")
   _CITIES: dict[str, list[dict]] = _load_json("cities_by_country.json")

   # Index for fast lookup
   _COUNTRY_BY_CODE: dict[str, dict] = {c["code"]: c for c in _COUNTRIES}
   ```

**Checkpoint:**

- [ ] `api/data/countries.json` exists with 249+ entries
- [ ] `api/data/cities_by_country.json` exists with entries for at least 50 countries
- [ ] Every country entry has: code, name_en, name_fa, latitude, longitude, timezone
- [ ] Every city entry has: name_en, name_fa, latitude, longitude, timezone
- [ ] Persian text is valid UTF-8 (no mojibake)
- Verify:
  ```bash
  python3 -c "
  import json
  countries = json.load(open('api/data/countries.json'))
  cities = json.load(open('api/data/cities_by_country.json'))
  assert len(countries) >= 249, f'Only {len(countries)} countries'
  assert len(cities) >= 50, f'Only {len(cities)} country city lists'
  assert all(c.get('name_fa') for c in countries), 'Missing FA names'
  ir_cities = cities.get('IR', [])
  assert len(ir_cities) >= 5, f'Iran has only {len(ir_cities)} cities'
  print(f'Countries: {len(countries)}, City lists: {len(cities)}, Iran cities: {len(ir_cities)}')
  print('Static data OK')
  "
  ```

STOP if checkpoint fails

---

### Phase 2: Location Service Rewrite (~60 min)

**Tasks:**

1. Keep existing `get_coordinates()` and `detect_location()` methods unchanged (backward compatible).

2. Add module-level JSON loading (from Phase 1) to top of `location_service.py`.

3. Add 4 new methods to `LocationService`:

   **`get_countries(lang: str = "en") -> list[dict]`**

   ```python
   def get_countries(self, lang: str = "en") -> list[dict]:
       """Return all countries sorted alphabetically by name in requested language.

       Args:
           lang: 'en' for English names, 'fa' for Persian names.

       Returns:
           List of dicts with keys: code, name, latitude, longitude, timezone.
           'name' is name_en or name_fa depending on lang parameter.
       """
       name_key = "name_fa" if lang == "fa" else "name_en"
       result = [
           {
               "code": c["code"],
               "name": c[name_key],
               "latitude": c["latitude"],
               "longitude": c["longitude"],
               "timezone": c["timezone"],
               "timezone_offset_hours": c["timezone_offset_hours"],
               "timezone_offset_minutes": c["timezone_offset_minutes"],
           }
           for c in _COUNTRIES
       ]
       result.sort(key=lambda x: x["name"])
       return result
   ```

   **`get_cities(country_code: str, lang: str = "en") -> list[dict]`**

   ```python
   def get_cities(self, country_code: str, lang: str = "en") -> list[dict]:
       """Return cities for a country, sorted alphabetically.

       Args:
           country_code: ISO 3166-1 alpha-2 code (e.g., 'IR', 'US').
           lang: 'en' or 'fa'.

       Returns:
           List of city dicts with keys: name, latitude, longitude, timezone.
           Empty list if country_code not found.
       """
       cities = _CITIES.get(country_code.upper(), [])
       name_key = "name_fa" if lang == "fa" else "name_en"
       result = [
           {
               "name": c[name_key],
               "latitude": c["latitude"],
               "longitude": c["longitude"],
               "timezone": c["timezone"],
           }
           for c in cities
       ]
       result.sort(key=lambda x: x["name"])
       return result
   ```

   **`get_timezone(country_code: str, city_name: str | None = None) -> dict | None`**

   ```python
   def get_timezone(
       self, country_code: str, city_name: str | None = None
   ) -> dict | None:
       """Get timezone info for a country/city.

       If city_name provided, looks up the specific city's timezone.
       Otherwise returns the country's default timezone.

       Returns:
           Dict with keys: timezone (IANA), offset_hours, offset_minutes.
           None if country_code not found.
       """
       country = _COUNTRY_BY_CODE.get(country_code.upper())
       if not country:
           return None

       if city_name:
           cities = _CITIES.get(country_code.upper(), [])
           for c in cities:
               if c["name_en"].lower() == city_name.lower() or c["name_fa"] == city_name:
                   return {
                       "timezone": c["timezone"],
                       "offset_hours": country["timezone_offset_hours"],
                       "offset_minutes": country["timezone_offset_minutes"],
                   }

       return {
           "timezone": country["timezone"],
           "offset_hours": country["timezone_offset_hours"],
           "offset_minutes": country["timezone_offset_minutes"],
       }
   ```

   **`search_cities(query: str, country_code: str | None = None, lang: str = "en", limit: int = 10) -> list[dict]`**

   ```python
   def search_cities(
       self,
       query: str,
       country_code: str | None = None,
       lang: str = "en",
       limit: int = 10,
   ) -> list[dict]:
       """Search cities by name prefix across all countries or within one.

       Searches both EN and FA names regardless of lang parameter.
       Returns results in the requested language.

       Args:
           query: Search string (minimum 1 character).
           country_code: Optional ISO code to limit search to one country.
           lang: 'en' or 'fa' for result name language.
           limit: Maximum results to return (default 10, max 50).

       Returns:
           List of matching city dicts with: name, country_code, country_name, latitude, longitude, timezone.
       """
       query_lower = query.lower().strip()
       if not query_lower:
           return []

       limit = min(limit, 50)
       name_key = "name_fa" if lang == "fa" else "name_en"
       results: list[dict] = []

       search_countries = (
           [country_code.upper()] if country_code else list(_CITIES.keys())
       )

       for code in search_countries:
           cities = _CITIES.get(code, [])
           country = _COUNTRY_BY_CODE.get(code)
           if not country:
               continue

           for city in cities:
               if (
                   city["name_en"].lower().startswith(query_lower)
                   or city["name_fa"].startswith(query)
               ):
                   results.append({
                       "name": city[name_key],
                       "country_code": code,
                       "country_name": country[name_key],
                       "latitude": city["latitude"],
                       "longitude": city["longitude"],
                       "timezone": city["timezone"],
                   })
                   if len(results) >= limit:
                       return results

       return results
   ```

4. Update existing `get_coordinates()` to check static data first before hitting Nominatim:

   ```python
   def get_coordinates(self, city: str, country: str | None = None) -> dict | None:
       # Check static data first (instant, no network)
       static_result = self._lookup_static(city, country)
       if static_result:
           return static_result

       # Fall through to existing Nominatim logic...
       # (keep all existing code below unchanged)
   ```

   ```python
   def _lookup_static(self, city: str, country: str | None = None) -> dict | None:
       """Try to find city in static data. Returns None if not found."""
       city_lower = city.lower().strip()

       if country:
           # Find country code from name
           code = None
           for c in _COUNTRIES:
               if c["name_en"].lower() == country.lower() or c["name_fa"] == country:
                   code = c["code"]
                   break
           if code:
               for c_city in _CITIES.get(code, []):
                   if c_city["name_en"].lower() == city_lower or c_city["name_fa"] == city:
                       return {
                           "city": c_city["name_en"],
                           "country": country,
                           "latitude": c_city["latitude"],
                           "longitude": c_city["longitude"],
                           "timezone": c_city["timezone"],
                           "cached": False,
                       }
       else:
           # Search all countries
           for code, cities in _CITIES.items():
               for c_city in cities:
                   if c_city["name_en"].lower() == city_lower or c_city["name_fa"] == city:
                       country_data = _COUNTRY_BY_CODE.get(code)
                       return {
                           "city": c_city["name_en"],
                           "country": country_data["name_en"] if country_data else None,
                           "latitude": c_city["latitude"],
                           "longitude": c_city["longitude"],
                           "timezone": c_city["timezone"],
                           "cached": False,
                       }

       return None
   ```

**Checkpoint:**

- [ ] `LocationService.get_countries()` returns 249+ entries
- [ ] `LocationService.get_countries(lang="fa")` returns Persian names sorted alphabetically
- [ ] `LocationService.get_cities("IR")` returns 5+ Iranian cities
- [ ] `LocationService.get_timezone("IR")` returns `{"timezone": "Asia/Tehran", ...}`
- [ ] `LocationService.search_cities("Teh")` returns Tehran as first result
- [ ] Existing `get_coordinates("Tehran")` now hits static data first (no Nominatim call)
- Verify:
  ```bash
  cd api && python3 -c "
  from app.services.location_service import LocationService
  svc = LocationService()
  countries = svc.get_countries()
  assert len(countries) >= 249, f'Only {len(countries)}'
  fa_countries = svc.get_countries(lang='fa')
  assert fa_countries[0]['name'] != countries[0]['name'], 'FA names should differ from EN'
  ir_cities = svc.get_cities('IR')
  assert len(ir_cities) >= 5
  tz = svc.get_timezone('IR')
  assert tz['timezone'] == 'Asia/Tehran'
  results = svc.search_cities('Teh')
  assert len(results) >= 1 and 'Tehran' in results[0]['name']
  # Static lookup should find Tehran without Nominatim
  coords = svc.get_coordinates('Tehran', 'Iran')
  assert coords is not None and coords['latitude'] > 35
  print('Location service OK')
  "
  ```

STOP if checkpoint fails

---

### Phase 3: Location API Endpoints (~30 min)

**Tasks:**

1. Add 6 new Pydantic models to `api/app/models/location.py`:

   ```python
   class CountryResponse(BaseModel):
       code: str
       name: str
       latitude: float
       longitude: float
       timezone: str
       timezone_offset_hours: int
       timezone_offset_minutes: int

   class CountryListResponse(BaseModel):
       countries: list[CountryResponse]
       total: int

   class CityResponse(BaseModel):
       name: str
       latitude: float
       longitude: float
       timezone: str

   class CityListResponse(BaseModel):
       cities: list[CityResponse]
       country_code: str
       total: int

   class TimezoneResponse(BaseModel):
       timezone: str
       offset_hours: int
       offset_minutes: int

   class CitySearchResponse(BaseModel):
       name: str
       country_code: str
       country_name: str
       latitude: float
       longitude: float
       timezone: str
   ```

2. Add 3 new endpoints to `api/app/routers/location.py`:

   **Endpoint 1: `GET /api/location/countries`**

   ```python
   @router.get(
       "/countries",
       response_model=CountryListResponse,
       dependencies=[Depends(require_scope("oracle:read"))],
   )
   def list_countries(
       lang: str = Query("en", pattern=r"^(en|fa)$"),
   ):
       """List all countries with bilingual names."""
       countries = _svc.get_countries(lang=lang)
       return CountryListResponse(
           countries=[CountryResponse(**c) for c in countries],
           total=len(countries),
       )
   ```

   **Endpoint 2: `GET /api/location/countries/{country_code}/cities`**

   ```python
   @router.get(
       "/countries/{country_code}/cities",
       response_model=CityListResponse,
       dependencies=[Depends(require_scope("oracle:read"))],
   )
   def list_cities(
       country_code: str = Path(..., min_length=2, max_length=2),
       lang: str = Query("en", pattern=r"^(en|fa)$"),
   ):
       """List top cities for a country."""
       cities = _svc.get_cities(country_code, lang=lang)
       return CityListResponse(
           cities=[CityResponse(**c) for c in cities],
           country_code=country_code.upper(),
           total=len(cities),
       )
   ```

   **Endpoint 3: `GET /api/location/timezone`**

   ```python
   @router.get(
       "/timezone",
       response_model=TimezoneResponse,
       dependencies=[Depends(require_scope("oracle:read"))],
   )
   def get_timezone(
       country_code: str = Query(..., min_length=2, max_length=2),
       city: str | None = Query(None),
   ):
       """Get timezone for a country/city combination."""
       result = _svc.get_timezone(country_code, city)
       if result is None:
           raise HTTPException(
               status_code=status.HTTP_404_NOT_FOUND,
               detail=f"Country '{country_code}' not found",
           )
       return TimezoneResponse(**result)
   ```

3. Add `Path` import to `location.py` (FastAPI's Path, not pathlib):

   ```python
   from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request, status
   ```

4. Update model imports in `location.py`:

   ```python
   from app.models.location import (
       CityListResponse,
       CityResponse,
       CoordinatesResponse,
       CountryListResponse,
       CountryResponse,
       LocationDetectResponse,
       TimezoneResponse,
   )
   ```

**Checkpoint:**

- [ ] `GET /api/location/countries` returns 249+ countries
- [ ] `GET /api/location/countries?lang=fa` returns Persian names
- [ ] `GET /api/location/countries/IR/cities` returns 5+ cities
- [ ] `GET /api/location/timezone?country_code=IR` returns `Asia/Tehran`
- [ ] All 3 new endpoints require `oracle:read` scope
- [ ] Unauthenticated requests return 401
- Verify: `grep -c "@router\." api/app/routers/location.py` — should return 5

STOP if checkpoint fails

---

### Phase 4: LocationSelector Rewrite (~60 min)

**Tasks:**

1. Rewrite `frontend/src/components/oracle/LocationSelector.tsx` with:

   **New features:**
   - Searchable country dropdown with type-to-filter (not just a plain `<select>`)
   - Cascading city select that loads cities when country changes (from API)
   - Manual coordinate input fields (lat/lng) for precision
   - Auto-detect via browser geolocation (keep existing behavior)
   - Bilingual labels based on current locale (EN/FA)
   - Loading state while fetching cities from API

   **Data flow:**

   ```
   User selects country → fetch cities from API → show city dropdown
   User selects city → coordinates auto-fill from city data
   User can override coordinates manually
   OR: User clicks auto-detect → browser geolocation fills lat/lng
   ```

   **Component structure:**

   ```tsx
   function LocationSelector({ value, onChange }: LocationSelectorProps) {
     const { t, i18n } = useTranslation();
     const lang = i18n.language === "fa" ? "fa" : "en";

     // State
     const [countries, setCountries] = useState<Country[]>([]);
     const [cities, setCities] = useState<City[]>([]);
     const [countrySearch, setCountrySearch] = useState("");
     const [isLoadingCountries, setIsLoadingCountries] = useState(true);
     const [isLoadingCities, setIsLoadingCities] = useState(false);
     const [isDetecting, setIsDetecting] = useState(false);
     const [detectError, setDetectError] = useState<string | null>(null);
     const [showManualCoords, setShowManualCoords] = useState(false);

     // Fetch countries on mount
     useEffect(() => {
       fetchCountries(lang)
         .then(setCountries)
         .finally(() => setIsLoadingCountries(false));
     }, [lang]);

     // Fetch cities when country changes
     useEffect(() => {
       if (value?.countryCode) {
         setIsLoadingCities(true);
         fetchCities(value.countryCode, lang)
           .then(setCities)
           .finally(() => setIsLoadingCities(false));
       }
     }, [value?.countryCode, lang]);

     // ... handlers and JSX
   }
   ```

   **Filtered country list:**

   ```tsx
   const filteredCountries = countries.filter((c) =>
     c.name.toLowerCase().includes(countrySearch.toLowerCase()),
   );
   ```

   **Use a dropdown with search input** — NOT a combobox library. Keep it simple:
   - Text input that filters the `<select>` options below it
   - Or a text input with a dropdown list (`<datalist>`) — simpler, native

   **Decision:** Use `<input>` + `<datalist>` for country search (native browser autocomplete). This avoids external dependencies and works on mobile. For city select, use a plain `<select>` since the list is small (5-10 items).

2. Update `frontend/src/utils/geolocationHelpers.ts`:
   - Keep `getCurrentPosition()` unchanged
   - Remove the `COUNTRIES` constant entirely (replaced by API calls)
   - Add API fetch helpers:

   ```typescript
   interface Country {
     code: string;
     name: string;
     latitude: number;
     longitude: number;
     timezone: string;
     timezone_offset_hours: number;
     timezone_offset_minutes: number;
   }

   interface City {
     name: string;
     latitude: number;
     longitude: number;
     timezone: string;
   }

   export async function fetchCountries(
     lang: string = "en",
   ): Promise<Country[]> {
     const resp = await fetch(`/api/location/countries?lang=${lang}`);
     if (!resp.ok) return [];
     const data = await resp.json();
     return data.countries;
   }

   export async function fetchCities(
     countryCode: string,
     lang: string = "en",
   ): Promise<City[]> {
     const resp = await fetch(
       `/api/location/countries/${countryCode}/cities?lang=${lang}`,
     );
     if (!resp.ok) return [];
     const data = await resp.json();
     return data.cities;
   }
   ```

3. Update `frontend/src/types/index.ts` — update `LocationData` to include `countryCode`:

   ```typescript
   export interface LocationData {
     lat: number;
     lon: number;
     country?: string;
     countryCode?: string;
     city?: string;
     timezone?: string;
   }
   ```

   **Note:** Adding `countryCode` and `timezone` to `LocationData` is additive — existing code that doesn't set them will still work (all optional).

**Checkpoint:**

- [ ] LocationSelector fetches countries from API on mount
- [ ] Country search filters the list as user types
- [ ] Selecting a country fetches and shows its cities
- [ ] Selecting a city auto-fills coordinates
- [ ] Auto-detect button still works via browser geolocation
- [ ] Manual coordinate input available as toggle
- [ ] Component works in both EN and FA locales
- [ ] `COUNTRIES` constant removed from `geolocationHelpers.ts`
- Verify: `grep -r "COUNTRIES" frontend/src/ --include="*.ts" --include="*.tsx"` — should return 0 hits (removed)

STOP if checkpoint fails

---

### Phase 5: Persian Keyboard Polish (~45 min)

**Tasks:**

1. Update `frontend/src/utils/persianKeyboardLayout.ts` to add shift layer:

   ```typescript
   /** Persian QWERTY keyboard layout — base rows (no shift) */
   export const PERSIAN_ROWS: string[][] = [
     ["ض", "ص", "ث", "ق", "ف", "غ", "ع", "ه", "خ", "ح", "ج", "چ"],
     ["ش", "س", "ی", "ب", "ل", "ا", "ت", "ن", "م", "ک", "گ"],
     ["ظ", "ط", "ز", "ر", "ذ", "د", "پ", "و"],
     ["ژ", "ء", "آ", "ئ", "ؤ", "ة", "ي"],
   ];

   /** Persian QWERTY keyboard layout — shift rows (numbers, diacritics, punctuation) */
   export const PERSIAN_SHIFT_ROWS: string[][] = [
     ["۱", "۲", "۳", "۴", "۵", "۶", "۷", "۸", "۹", "۰", "ـ", "×"],
     ["ٌ", "ٍ", "ً", "َ", "ُ", "ِ", "ّ", "؛", ":", "»", "«"],
     ["ٰ", "ٓ", "ٔ", "،", ".", "؟", "!", "(", ")"],
     ["-", "+", "=", "/", "\\", "@", "#"],
   ];
   ```

   **Shift layer contents:**
   - Row 1: Persian digits (۱-۰) + underscore + multiplication
   - Row 2: Arabic diacritics (tanwin, fatha, damma, kasra, shadda) + Persian punctuation (؛ : » «)
   - Row 3: More diacritics + Persian comma/period/question mark + parentheses
   - Row 4: Common symbols used in Persian text

2. Update `frontend/src/components/oracle/PersianKeyboard.tsx`:

   **Add Shift key state:**

   ```tsx
   const [isShifted, setIsShifted] = useState(false);
   const rows = isShifted ? PERSIAN_SHIFT_ROWS : PERSIAN_ROWS;
   ```

   **Add Shift button to bottom row:**

   ```tsx
   <div className="flex gap-1 justify-center">
     <button
       type="button"
       onClick={() => setIsShifted(!isShifted)}
       aria-label={t("oracle.keyboard_shift")}
       className={`h-8 px-3 text-xs border border-nps-border rounded transition-colors ${
         isShifted
           ? "bg-nps-oracle-accent/30 text-nps-oracle-accent border-nps-oracle-accent"
           : "bg-nps-bg-input text-nps-text-dim hover:bg-nps-bg-hover"
       }`}
     >
       {t("oracle.keyboard_shift")}
     </button>
     <button type="button" onClick={() => onCharacterClick(" ")} ...>
       {t("oracle.keyboard_space")}
     </button>
     <button type="button" onClick={onBackspace} ...>
       ⌫
     </button>
   </div>
   ```

   **Smart positioning** — prevent keyboard from overflowing below viewport:

   ```tsx
   const [positionAbove, setPositionAbove] = useState(false);

   useEffect(() => {
     if (panelRef.current) {
       const rect = panelRef.current.getBoundingClientRect();
       if (rect.bottom > window.innerHeight) {
         setPositionAbove(true);
       }
     }
   }, []);

   // In JSX: change className based on positionAbove
   className={`absolute left-0 right-0 z-50 bg-nps-bg-card border border-nps-oracle-border rounded-lg p-3 shadow-lg ${
     positionAbove ? "bottom-full mb-1" : "top-full mt-1"
   }`}
   ```

   **Mobile touch support** — add `onTouchStart` alongside `onClick`:

   ```tsx
   {
     rows.map((row, rowIndex) => (
       <div key={rowIndex} className="flex gap-1 justify-center flex-wrap">
         {row.map((char) => (
           <button
             key={`${isShifted ? "s" : "b"}-${char}`}
             type="button"
             onClick={() => onCharacterClick(char)}
             onTouchStart={(e) => {
               e.preventDefault();
               onCharacterClick(char);
             }}
             aria-label={char}
             className="w-8 h-8 text-sm bg-nps-bg-input hover:bg-nps-bg-hover active:bg-nps-oracle-accent/20 border border-nps-border rounded text-nps-text transition-colors select-none"
           >
             {char}
           </button>
         ))}
       </div>
     ));
   }
   ```

   **Key changes summary:**
   - `select-none` CSS class prevents text selection on mobile
   - `active:bg-nps-oracle-accent/20` provides visual feedback on touch
   - `onTouchStart` with `preventDefault()` prevents double-firing on mobile
   - Key attribute includes shift state to force re-render when toggling

**Checkpoint:**

- [ ] Shift button toggles between base and shift character layers
- [ ] Shift button has visual indicator when active (accent color)
- [ ] Keyboard positions above input if below-viewport overflow detected
- [ ] Touch events work on mobile (no double-fire)
- [ ] `PERSIAN_SHIFT_ROWS` has 4 rows with numbers, diacritics, punctuation
- Verify: `grep -c "PERSIAN_SHIFT_ROWS" frontend/src/utils/persianKeyboardLayout.ts` — should return 1+
- Verify: `grep -c "onTouchStart" frontend/src/components/oracle/PersianKeyboard.tsx` — should return 1+

STOP if checkpoint fails

---

### Phase 6: RTL Text Direction Handling (~15 min)

**Tasks:**

1. Ensure LocationSelector respects RTL in FA locale:
   - Country search input: `dir="auto"` attribute (auto-detects text direction)
   - City select: `dir="auto"` attribute
   - Coordinate labels: remain LTR (numbers are always LTR)
   - Dropdown positioning: mirrors in RTL

2. Ensure PersianKeyboard renders correctly in both LTR and RTL:
   - Already has `dir="rtl"` on the panel — keep this
   - Close button position: should be top-left in RTL (already correct: `left-1`)
   - Shift/Space/Backspace row: order should be logical (Shift first, then Space, then Backspace)

3. Test with `i18n.language = "fa"` that labels render in Persian.

**Checkpoint:**

- [ ] LocationSelector labels are Persian when locale is FA
- [ ] Country names display in Persian when locale is FA
- [ ] City names display in Persian when locale is FA
- [ ] Coordinate numbers remain LTR regardless of locale
- [ ] PersianKeyboard renders correctly in both EN and FA contexts

STOP if checkpoint fails

---

### Phase 7: Translations & i18n Updates (~20 min)

**Tasks:**

1. Add new translation keys to `frontend/src/locales/en.json` under `oracle`:

   ```json
   "location_search_country": "Search country...",
   "location_select_city": "Select city",
   "location_no_cities": "No cities available",
   "location_manual_coords": "Enter coordinates manually",
   "location_latitude": "Latitude",
   "location_longitude": "Longitude",
   "location_timezone": "Timezone",
   "location_loading_countries": "Loading countries...",
   "location_loading_cities": "Loading cities...",
   "keyboard_shift": "Shift",
   "keyboard_numbers": "Numbers & Symbols"
   ```

2. Add corresponding Persian translations to `frontend/src/locales/fa.json` under `oracle`:

   ```json
   "location_search_country": "\u062c\u0633\u062a\u062c\u0648\u06cc \u06a9\u0634\u0648\u0631...",
   "location_select_city": "\u0627\u0646\u062a\u062e\u0627\u0628 \u0634\u0647\u0631",
   "location_no_cities": "\u0634\u0647\u0631\u06cc \u0645\u0648\u062c\u0648\u062f \u0646\u06cc\u0633\u062a",
   "location_manual_coords": "\u0648\u0631\u0648\u062f \u062f\u0633\u062a\u06cc \u0645\u062e\u062a\u0635\u0627\u062a",
   "location_latitude": "\u0639\u0631\u0636 \u062c\u063a\u0631\u0627\u0641\u06cc\u0627\u06cc\u06cc",
   "location_longitude": "\u0637\u0648\u0644 \u062c\u063a\u0631\u0627\u0641\u06cc\u0627\u06cc\u06cc",
   "location_timezone": "\u0645\u0646\u0637\u0642\u0647 \u0632\u0645\u0627\u0646\u06cc",
   "location_loading_countries": "\u062f\u0631 \u062d\u0627\u0644 \u0628\u0627\u0631\u06af\u0630\u0627\u0631\u06cc \u06a9\u0634\u0648\u0631\u0647\u0627...",
   "location_loading_cities": "\u062f\u0631 \u062d\u0627\u0644 \u0628\u0627\u0631\u06af\u0630\u0627\u0631\u06cc \u0634\u0647\u0631\u0647\u0627...",
   "keyboard_shift": "\u0634\u06cc\u0641\u062a",
   "keyboard_numbers": "\u0627\u0639\u062f\u0627\u062f \u0648 \u0646\u0645\u0627\u062f\u0647\u0627"
   ```

3. Verify no duplicate keys in locale files:
   ```bash
   python3 -c "
   import json
   for f in ['frontend/src/locales/en.json', 'frontend/src/locales/fa.json']:
       data = json.load(open(f))
       oracle = data.get('oracle', {})
       keys = list(oracle.keys())
       dupes = [k for k in keys if keys.count(k) > 1]
       assert not dupes, f'{f}: duplicate keys: {dupes}'
       print(f'  OK: {f} ({len(oracle)} oracle keys)')
   "
   ```

**Checkpoint:**

- [ ] 11 new keys added to both EN and FA locale files
- [ ] No duplicate keys in either file
- [ ] FA translations are correct Persian text (not transliteration)
- Verify: `python3 -c "import json; en=json.load(open('frontend/src/locales/en.json')); assert 'location_search_country' in en['oracle']; print('i18n OK')"`

STOP if checkpoint fails

---

### Phase 8: API Tests (~45 min)

**Tasks:**

1. Add 12+ new tests to `api/tests/test_location.py`:

   ```python
   # ─── GET /countries ──────────────────────────────────────────────────────────

   @pytest.mark.asyncio
   async def test_countries_list_returns_all(client):
       """GET /api/location/countries returns 249+ countries."""
       resp = await client.get("/api/location/countries")
       assert resp.status_code == 200
       data = resp.json()
       assert data["total"] >= 249
       assert len(data["countries"]) >= 249
       # Verify structure
       first = data["countries"][0]
       assert "code" in first
       assert "name" in first
       assert "latitude" in first
       assert "timezone" in first

   @pytest.mark.asyncio
   async def test_countries_list_fa(client):
       """GET /api/location/countries?lang=fa returns Persian names."""
       resp = await client.get("/api/location/countries?lang=fa")
       assert resp.status_code == 200
       data = resp.json()
       # Iran should appear with Persian name
       iran = next((c for c in data["countries"] if c["code"] == "IR"), None)
       assert iran is not None
       assert iran["name"] == "\u0627\u06cc\u0631\u0627\u0646"

   @pytest.mark.asyncio
   async def test_countries_sorted_alphabetically(client):
       """Countries should be sorted by name."""
       resp = await client.get("/api/location/countries")
       data = resp.json()
       names = [c["name"] for c in data["countries"]]
       assert names == sorted(names)

   @pytest.mark.asyncio
   async def test_countries_unauthenticated_401(unauth_client):
       """Unauthenticated requests to countries return 401."""
       resp = await unauth_client.get("/api/location/countries")
       assert resp.status_code == 401

   # ─── GET /countries/{code}/cities ────────────────────────────────────────────

   @pytest.mark.asyncio
   async def test_cities_iran(client):
       """GET /api/location/countries/IR/cities returns Iranian cities."""
       resp = await client.get("/api/location/countries/IR/cities")
       assert resp.status_code == 200
       data = resp.json()
       assert data["country_code"] == "IR"
       assert data["total"] >= 5
       # Tehran should be in the list
       names = [c["name"] for c in data["cities"]]
       assert "Tehran" in names or any("Tehran" in n for n in names)

   @pytest.mark.asyncio
   async def test_cities_iran_fa(client):
       """Cities returned in Persian when lang=fa."""
       resp = await client.get("/api/location/countries/IR/cities?lang=fa")
       data = resp.json()
       names = [c["name"] for c in data["cities"]]
       assert "\u062a\u0647\u0631\u0627\u0646" in names  # Tehran in Persian

   @pytest.mark.asyncio
   async def test_cities_unknown_country(client):
       """Unknown country code returns empty list (not 404)."""
       resp = await client.get("/api/location/countries/ZZ/cities")
       assert resp.status_code == 200
       data = resp.json()
       assert data["total"] == 0
       assert data["cities"] == []

   @pytest.mark.asyncio
   async def test_cities_have_coordinates(client):
       """Each city has valid latitude and longitude."""
       resp = await client.get("/api/location/countries/US/cities")
       data = resp.json()
       for city in data["cities"]:
           assert -90 <= city["latitude"] <= 90
           assert -180 <= city["longitude"] <= 180

   # ─── GET /timezone ───────────────────────────────────────────────────────────

   @pytest.mark.asyncio
   async def test_timezone_iran(client):
       """GET /api/location/timezone?country_code=IR returns Asia/Tehran."""
       resp = await client.get("/api/location/timezone?country_code=IR")
       assert resp.status_code == 200
       data = resp.json()
       assert data["timezone"] == "Asia/Tehran"
       assert data["offset_hours"] == 3
       assert data["offset_minutes"] == 30

   @pytest.mark.asyncio
   async def test_timezone_with_city(client):
       """Timezone lookup with city name."""
       resp = await client.get("/api/location/timezone?country_code=US&city=Los Angeles")
       assert resp.status_code == 200
       data = resp.json()
       assert data["timezone"] == "America/Los_Angeles"

   @pytest.mark.asyncio
   async def test_timezone_unknown_country_404(client):
       """Unknown country code returns 404."""
       resp = await client.get("/api/location/timezone?country_code=ZZ")
       assert resp.status_code == 404

   # ─── Static fallback ─────────────────────────────────────────────────────────

   @pytest.mark.asyncio
   async def test_coordinates_static_fallback(client):
       """get_coordinates finds Tehran in static data without Nominatim."""
       # No mock needed — static data should resolve it
       svc = LocationService()
       result = svc.get_coordinates("Tehran", "Iran")
       assert result is not None
       assert result["latitude"] == pytest.approx(35.6892, abs=0.01)
   ```

2. All new tests follow existing patterns:
   - Use `client`, `readonly_client`, `unauth_client` fixtures (from conftest.py)
   - Use `@pytest.mark.asyncio` decorator
   - Assert specific HTTP status codes and response body structure

**Checkpoint:**

- [ ] 12+ new test functions in `api/tests/test_location.py`
- [ ] All new tests pass alongside existing 12 tests
- Verify: `cd api && python3 -m pytest tests/test_location.py -v --tb=short`

STOP if checkpoint fails

---

### Phase 9: Frontend Component Tests (~45 min)

**Tasks:**

1. Create or update `frontend/src/components/oracle/__tests__/LocationSelector.test.tsx`:

   ```
   test_renders_country_search_input         — Renders text input for country search
   test_fetches_countries_on_mount           — Calls fetchCountries on component mount
   test_filters_countries_by_search          — Typing in search filters country list
   test_selects_country_loads_cities         — Selecting a country triggers city fetch
   test_selects_city_updates_coordinates     — Selecting a city fills lat/lng
   test_auto_detect_calls_geolocation        — Auto-detect button triggers browser geolocation
   test_manual_coordinate_input              — Manual lat/lng inputs update LocationData
   ```

2. Create or update `frontend/src/components/oracle/__tests__/PersianKeyboard.test.tsx`:

   ```
   test_renders_base_characters              — Shows Persian base characters by default
   test_shift_toggles_to_numbers             — Clicking Shift shows number/symbol layer
   test_shift_toggles_back                   — Clicking Shift again returns to base layer
   test_character_click_callback             — Clicking a character calls onCharacterClick
   test_touch_event_fires                    — Touch event on character calls onCharacterClick
   ```

3. All tests use `@testing-library/react` patterns with `render`, `screen`, `fireEvent`.

4. Mock API calls with `vi.mock` or `msw` depending on existing test infrastructure.

**Checkpoint:**

- [ ] 7 LocationSelector tests exist
- [ ] 5 PersianKeyboard tests exist
- [ ] All frontend tests pass
- Verify: `cd frontend && npx vitest run --reporter=verbose src/components/oracle/__tests__/`

STOP if checkpoint fails

---

### Phase 10: Integration & E2E Verification (~20 min)

**Tasks:**

1. Verify the full flow end-to-end:
   - API starts without errors: `cd api && python3 -c "from app.main import app; print('API imports OK')"`
   - Location endpoints appear in Swagger docs: `GET /docs` shows `/api/location/countries`, `/api/location/countries/{code}/cities`, `/api/location/timezone`
   - Frontend builds without errors: `cd frontend && npx tsc --noEmit`

2. Run all API tests:

   ```bash
   cd api && python3 -m pytest tests/test_location.py -v --tb=short
   ```

3. Run frontend type check:

   ```bash
   cd frontend && npx tsc --noEmit
   ```

4. Verify static data integrity:
   ```bash
   python3 -c "
   import json
   countries = json.load(open('api/data/countries.json'))
   cities = json.load(open('api/data/cities_by_country.json'))
   # Verify every city reference has a valid country
   for code in cities:
       assert code in {c['code'] for c in countries}, f'City list for {code} has no matching country'
   # Verify coordinate ranges
   for c in countries:
       assert -90 <= c['latitude'] <= 90, f'{c[\"code\"]}: bad lat {c[\"latitude\"]}'
       assert -180 <= c['longitude'] <= 180, f'{c[\"code\"]}: bad lon {c[\"longitude\"]}'
   print(f'Integrity OK: {len(countries)} countries, {sum(len(v) for v in cities.values())} total cities')
   "
   ```

**Checkpoint:**

- [ ] API imports cleanly with no errors
- [ ] All API tests pass (existing 12 + new 12 = 24+ total)
- [ ] Frontend type-checks cleanly
- [ ] Static data integrity verified
- [ ] No broken imports across the project

STOP if checkpoint fails

---

### Phase 11: Documentation & Cleanup (~15 min)

**Tasks:**

1. Run quality pipeline:

   ```bash
   cd api && python3 -m black app/services/location_service.py app/routers/location.py app/models/location.py && \
   python3 -m ruff check --fix app/services/location_service.py app/routers/location.py app/models/location.py
   ```

   ```bash
   cd frontend && npx prettier --write src/components/oracle/LocationSelector.tsx src/components/oracle/PersianKeyboard.tsx src/utils/persianKeyboardLayout.ts src/utils/geolocationHelpers.ts
   ```

2. Verify no `COUNTRIES` constant usage remains in frontend:

   ```bash
   grep -rn "COUNTRIES" frontend/src/ --include="*.ts" --include="*.tsx" | grep -v "node_modules" | grep -v "__tests__"
   ```

   Should return 0 hits.

3. Verify `geolocationHelpers.ts` only exports `getCurrentPosition` and the new fetch functions.

4. Git commit:

   ```bash
   git add -A
   git commit -m "[api][frontend] upgrade location system + polish Persian keyboard (#session-5)

   - Add static countries.json (250+) and cities_by_country.json with bilingual EN+FA names
   - Add 4 new LocationService methods: get_countries, get_cities, get_timezone, search_cities
   - Add 3 new API endpoints: countries list, cities by country, timezone lookup
   - Rewrite LocationSelector with searchable country, cascading city, manual coords
   - Add Shift key layer to PersianKeyboard with numbers/diacritics/punctuation
   - Add smart positioning and mobile touch support to keyboard
   - Add 12+ API tests and 12+ frontend tests
   - Remove hardcoded COUNTRIES constant from frontend"
   ```

**Checkpoint:**

- [ ] Code formatted and linted
- [ ] No `COUNTRIES` constant in frontend (removed)
- [ ] All tests pass
- [ ] Committed to git

---

## TESTS TO WRITE

### API Tests — `api/tests/test_location.py` (12 new)

| Test Function                          | Verifies                                              |
| -------------------------------------- | ----------------------------------------------------- |
| `test_countries_list_returns_all`      | Returns 249+ countries with correct structure         |
| `test_countries_list_fa`               | Persian names returned when `lang=fa`                 |
| `test_countries_sorted_alphabetically` | Countries sorted by name                              |
| `test_countries_unauthenticated_401`   | Unauthenticated request returns 401                   |
| `test_cities_iran`                     | Iran has 5+ cities, Tehran included                   |
| `test_cities_iran_fa`                  | Persian city names returned when `lang=fa`            |
| `test_cities_unknown_country`          | Unknown code returns empty list (200, not 404)        |
| `test_cities_have_coordinates`         | Every city has valid lat/lng ranges                   |
| `test_timezone_iran`                   | Iran returns `Asia/Tehran` with +3:30 offset          |
| `test_timezone_with_city`              | City-specific timezone (e.g., US + LA → America/LA)   |
| `test_timezone_unknown_country_404`    | Unknown country code returns 404                      |
| `test_coordinates_static_fallback`     | `get_coordinates("Tehran")` resolves from static data |

### Frontend Tests — LocationSelector (7 new)

| Test Function                           | Verifies                                        |
| --------------------------------------- | ----------------------------------------------- |
| `test_renders_country_search_input`     | Country search input is rendered                |
| `test_fetches_countries_on_mount`       | API called to fetch countries on mount          |
| `test_filters_countries_by_search`      | Typing filters the country list                 |
| `test_selects_country_loads_cities`     | Country selection triggers city fetch           |
| `test_selects_city_updates_coordinates` | City selection fills lat/lng                    |
| `test_auto_detect_calls_geolocation`    | Auto-detect button triggers browser geolocation |
| `test_manual_coordinate_input`          | Manual lat/lng fields update the value          |

### Frontend Tests — PersianKeyboard (5 new)

| Test Function                   | Verifies                                     |
| ------------------------------- | -------------------------------------------- |
| `test_renders_base_characters`  | Shows base Persian characters by default     |
| `test_shift_toggles_to_numbers` | Shift shows numbers/diacritics layer         |
| `test_shift_toggles_back`       | Second Shift press returns to base           |
| `test_character_click_callback` | Character click invokes `onCharacterClick`   |
| `test_touch_event_fires`        | Touch on character invokes callback (mobile) |

**Total: 24 new tests**

---

## ACCEPTANCE CRITERIA

- [ ] `api/data/countries.json` has 249+ country entries with bilingual EN+FA names
- [ ] `api/data/cities_by_country.json` has cities for 50+ countries with bilingual names
- [ ] `GET /api/location/countries` returns all countries sorted alphabetically
- [ ] `GET /api/location/countries?lang=fa` returns Persian names
- [ ] `GET /api/location/countries/IR/cities` returns 5+ Iranian cities
- [ ] `GET /api/location/timezone?country_code=IR` returns `Asia/Tehran` with offset +3:30
- [ ] Static data fallback: `get_coordinates("Tehran")` resolves without Nominatim
- [ ] LocationSelector has searchable country dropdown, cascading city, manual coordinates
- [ ] LocationSelector works in both EN and FA locales with bilingual labels
- [ ] PersianKeyboard has working Shift key that toggles to numbers/diacritics layer
- [ ] PersianKeyboard positions above input when below-viewport overflow detected
- [ ] PersianKeyboard handles mobile touch events without double-fire
- [ ] Hardcoded `COUNTRIES` constant removed from frontend
- [ ] 12+ new API tests pass
- [ ] 12+ new frontend tests pass
- [ ] All existing tests still pass (no regressions)
- Verify all:
  ```bash
  test -f api/data/countries.json && \
  test -f api/data/cities_by_country.json && \
  python3 -c "import json; c=json.load(open('api/data/countries.json')); assert len(c)>=249" && \
  grep -q "get_countries" api/app/services/location_service.py && \
  grep -q "countries" api/app/routers/location.py && \
  grep -q "PERSIAN_SHIFT_ROWS" frontend/src/utils/persianKeyboardLayout.ts && \
  grep -q "onTouchStart" frontend/src/components/oracle/PersianKeyboard.tsx && \
  echo "ALL ACCEPTANCE CRITERIA VERIFIABLE"
  ```

---

## ERROR SCENARIOS

| Scenario                                         | Expected Behavior                                                      |
| ------------------------------------------------ | ---------------------------------------------------------------------- |
| `countries.json` missing at startup              | `FileNotFoundError` logged, endpoints return 500 — must fix data path  |
| `cities_by_country.json` missing                 | Countries work, cities endpoints return empty lists — graceful degrade |
| Invalid `lang` parameter (not en/fa)             | 422 Validation Error from Query pattern validation                     |
| Country code "zz" (doesn't exist)                | Cities: empty list (200). Timezone: 404.                               |
| Country code lowercase "ir"                      | Normalized to uppercase "IR" in service methods                        |
| City search with empty query                     | Returns empty list (no results)                                        |
| City search with very long query (1000+ chars)   | Returns empty list (no match), no crash                                |
| Browser geolocation denied by user               | LocationSelector shows error message, falls back to manual selection   |
| Browser geolocation timeout                      | LocationSelector shows error message, falls back to manual selection   |
| API unavailable when LocationSelector mounts     | Country list empty, user can still enter manual coordinates            |
| Persian name search in city search               | Matches `name_fa` field — Persian users can search in their language   |
| Nominatim down + city not in static data         | `get_coordinates()` returns None (existing behavior preserved)         |
| PersianKeyboard Shift with rapidly repeated taps | State toggles correctly, no stuck state                                |
| PersianKeyboard outside viewport (near bottom)   | Keyboard renders above the input field instead                         |

---

## DESIGN DECISIONS

| Decision                            | Choice                                        | Rationale                                                                                                                                     |
| ----------------------------------- | --------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| Static JSON vs database table       | Static JSON files                             | 250 countries rarely change. JSON loads once at startup, zero DB queries, <1ms response. DB table would be slower and add migration overhead. |
| Bilingual names in data vs i18n     | EN+FA names stored directly in JSON           | Country/city names are proper nouns — they need specific translations, not pattern-based i18n. Storing both names in data is cleaner.         |
| Country search UI                   | `<input>` + `<datalist>` (native browser)     | No external dependency. Works on mobile. Accessible by default. `<datalist>` provides native autocomplete UX.                                 |
| City endpoint: 200 for unknown code | Return empty list, not 404                    | Frontend can handle empty list gracefully. 404 would require special error handling for a non-error case.                                     |
| Timezone in static data vs library  | Static `timezone_offset_hours/minutes` + IANA | Removes optional `timezonefinder` dependency. Static offsets work for 95% of cases. IANA name provided for DST-aware clients.                 |
| Persian keyboard shift layer        | State toggle in component, not layout file    | Layout file exports both arrays. Component manages state. Clean separation of data and behavior.                                              |
| Mobile touch: `onTouchStart`        | Prevent default + call handler                | Prevents ghost click (double-fire on mobile). `onTouchStart` fires before `onClick`, `preventDefault` stops the click.                        |
| Keyboard positioning                | Check `getBoundingClientRect()` on mount      | Simple and reliable. No need for ResizeObserver or scroll listeners for this use case.                                                        |
| Remove COUNTRIES from frontend      | Delete entirely, API is source of truth       | Single source of truth. No sync issues between hardcoded frontend data and API data.                                                          |
| Keep existing endpoints             | Don't modify GET /coordinates or GET /detect  | Backward compatible. Existing code that uses these endpoints continues working.                                                               |

---

## HANDOFF

**Created:**

- `api/data/countries.json` (250+ countries with bilingual names)
- `api/data/cities_by_country.json` (cities per country with bilingual names)

**Modified:**

- `api/app/services/location_service.py` — 4 new methods + static data loading + static fallback for get_coordinates
- `api/app/routers/location.py` — 3 new endpoints (countries, cities, timezone)
- `api/app/models/location.py` — 6 new Pydantic models
- `frontend/src/components/oracle/LocationSelector.tsx` — Rewritten: searchable country, cascading city, manual coords
- `frontend/src/components/oracle/PersianKeyboard.tsx` — Polish: Shift key, smart positioning, mobile touch
- `frontend/src/utils/persianKeyboardLayout.ts` — Added `PERSIAN_SHIFT_ROWS`
- `frontend/src/utils/geolocationHelpers.ts` — Removed `COUNTRIES`, added API fetch helpers
- `frontend/src/types/index.ts` — Added `countryCode`, `timezone` to `LocationData`
- `frontend/src/locales/en.json` — 11 new location/keyboard translation keys
- `frontend/src/locales/fa.json` — 11 new location/keyboard translation keys
- `api/tests/test_location.py` — 12+ new tests

**Next session (Session 6) receives:**

- Static location data available via 3 fast API endpoints (no Nominatim dependency for common lookups)
- `get_timezone()` method available for looking up timezone from country/city — used by framework bridge for `tz_hours`/`tz_minutes` parameters
- `LocationData` interface now includes `countryCode` and `timezone` — Session 6's framework bridge can extract timezone offset from the profile's location
- LocationSelector provides clean country code + city name + coordinates — all needed by the Oracle profile for framework readings
- PersianKeyboard is polished and ready for daily use with full character coverage
