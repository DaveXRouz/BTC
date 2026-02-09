# Numerology Systems — Calculation Reference

> Reference: `.archive/v3/engines/numerology.py` (294 lines)
> Current location: `services/oracle/oracle_service/engines/numerology.py`

---

## Three Systems

| System          | Language              | Used In          |
| --------------- | --------------------- | ---------------- |
| **Pythagorean** | English               | Legacy + Current |
| **Chaldean**    | English (alternative) | New              |
| **Abjad**       | Persian/Arabic        | New              |

All reduce to single digit (1-9) preserving **master numbers** (11, 22, 33).

---

## Pythagorean (Primary)

**Letter table:** A=1 B=2 C=3 D=4 E=5 F=6 G=7 H=8 I=9, J=1 K=2 ... Z=8

**Reduction:** Sum digits repeatedly. Stop at 1-9 or master number.

```python
def numerology_reduce(n):
    if n in (11, 22, 33): return n
    while n > 9:
        n = sum(int(d) for d in str(n))
        if n in (11, 22, 33): return n
    return n
```

**Core calculations:**

- `name_to_number(name)` — sum all letters → reduce
- `name_soul_urge(name)` — vowels (A,E,I,O,U) only → reduce
- `name_personality(name)` — consonants only → reduce
- `life_path(year, month, day)` — reduce each part, sum, reduce again
- `personal_year(birth_month, birth_day, current_year)` — annual cycle number

---

## Chaldean (Alternative English — New)

Different assignments: A=1 B=2 C=3 D=4 E=5 **F=8** **G=3** H=5 I=1, no letter = 9 (sacred). Same reduction rules.

---

## Abjad (Persian — New)

Arabic/Persian letters with traditional values: ا=1 ب=2 ج=3 ... غ=1000. Persian extras: پ=2 چ=3 ژ=7 گ=20. Same reduction principle.

---

## FC60 Integration

`number_vibration(n)` bridges both systems:

- `digit_sum` + `reduced` (numerology)
- `fc60_token` + `animal` + `element` (FC60 via n % 60)

## Compatibility Scoring

```
Same reduced number → 1.0 (perfect)
Sum to 9 → 0.8 (completion pair)
Master + base (11,2) → 0.9
Same FC60 animal → +0.2 bonus
Same FC60 element → +0.15 bonus
Base → 0.3
```

---

## Test Vectors

| Input     | Function          | Expected    |
| --------- | ----------------- | ----------- |
| "DAVE"    | name_to_number    | 5           |
| 1990,6,15 | life_path         | 4           |
| 29        | numerology_reduce | 11 (master) |
| 347       | digit_sum_reduced | 5           |
