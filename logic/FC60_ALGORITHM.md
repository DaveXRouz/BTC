# FC60 Algorithm — FrankenChron-60 Calculation Machine

> Reference: `.archive/v3/engines/fc60.py` (966 lines, zero external dependencies)
> Current location: `services/oracle/oracle_service/engines/fc60.py`

---

## What FC60 Does

Converts any date+time into a unique symbolic code using a base-60 system. Each moment gets a "fingerprint" made of animals, elements, and cosmic markers used for numerological analysis.

---

## Base-60 Token System

Every integer 0–59 maps to a 4-char token: **2-letter Animal + 2-letter Element**.

**12 Animals:** RA(Rat), OX(Ox), TI(Tiger), RU(Rabbit), DR(Dragon), SN(Snake), HO(Horse), GO(Goat), MO(Monkey), RO(Rooster), DO(Dog), PI(Pig)

**5 Elements:** WU(Wood), FI(Fire), ER(Earth), MT(Metal), WA(Water)

**Encoding:** `token60(n) = ANIMALS[n // 5] + ELEMENTS[n % 5]`
**Decoding:** `digit60(tok) = animal_index * 5 + element_index`

Example: `token60(23)` → 23//5=4(Dragon "DR") + 23%5=3(Metal "MT") → **"DRMT"**

---

## Key Formulas

### Julian Day Number (Fliegel–Van Flandern)

```
a = (14 - month) // 12
y2 = year + 4800 - a
m2 = month + 12 * a - 3
JDN = day + (153*m2 + 2)//5 + 365*y2 + y2//4 - y2//100 + y2//400 - 32045
```

### Weekday: `(JDN + 1) % 7` → 0=Sunday ... 6=Saturday

### Moon Phase

```
age = (JDN - 2451550.1) % 29.530588853
illumination = 50.0 * (1.0 - cos(2π * age / 29.530588853))
```

8 phases: 🌑🌒🌓🌔🌕🌖🌗🌘

### Gānzhī (干支) Sexagenary Cycle

```
stem_index = (year - 4) % 10    # 10 Heavenly Stems
branch_index = (year - 4) % 12  # 12 Earthly Branches
```

### Weighted Checksum (Luhn-inspired)

```
chk = (1*(year%60) + 2*month + 3*day + 4*hour + 5*minute + 6*second + 7*(JDN%60)) % 60
```

---

## Full FC60 Output

`encode_fc60(datetime)` produces: JDN as base-60 tokens, weekday token, timezone token, moon phase token, Gānzhī stem+branch tokens, weighted checksum, plus symbolic reading metadata.

---

## Test Vectors (Current MUST Match Legacy)

| Input      | Expected JDN | token60(JDN % 60)    |
| ---------- | ------------ | -------------------- |
| 2024-01-01 | 2460310      | token60(10) = "OXWU" |
| 2000-01-01 | 2451545      | token60(45) = "ROWU" |
| 1990-06-15 | 2448058      | token60(58) = "PIMT" |

Use `.archive/v3/engines/fc60.py:self_test()` as verification baseline.
