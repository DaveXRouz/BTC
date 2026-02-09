# FC60 AI Quick Reference Card

**Purpose:** Self-contained reference for encoding/decoding any FC60 stamp. Read this file at the start of every conversation.

**Stamp format:** `WD-MO-DOM HALF·HOUR-MINUTE-SECOND`
**Example:** `VE-OX-OXFI ☀OX-RUWU-RAWU` = Friday, February 6, 01:15:00

---

## §1. TOKEN60 Encoding Rule

```
TOKEN60(n) = ANIMAL[floor(n/5)] + ELEMENT[n mod 5]     (0 ≤ n ≤ 59)

DIGIT60(token) = ANIMAL_INDEX(token[0:2]) × 5 + ELEMENT_INDEX(token[2:4])

Multi-digit (n ≥ 60):
  digits = []
  while n > 0: digits.prepend(n mod 60); n = floor(n/60)
  result = join(TOKEN60(d) for d in digits, separator="-")

Negative: NEG- + encode_base60(abs(n))
```

**Verification:** `TOKEN60(DIGIT60(T)) = T` must always hold.

---

## §2. Complete TOKEN60 Table (0–59)

| Idx | Token | Idx | Token | Idx | Token |
| --: | ----- | --: | ----- | --: | ----- |
|   0 | RAWU  |  20 | DRWU  |  40 | MOWU  |
|   1 | RAFI  |  21 | DRFI  |  41 | MOFI  |
|   2 | RAER  |  22 | DRER  |  42 | MOER  |
|   3 | RAMT  |  23 | DRMT  |  43 | MOMT  |
|   4 | RAWA  |  24 | DRWA  |  44 | MOWA  |
|   5 | OXWU  |  25 | SNWU  |  45 | ROWU  |
|   6 | OXFI  |  26 | SNFI  |  46 | ROFI  |
|   7 | OXER  |  27 | SNER  |  47 | ROER  |
|   8 | OXMT  |  28 | SNMT  |  48 | ROMT  |
|   9 | OXWA  |  29 | SNWA  |  49 | ROWA  |
|  10 | TIWU  |  30 | HOWU  |  50 | DOWU  |
|  11 | TIFI  |  31 | HOFI  |  51 | DOFI  |
|  12 | TIER  |  32 | HOER  |  52 | DOER  |
|  13 | TIMT  |  33 | HOMT  |  53 | DOMT  |
|  14 | TIWA  |  34 | HOWA  |  54 | DOWA  |
|  15 | RUWU  |  35 | GOWU  |  55 | PIWU  |
|  16 | RUFI  |  36 | GOFI  |  56 | PIFI  |
|  17 | RUER  |  37 | GOER  |  57 | PIER  |
|  18 | RUMT  |  38 | GOMT  |  58 | PIMT  |
|  19 | RUWA  |  39 | GOWA  |  59 | PIWA  |

---

## §3. Animal Table (12 Earthly Branches)

| Idx | Code | Animal  | Chinese | Essence                     |
| --: | ---- | ------- | ------- | --------------------------- |
|   0 | RA   | Rat     | 子 Zǐ   | Resourcefulness, beginnings |
|   1 | OX   | Ox      | 丑 Chǒu | Patience, steady progress   |
|   2 | TI   | Tiger   | 寅 Yín  | Power, bold action          |
|   3 | RU   | Rabbit  | 卯 Mǎo  | Diplomacy, gentle wisdom    |
|   4 | DR   | Dragon  | 辰 Chén | Transformation, ambition    |
|   5 | SN   | Snake   | 巳 Sì   | Precision, depth            |
|   6 | HO   | Horse   | 午 Wǔ   | Movement, independence      |
|   7 | GO   | Goat    | 未 Wèi  | Creativity, harmony         |
|   8 | MO   | Monkey  | 申 Shēn | Cleverness, flexibility     |
|   9 | RO   | Rooster | 酉 Yǒu  | Confidence, discipline      |
|  10 | DO   | Dog     | 戌 Xū   | Loyalty, protection         |
|  11 | PI   | Pig     | 亥 Hài  | Generosity, completion      |

**Memory aid:** RA-OX-TI-RU-DR-SN-HO-GO-MO-RO-DO-PI

---

## §4. Element Table (5 Wu Xing)

| Idx | Code | Element | Chinese | Meaning                 |
| --: | ---- | ------- | ------- | ----------------------- |
|   0 | WU   | Wood    | 木 Mù   | Growth, flexibility     |
|   1 | FI   | Fire    | 火 Huǒ  | Passion, transformation |
|   2 | ER   | Earth   | 土 Tǔ   | Stability, grounding    |
|   3 | MT   | Metal   | 金 Jīn  | Precision, refinement   |
|   4 | WA   | Water   | 水 Shuǐ | Flow, hidden truths     |

**Memory aid:** WU-FI-ER-MT-WA

---

## §5. Weekday Table

| Idx | Token | Day       | Planet    | Domain                 |
| --: | ----- | --------- | --------- | ---------------------- |
|   0 | SO    | Sunday    | Sun ☉     | Identity, vitality     |
|   1 | LU    | Monday    | Moon ☽    | Emotions, intuition    |
|   2 | MA    | Tuesday   | Mars ♂    | Drive, action          |
|   3 | ME    | Wednesday | Mercury ☿ | Communication, thought |
|   4 | JO    | Thursday  | Jupiter ♃ | Expansion, wisdom      |
|   5 | VE    | Friday    | Venus ♀   | Love, values, beauty   |
|   6 | SA    | Saturday  | Saturn ♄  | Discipline, mastery    |

**Formula:** `weekday_index = (JDN + 1) mod 7`

---

## §6. Month Encoding

> **WARNING:** Month uses `ANIMAL[month - 1]`, NOT `ANIMAL[month]`. January = index 0 = RA.

| Month    |   # | Token | Month     |   # | Token |
| -------- | --: | ----- | --------- | --: | ----- |
| January  |   1 | RA    | July      |   7 | HO    |
| February |   2 | OX    | August    |   8 | GO    |
| March    |   3 | TI    | September |   9 | MO    |
| April    |   4 | RU    | October   |  10 | RO    |
| May      |   5 | DR    | November  |  11 | DO    |
| June     |   6 | SN    | December  |  12 | PI    |

---

## §7. Day-of-Month Table (1–31)

| Day | Token | Day | Token | Day | Token | Day | Token |
| --: | ----- | --: | ----- | --: | ----- | --: | ----- |
|   1 | RAFI  |   9 | OXWA  |  17 | RUER  |  25 | SNWU  |
|   2 | RAER  |  10 | TIWU  |  18 | RUMT  |  26 | SNFI  |
|   3 | RAMT  |  11 | TIFI  |  19 | RUWA  |  27 | SNER  |
|   4 | RAWA  |  12 | TIER  |  20 | DRWU  |  28 | SNMT  |
|   5 | OXWU  |  13 | TIMT  |  21 | DRFI  |  29 | SNWA  |
|   6 | OXFI  |  14 | TIWA  |  22 | DRER  |  30 | HOWU  |
|   7 | OXER  |  15 | RUWU  |  23 | DRMT  |  31 | HOFI  |
|   8 | OXMT  |  16 | RUFI  |  24 | DRWA  |     |       |

**Rule:** `DOM = TOKEN60(day)`

---

## §8. Hour Encoding (00–23)

> **WARNING:** Hour token uses 2-char `ANIMAL[hour % 12]`, NOT 4-char TOKEN60.

|  Hr | Token |  Hr | Token |  Hr | Token |  Hr | Token |
| --: | ----- | --: | ----- | --: | ----- | --: | ----- |
|   0 | ☀RA   |   6 | ☀HO   |  12 | 🌙RA  |  18 | 🌙HO  |
|   1 | ☀OX   |   7 | ☀GO   |  13 | 🌙OX  |  19 | 🌙GO  |
|   2 | ☀TI   |   8 | ☀MO   |  14 | 🌙TI  |  20 | 🌙MO  |
|   3 | ☀RU   |   9 | ☀RO   |  15 | 🌙RU  |  21 | 🌙RO  |
|   4 | ☀DR   |  10 | ☀DO   |  16 | 🌙DR  |  22 | 🌙DO  |
|   5 | ☀SN   |  11 | ☀PI   |  17 | 🌙SN  |  23 | 🌙PI  |

**Rules:**

- `HALF = ☀ if hour < 12, else 🌙`
- `HOUR = ANIMAL[hour mod 12]` (2-char code)
- `MINUTE = TOKEN60(minute)` (4-char token)
- `SECOND = TOKEN60(second)` (4-char token)
- **Format:** `HALF` `HOUR` `-` `MINUTE` [`-` `SECOND`]

---

## §9. Heavenly Stems (10 Tiāngān)

| Idx | Token | Stem | Chinese | Element | Polarity |
| --: | ----- | ---- | ------- | ------- | -------- |
|   0 | JA    | Jiǎ  | 甲      | Wood    | Yang (+) |
|   1 | YI    | Yǐ   | 乙      | Wood    | Yin (−)  |
|   2 | BI    | Bǐng | 丙      | Fire    | Yang (+) |
|   3 | DI    | Dīng | 丁      | Fire    | Yin (−)  |
|   4 | WW    | Wù   | 戊      | Earth   | Yang (+) |
|   5 | JI    | Jǐ   | 己      | Earth   | Yin (−)  |
|   6 | GE    | Gēng | 庚      | Metal   | Yang (+) |
|   7 | XI    | Xīn  | 辛      | Metal   | Yin (−)  |
|   8 | RE    | Rén  | 壬      | Water   | Yang (+) |
|   9 | GU    | Guǐ  | 癸      | Water   | Yin (−)  |

**Memory aid:** JA-YI-BI-DI-WW-JI-GE-XI-RE-GU

---

## §10. Moon Phase Table

**Constants:** Synodic month = 29.530588853 days; Reference new moon JDN = 2451550.1

**Moon age:** `(JDN - 2451550.1) mod 29.530588853`

| Phase           | Emoji | Day Range     | Energy    | Best For               | Avoid               |
| --------------- | ----- | ------------- | --------- | ---------------------- | ------------------- |
| New Moon        | 🌑    | 0.00 – 1.85   | Seed      | Setting intentions     | Big reveals         |
| Waxing Crescent | 🌒    | 1.85 – 7.38   | Build     | First steps, resources | Giving up           |
| First Quarter   | 🌓    | 7.38 – 11.07  | Challenge | Decisions, obstacles   | Avoiding conflict   |
| Waxing Gibbous  | 🌔    | 11.07 – 14.77 | Refine    | Editing, perfecting    | Starting new things |
| Full Moon       | 🌕    | 14.77 – 16.61 | Culminate | Celebrating, releasing | Starting            |
| Waning Gibbous  | 🌖    | 16.61 – 22.14 | Share     | Teaching, distributing | Hoarding            |
| Last Quarter    | 🌗    | 22.14 – 25.83 | Release   | Letting go, forgiving  | Holding on          |
| Waning Crescent | 🌘    | 25.83 – 29.53 | Rest      | Reflection, dreaming   | Pushing hard        |

**Illumination:** `(1 - cos(2π × age / 29.530588853)) / 2 × 100`

---

## §11. JDN Formula (Fliegel–Van Flandern)

### Gregorian → JDN

```
INPUT:  Y (year), M (month 1–12), D (day 1–31)

A  = floor((14 - M) / 12)
Y2 = Y + 4800 - A
M2 = M + 12×A - 3

JDN = D
    + floor((153×M2 + 2) / 5)
    + 365×Y2
    + floor(Y2 / 4)
    - floor(Y2 / 100)
    + floor(Y2 / 400)
    - 32045
```

> **WARNING:** `floor((153×M2 + 2) / 5)` is the most common arithmetic error source.
> For M2=11: 153×11=1683, 1683+2=1685, floor(1685/5)=337, NOT 336.

### JDN → Gregorian (Inverse)

```
a = JDN + 32044
b = floor((4×a + 3) / 146097)
c = a - floor(146097×b / 4)
d = floor((4×c + 3) / 1461)
e = c - floor(1461×d / 4)
m = floor((5×e + 2) / 153)

D = e - floor((153×m + 2) / 5) + 1
M = m + 3 - 12×floor(m / 10)
Y = 100×b + d - 4800 + floor(m / 10)
```

### J60 Encoding

`J60 = encode_base60(JDN)` — each base-60 digit becomes a TOKEN60, joined by hyphens.

### Key Epochs

| Date       |       JDN |
| ---------- | --------: |
| 2000-01-01 | 2,451,545 |
| 1970-01-01 | 2,440,588 |
| 2026-02-06 | 2,461,078 |
| 2024-02-29 | 2,460,370 |
| 2025-12-31 | 2,461,041 |

---

## §12. Weekday from JDN

```
weekday_index = (JDN + 1) mod 7
WEEKDAY_TOKEN = ["SO","LU","MA","ME","JO","VE","SA"][weekday_index]
```

### Verification Anchors

| Date       |       JDN | (JDN+1)%7 | Weekday   | Token |
| ---------- | --------: | --------: | --------- | ----- |
| 2000-01-01 | 2,451,545 |         6 | Saturday  | SA    |
| 1970-01-01 | 2,440,588 |         4 | Thursday  | JO    |
| 2026-02-06 | 2,461,078 |         5 | Friday    | VE    |
| 2024-02-29 | 2,460,370 |         4 | Thursday  | JO    |
| 2025-12-31 | 2,461,041 |         3 | Wednesday | ME    |

---

## §13. CHK Formula (Weighted Check Token)

> **WARNING:** CHK uses LOCAL date/time values, NOT UTC-adjusted.
> `year mod 60` is the full year mod 60 (2026 mod 60 = 46), NOT last two digits.

### Full (date + time)

```
chk_value = (
    1 × (Y mod 60) +
    2 × M +
    3 × D +
    4 × HH +
    5 × MM +
    6 × SS +
    7 × (JDN mod 60)
) mod 60

CHK = TOKEN60(chk_value)
```

### Date-only

```
chk_value = (
    1 × (Y mod 60) +
    2 × M +
    3 × D +
    7 × (JDN mod 60)
) mod 60
```

### Verification

| Date/Time           | Y%60 |   M |   D |  HH |  MM |  SS | JDN%60 | CHK val | CHK  |
| ------------------- | ---: | --: | --: | --: | --: | --: | -----: | ------: | ---- |
| 2026-02-06 01:15:00 |   46 |   2 |   6 |   1 |  15 |   0 |     58 |      13 | TIMT |
| 2025-12-31 23:59:59 |   45 |  12 |  31 |  23 |  59 |  59 |     21 |      30 | HOWU |
| 2026-01-01 00:00:00 |   46 |   1 |   1 |   0 |   0 |   0 |     22 |      25 | SNWU |
| 2000-01-01 00:00:00 |   20 |   1 |   1 |   0 |   0 |   0 |      5 |       0 | RAWU |

---

## §14. Cross-Check Formulas

```
MJD       = JDN - 2,400,001
RD        = JDN - 1,721,425
Unix days = JDN - 2,440,588

Cross-check identity: MJD = RD - 678,576

Unix seconds = unix_days × 86400 + HH×3600 + MM×60 + SS - tz_offset_seconds
```

### Verification

| Date       |       JDN |    MJD |      RD | Unix Days |
| ---------- | --------: | -----: | ------: | --------: |
| 2000-01-01 | 2,451,545 | 51,544 | 730,120 |    10,957 |
| 1970-01-01 | 2,440,588 | 40,587 | 719,163 |         0 |
| 2026-02-06 | 2,461,078 | 61,077 | 739,653 |    20,490 |

---

## §15. Essential Test Vectors

### TV1: Primary Reference — 2026-02-06 01:15:00 UTC+8

```
INPUT:  2026-02-06T01:15:00+08:00

JDN Calculation:
  A=1, Y2=6825, M2=11
  floor((153×11+2)/5) = floor(1685/5) = 337
  365×6825 = 2,491,125
  floor(6825/4)=1706, floor(6825/100)=68, floor(6825/400)=17
  JDN = 6 + 337 + 2,491,125 + 1706 - 68 + 17 - 32,045 = 2,461,078

OUTPUT:
  FC60:  VE-OX-OXFI ☀OX-RUWU-RAWU
  ISO:   2026-02-06T01:15:00+08:00
  TZ60:  +OXMT-RAWU
  Y60:   HOMT-ROFI
  Y2K:   SNFI
  J:     TIFI-DRMT-GOER-PIMT
  MJD:   RAFI-RAWU-RUER-PIER
  RD:    RAMT-SNWU-SNER-HOMT
  MOON:  🌖 age=19.05d
  GZ:    BI-HO (丙午 Fire Horse)
  CHK:   TIMT
         (1×46 + 2×2 + 3×6 + 4×1 + 5×15 + 6×0 + 7×58) mod 60
         = (46+4+18+4+75+0+406) mod 60 = 553 mod 60 = 13 → TIMT
```

### TV2: Y2K Reference — 2000-01-01 00:00:00 UTC

```
INPUT:  2000-01-01T00:00:00Z

  JDN = 2,451,545
  Weekday: (2451545+1) mod 7 = 6 → SA (Saturday)

OUTPUT:
  FC60:  SA-RA-RAFI ☀RA-RAWU-RAWU
  ISO:   2000-01-01T00:00:00Z
  TZ60:  Z
  Y60:   HOMT-DRWU
  Y2K:   RAWU
  J:     TIFI-DRWU-PIWA-OXWU
  RD:    RAMT-DRER-ROMT-MOWU (730,120)
  GZ:    GE-DR (庚辰 Metal Dragon)
  CHK:   RAWU
         (1×20 + 2×1 + 3×1 + 4×0 + 5×0 + 6×0 + 7×5) mod 60
         = (20+2+3+0+0+0+35) mod 60 = 60 mod 60 = 0 → RAWU
```

### TV4: Leap Day — 2024-02-29 12:00:00 UTC

```
INPUT:  2024-02-29T12:00:00Z

  JDN = 2,460,370
  Weekday: (2460370+1) mod 7 = 4 → JO (Thursday)

OUTPUT:
  FC60:  JO-OX-SNWA 🌙RA-RAWU-RAWU
  ISO:   2024-02-29T12:00:00Z
  TZ60:  Z
  Y60:   HOMT-MOWA
  J:     TIFI-DRMT-SNFI-TIWU
  GZ:    JA-DR (甲辰 Wood Dragon)
  CHK:   TIMT
         (1×44 + 2×2 + 3×29 + 4×12 + 5×0 + 6×0 + 7×10) mod 60
         = (44+4+87+48+0+0+70) mod 60 = 253 mod 60 = 13 → TIMT
```

### TV5: Year End — 2025-12-31 23:59:59 UTC

```
INPUT:  2025-12-31T23:59:59Z

  JDN = 2,461,041
  Weekday: (2461041+1) mod 7 = 3 → ME (Wednesday)

OUTPUT:
  FC60:  ME-PI-HOFI 🌙PI-PIWA-PIWA
  ISO:   2025-12-31T23:59:59Z
  Y60:   HOMT-ROWU
  J:     TIFI-DRMT-GOER-DRFI
  CHK:   HOWU
         (1×45 + 2×12 + 3×31 + 4×23 + 5×59 + 6×59 + 7×21) mod 60
         = (45+24+93+92+295+354+147) mod 60 = 1050 mod 60 = 30 → HOWU
```

### TV15: Round-Trip Decode

```
INPUT (FC60):  "VE-OX-OXFI ☀OX-RUWU-RAWU"

DECODE:
  WD = VE → Friday
  MO = OX → ANIMAL index 1 → month = 1+1 = 2 (February)
  DOM = OXFI → DIGIT60 = 1×5+1 = 6
  HALF = ☀ → AM (hour < 12)
  HOUR = OX → ANIMAL index 1 → hour = 1
  MINUTE = RUWU → DIGIT60 = 3×5+0 = 15
  SECOND = RAWU → DIGIT60 = 0×5+0 = 0

RESULT: Friday, February 6, 01:15:00

VERIFY: JDN for 2026-02-06 = 2,461,078
  (2461078+1) mod 7 = 5 → VE (Friday) ✓
```

---

## §16. Timezone Encoding (TZ60)

```
UTC exactly:      TZ60 = "Z"
Otherwise:        TZ60 = SIGN + TOKEN60(abs_hours) + "-" + TOKEN60(abs_minutes)
  SIGN = "+" (east of UTC) or "-" (west of UTC)
```

### Common Offsets

| Offset | TZ60       | Region           |
| ------ | ---------- | ---------------- |
| +00:00 | Z          | UTC              |
| +01:00 | +RAFI-RAWU | Central Europe   |
| +03:00 | +RAMT-RAWU | Moscow           |
| +05:00 | +OXWU-RAWU | Pakistan         |
| +05:30 | +OXWU-HOWU | India            |
| +08:00 | +OXMT-RAWU | China, Singapore |
| +09:00 | +OXWA-RAWU | Japan, Korea     |
| +12:00 | +TIER-RAWU | New Zealand      |
| -05:00 | -OXWU-RAWU | US Eastern       |
| -08:00 | -OXMT-RAWU | US Pacific       |

---

## §17. Year Encoding

### Y60 (Absolute — Required)

```
Y60 = encode_base60(year)
```

| Year | Base-60 Digits | Y60       |
| ---: | -------------- | --------- |
| 1970 | [32, 50]       | HOER-DOWU |
| 2000 | [33, 20]       | HOMT-DRWU |
| 2024 | [33, 44]       | HOMT-MOWA |
| 2025 | [33, 45]       | HOMT-ROWU |
| 2026 | [33, 46]       | HOMT-ROFI |

### Y2K (60-Year Cycle — Compact)

```
Y2K = TOKEN60((year - 2000) mod 60)
```

| Year | (Y-2000)%60 | Y2K  |
| ---: | ----------: | ---- |
| 2000 |           0 | RAWU |
| 2024 |          24 | DRWA |
| 2025 |          25 | SNWU |
| 2026 |          26 | SNFI |

> **Note:** Y2K is ambiguous without Y60 — years 2000 and 2060 both produce RAWU.

---

## §18. Ganzhi Cycle (干支)

### Year Ganzhi

```
Reference: Year 4 CE = 甲子 (Jiǎ-Zǐ) = Stem 0, Branch 0

stem_index   = (year - 4) mod 10
branch_index = (year - 4) mod 12

GZ = STEM_TOKEN[stem_index] + "-" + ANIMAL_TOKEN[branch_index]
```

| Year | Stem | Branch | GZ    | Traditional      |
| ---: | ---: | -----: | ----- | ---------------- |
| 2020 |    6 |      0 | GE-RA | 庚子 Metal Rat   |
| 2024 |    0 |      4 | JA-DR | 甲辰 Wood Dragon |
| 2025 |    1 |      5 | YI-SN | 乙巳 Wood Snake  |
| 2026 |    2 |      6 | BI-HO | 丙午 Fire Horse  |
| 2030 |    6 |     10 | GE-DO | 庚戌 Metal Dog   |

### Day Ganzhi

```
day_gz_index = (JDN + 49) mod 60
day_stem     = day_gz_index mod 10
day_branch   = day_gz_index mod 12

Day_GZ = STEM_TOKEN[day_stem] + "-" + ANIMAL_TOKEN[day_branch]
```

**Example:** JDN 2,461,078 (2026-02-06)

```
gz = (2461078 + 49) mod 60 = 2461127 mod 60 = 47
stem  = 47 mod 10 = 7 → XI (Metal, Yin)
branch = 47 mod 12 = 11 → PI (Pig)
Day Ganzhi: XI-PI (辛亥 Metal Pig)
```

### Hour Ganzhi

```
hour_branch = floor((hour + 1) / 2) mod 12
hour_stem   = (day_stem × 2 + hour_branch) mod 10
```

---

_End of Quick Reference — 18 sections, self-contained for FC60 encode/decode._
