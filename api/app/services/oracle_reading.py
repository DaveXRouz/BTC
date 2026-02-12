"""Oracle reading service — computation via legacy engines + DB persistence."""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

from fastapi import Depends, WebSocket
from sqlalchemy.orm import Session

from app.database import get_db
from app.orm.oracle_reading import OracleReading, OracleReadingUser
from app.services.security import EncryptionService, get_encryption_service

if TYPE_CHECKING:
    from app.orm.oracle_user import OracleUser
    from oracle_service.models.reading_types import UserProfile

logger = logging.getLogger(__name__)

# ─── Engine imports via sys.path shim (same approach as gRPC server) ─────────
#
# Two paths needed:
# 1. Parent of oracle_service/ so `import oracle_service` works (for logic/__init__.py)
# 2. Inside oracle_service/ so `from engines.xxx` works (legacy-style imports)

_ORACLE_PARENT_DIR = str(Path(__file__).resolve().parents[3] / "services" / "oracle")
_ORACLE_SERVICE_DIR = str(
    Path(__file__).resolve().parents[3] / "services" / "oracle" / "oracle_service"
)
if _ORACLE_PARENT_DIR not in sys.path:
    sys.path.insert(0, _ORACLE_PARENT_DIR)
if _ORACLE_SERVICE_DIR not in sys.path:
    sys.path.insert(0, _ORACLE_SERVICE_DIR)

import oracle_service  # noqa: E402, F401 — triggers shim for absolute imports

from oracle_service.framework_bridge import (  # noqa: E402
    ANIMAL_NAMES,
    STEM_ELEMENTS,
    STEM_NAMES,
    STEM_POLARITY,
    encode_fc60,
    ganzhi_year,
    LETTER_VALUES,
    LIFE_PATH_MEANINGS,
    life_path,
    numerology_reduce,
    personal_year,
)
from engines.oracle import (  # noqa: E402
    _get_zodiac,
    daily_insight,
    question_sign,
    read_name,
    read_sign,
)
from engines.timing_advisor import (  # noqa: E402
    get_current_quality,
)
from engines.multi_user_service import MultiUserFC60Service  # noqa: E402
from engines.ai_interpreter import (  # noqa: E402
    interpret_multi_user,
    interpret_reading,
)

# Backward-compatible alias — interpret_group was renamed to interpret_multi_user in Session 13
interpret_group = interpret_multi_user

# ─── Helpers ─────────────────────────────────────────────────────────────────


def _parse_datetime(dt_str: str | None) -> datetime:
    """Parse ISO 8601 string to datetime, defaulting to now UTC."""
    if not dt_str:
        return datetime.now(timezone.utc)
    try:
        if "T" in dt_str:
            return datetime.fromisoformat(dt_str)
        return datetime.strptime(dt_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        return datetime.now(timezone.utc)


# ─── Oracle Reading Service ──────────────────────────────────────────────────


class OracleReadingService:
    """Core service for oracle computations and reading persistence."""

    def __init__(self, db: Session, enc: EncryptionService | None = None):
        self.db = db
        self.enc = enc

    # ── Computation methods (ported from gRPC server.py) ──

    def get_reading(self, datetime_str: str | None, extended: bool = False) -> dict:
        """Full oracle reading for a date/time."""
        dt = _parse_datetime(datetime_str)
        y, m, d = dt.year, dt.month, dt.day
        h, mi, s = dt.hour, dt.minute, dt.second
        tz_h = dt.utcoffset().seconds // 3600 if dt.utcoffset() else 0
        tz_m = (dt.utcoffset().seconds % 3600) // 60 if dt.utcoffset() else 0

        # FC60 encoding
        fc60_result = encode_fc60(y, m, d, h, mi, s, tz_h, tz_m)
        stem_idx, branch_idx = ganzhi_year(y)

        element_balance = {
            "Wood": 0.2,
            "Fire": 0.2,
            "Earth": 0.2,
            "Metal": 0.2,
            "Water": 0.2,
        }
        element_balance[STEM_ELEMENTS[stem_idx]] = 0.4

        fc60_data = {
            "cycle": fc60_result.get("jdn", 0) % 60,
            "element": STEM_ELEMENTS[stem_idx],
            "polarity": STEM_POLARITY[stem_idx],
            "stem": STEM_NAMES[stem_idx],
            "branch": ANIMAL_NAMES[branch_idx],
            "year_number": numerology_reduce(sum(int(c) for c in str(y))),
            "month_number": numerology_reduce(m),
            "day_number": numerology_reduce(d),
            "energy_level": fc60_result.get("moon_illumination", 50.0) / 100.0,
            "element_balance": element_balance,
        }

        # Numerology
        lp = life_path(y, m, d)
        day_vib = numerology_reduce(d)
        py = personal_year(m, d, y)
        pm = numerology_reduce(m + numerology_reduce(sum(int(c) for c in str(y))))
        pd = numerology_reduce(d + m + numerology_reduce(sum(int(c) for c in str(y))))
        lp_info = LIFE_PATH_MEANINGS.get(lp, ("", ""))

        numerology_data = {
            "life_path": lp,
            "day_vibration": day_vib,
            "personal_year": py,
            "personal_month": pm,
            "personal_day": pd,
            "interpretation": f"{lp_info[0]}: {lp_info[1]}" if lp_info[0] else "",
        }

        # Zodiac
        zodiac_info = _get_zodiac(m, d)
        zodiac = {
            "sign": zodiac_info.get("sign", ""),
            "element": zodiac_info.get("element", ""),
            "ruling_planet": zodiac_info.get("ruling_planet", ""),
        }

        # Chinese calendar
        chinese = {
            "animal": ANIMAL_NAMES[branch_idx],
            "element": STEM_ELEMENTS[stem_idx],
            "yin_yang": STEM_POLARITY[stem_idx],
        }

        # Full multi-system reading via oracle.read_sign
        date_str = f"{y:04d}-{m:02d}-{d:02d}"
        time_str = f"{h:02d}:{mi:02d}"
        sign_result = read_sign(time_str, date=date_str, time_str=time_str)
        summary = sign_result.get("interpretation", "")
        systems = sign_result.get("systems", {})

        # Moon phase data
        moon_sys = systems.get("moon", {})
        moon_data = None
        if moon_sys and moon_sys.get("phase_name"):
            moon_data = {
                "phase_name": moon_sys.get("phase_name", ""),
                "illumination": moon_sys.get("illumination", 0),
                "age_days": moon_sys.get("age_days", 0),
                "meaning": moon_sys.get("meaning", ""),
                "emoji": moon_sys.get("emoji", ""),
            }

        # Angel numbers
        angel_sys = systems.get("angel", {})
        angel_data = None
        if angel_sys and angel_sys.get("matches"):
            angel_data = {
                "matches": [
                    {"number": m["number"], "meaning": m["meaning"]} for m in angel_sys["matches"]
                ]
            }

        # Chaldean numerology
        chaldean_sys = systems.get("chaldean", {})
        chaldean_data = None
        if chaldean_sys and chaldean_sys.get("value"):
            chaldean_data = {
                "value": chaldean_sys.get("value", 0),
                "meaning": chaldean_sys.get("meaning", ""),
                "letter_values": chaldean_sys.get("letter_values", ""),
            }

        # Ganzhi (Chinese cosmology) — richer than the basic chinese dict
        ganzhi_sys = systems.get("ganzhi", {})
        ganzhi_data = None
        if ganzhi_sys and ganzhi_sys.get("year_name"):
            ganzhi_data = {
                "year_name": ganzhi_sys.get("year_name", ""),
                "year_animal": ganzhi_sys.get("year_animal", ""),
                "stem_element": ganzhi_sys.get("stem_element", ""),
                "stem_polarity": ganzhi_sys.get("stem_polarity", ""),
                "hour_animal": ganzhi_sys.get("hour_animal", ""),
                "hour_branch": ganzhi_sys.get("hour_branch", ""),
            }

        # FC60 extended stamp data
        fc60_sys = systems.get("fc60", {})
        fc60_extended = None
        if fc60_sys and fc60_sys.get("stamp"):
            fc60_extended = {
                "stamp": fc60_sys.get("stamp", ""),
                "weekday_name": fc60_sys.get("weekday_name", ""),
                "weekday_planet": fc60_sys.get("weekday_planet", ""),
                "weekday_domain": fc60_sys.get("weekday_domain", ""),
            }

        # Zodiac quality (currently dropped from zodiac dict)
        zodiac_sys = systems.get("zodiac", {})
        if zodiac_sys.get("quality"):
            zodiac["quality"] = zodiac_sys["quality"]

        # Synchronicities
        synchronicities = sign_result.get("synchronicities", [])

        # AI interpretation
        ai_interpretation = None
        try:
            interp_result = interpret_reading(sign_result, format_type="advice")
            ai_interpretation = interp_result.text
        except Exception:
            logger.warning("AI interpretation unavailable for reading", exc_info=True)

        return {
            "fc60": fc60_data,
            "numerology": numerology_data,
            "zodiac": zodiac,
            "chinese": chinese,
            "moon": moon_data,
            "angel": angel_data,
            "chaldean": chaldean_data,
            "ganzhi": ganzhi_data,
            "fc60_extended": fc60_extended,
            "synchronicities": synchronicities,
            "ai_interpretation": ai_interpretation,
            "summary": summary,
            "generated_at": dt.isoformat(),
        }

    def get_question_sign(self, question: str) -> dict:
        """Ask a yes/no question with numerological context."""
        result = question_sign(question)

        reduced_numbers = result.get("numerology", {}).get("reduced", [])
        if reduced_numbers:
            primary = reduced_numbers[0]
            if primary in (11, 22, 33):
                answer = "maybe"
            elif primary % 2 == 1:
                answer = "yes"
            else:
                answer = "no"
            sign_number = primary
        else:
            qlen = sum(1 for c in question if c.isalpha())
            sign_number = numerology_reduce(qlen) if qlen > 0 else 7
            if sign_number in (11, 22, 33):
                answer = "maybe"
            elif sign_number % 2 == 1:
                answer = "yes"
            else:
                answer = "no"

        interpretation = result.get("reading", "") or result.get("advice", "")
        confidence = 0.7 if result.get("numerology", {}).get("meanings") else 0.5

        return {
            "question": question,
            "answer": answer,
            "sign_number": sign_number,
            "interpretation": interpretation,
            "confidence": confidence,
        }

    def get_name_reading(self, name: str) -> dict:
        """Name cipher reading."""
        result = read_name(name)

        letters = []
        element_cycle = ["Fire", "Earth", "Metal", "Water", "Wood"]
        for ch in name.upper():
            if ch.isalpha():
                val = LETTER_VALUES.get(ch, 0)
                elem = element_cycle[(val - 1) % 5] if val > 0 else ""
                letters.append({"letter": ch, "value": val, "element": elem})

        return {
            "name": name,
            "destiny_number": result.get("expression", 0),
            "soul_urge": result.get("soul_urge", 0),
            "personality": result.get("personality", 0),
            "letters": letters,
            "interpretation": result.get("interpretation", ""),
        }

    def get_daily_insight(self, date_str: str | None) -> dict:
        """Daily insight for a given date or today."""
        dt = _parse_datetime(date_str)
        result = daily_insight(dt)

        lucky = [str(n) for n in result.get("lucky_numbers", [])]

        return {
            "date": result.get("date", dt.strftime("%Y-%m-%d")),
            "insight": result.get("insight", ""),
            "lucky_numbers": lucky,
            "optimal_activity": result.get("energy", ""),
        }

    def suggest_range(
        self,
        scanned_ranges: list[str],
        puzzle_number: int,
        ai_level: int,
    ) -> dict:
        """AI-suggested scan range based on timing + coverage."""
        timing = get_current_quality()
        score = timing.get("score", 0.5)

        level = ai_level or 1
        if score >= 0.8:
            strategy = "cosmic"
            confidence = 0.8
        elif level >= 3:
            strategy = "gap_fill"
            confidence = 0.7
        else:
            strategy = "random"
            confidence = 0.5

        puzzle = puzzle_number or 66
        if 0 < puzzle <= 160:
            range_start = 1 << (puzzle - 1)
            range_end = (1 << puzzle) - 1
        else:
            range_start = 0x1
            range_end = 0xFFFFFFFFFFFFFFFF

        reasoning = (
            f"Strategy '{strategy}' selected. "
            f"Timing quality: {timing.get('quality', 'fair')} ({score:.2f}). "
            f"AI level: {level}. "
            f"Moon: {timing.get('moon_phase', 'unknown')}."
        )

        return {
            "range_start": hex(range_start),
            "range_end": hex(range_end),
            "strategy": strategy,
            "confidence": confidence,
            "reasoning": reasoning,
        }

    # ── Multi-user analysis ──

    def get_multi_user_reading(
        self, users: list[dict], include_interpretation: bool = True
    ) -> dict:
        """Run multi-user FC60 analysis via T3-S2 engine.

        Args:
            users: List of {name, birth_year, birth_month, birth_day} dicts.
            include_interpretation: Whether to generate AI narrative.

        Returns:
            Complete analysis dict with optional AI interpretation.
        """
        svc = MultiUserFC60Service()
        result = svc.analyze(users)
        result_dict = result.to_dict()

        if include_interpretation:
            try:
                interp = interpret_group(result_dict)
                result_dict["ai_interpretation"] = interp.to_dict()
            except Exception:
                logger.warning("AI interpretation unavailable, skipping", exc_info=True)
                result_dict["ai_interpretation"] = None
        else:
            result_dict["ai_interpretation"] = None

        return result_dict

    def store_multi_user_reading(
        self,
        primary_user_id: int | None,
        user_ids: list[int | None],
        result_dict: dict,
        ai_interpretation: dict | None,
    ) -> OracleReading:
        """Persist a multi-user reading + junction table entries."""
        enc_ai = None
        if ai_interpretation:
            ai_str = json.dumps(ai_interpretation)
            enc_ai = self.enc.encrypt_field(ai_str) if self.enc else ai_str

        reading = OracleReading(
            user_id=primary_user_id,
            is_multi_user=True,
            primary_user_id=primary_user_id,
            question="",
            sign_type="multi_user",
            sign_value=f"{result_dict.get('user_count', 0)}-user analysis",
            reading_result=json.dumps(result_dict),
            individual_results=json.dumps(result_dict.get("profiles", [])),
            compatibility_matrix=json.dumps(result_dict.get("pairwise_compatibility", [])),
            combined_energy=json.dumps(result_dict.get("group_energy", {})),
            ai_interpretation=enc_ai,
        )
        self.db.add(reading)
        self.db.flush()

        for i, uid in enumerate(user_ids):
            if uid is not None:
                entry = OracleReadingUser(
                    reading_id=reading.id,
                    user_id=uid,
                    is_primary=(uid == primary_user_id),
                )
                self.db.add(entry)

        self.db.flush()
        return reading

    # ── Daily reading (Session 16) ──

    async def create_daily_reading(
        self,
        user_id: int,
        date_str: str | None,
        locale: str,
        numerology_system: str,
        force_regenerate: bool = False,
        progress_callback=None,
    ) -> dict:
        """Create a daily reading (or return cached version).

        1. Check oracle_daily_readings for existing (user_id, date)
        2. If found and not force_regenerate: return cached reading
        3. If not found: generate via orchestrator, store, create cache entry
        """
        target_date_str = date_str or datetime.now(timezone.utc).strftime("%Y-%m-%d")
        target_date = datetime.strptime(target_date_str, "%Y-%m-%d")
        reading_date = target_date.date()

        # Check cache (unless force_regenerate)
        if not force_regenerate:
            cached = self._get_daily_cache(user_id, reading_date)
            if cached:
                return cached

        # Load user, build profile, generate reading
        oracle_user = self._get_oracle_user(user_id)
        user_profile = self._build_user_profile(oracle_user, numerology_system)

        from oracle_service.reading_orchestrator import ReadingOrchestrator

        orchestrator = ReadingOrchestrator(progress_callback=progress_callback)
        result = await orchestrator.generate_daily_reading(user_profile, target_date, locale)

        # Store in oracle_readings
        ai_text = ""
        ai_interp = result.get("ai_interpretation")
        if isinstance(ai_interp, dict):
            ai_text = ai_interp.get("full_text", "")
        elif isinstance(ai_interp, str):
            ai_text = ai_interp

        reading = self.store_reading(
            user_id=user_id,
            sign_type="daily",
            sign_value=target_date_str,
            question=None,
            reading_result=result.get("framework_result"),
            ai_interpretation=ai_text or None,
        )

        # Create cache entry in oracle_daily_readings
        self._create_daily_cache(user_id, reading_date, reading.id)

        result["id"] = reading.id
        created_at = reading.created_at
        result["created_at"] = (
            created_at.isoformat() if isinstance(created_at, datetime) else str(created_at or "")
        )

        return result

    def get_cached_daily_reading(self, user_id: int, date_str: str | None) -> dict | None:
        """Get cached daily reading for a user and date. Returns None if not cached."""
        target_date_str = date_str or datetime.now(timezone.utc).strftime("%Y-%m-%d")
        target_date = datetime.strptime(target_date_str, "%Y-%m-%d").date()
        return self._get_daily_cache(user_id, target_date)

    def _get_daily_cache(self, user_id: int, reading_date) -> dict | None:
        """Look up daily reading via oracle_daily_readings -> oracle_readings join."""
        from app.orm.oracle_reading import OracleDailyReading

        cache_row = (
            self.db.query(OracleDailyReading)
            .filter(
                OracleDailyReading.user_id == user_id,
                OracleDailyReading.reading_date == reading_date,
            )
            .first()
        )
        if not cache_row:
            return None

        reading = (
            self.db.query(OracleReading)
            .filter(
                OracleReading.id == cache_row.reading_id,
            )
            .first()
        )
        if not reading:
            return None

        # Reconstruct response from stored reading
        reading_result = None
        if reading.reading_result:
            try:
                reading_result = (
                    json.loads(reading.reading_result)
                    if isinstance(reading.reading_result, str)
                    else reading.reading_result
                )
            except (json.JSONDecodeError, TypeError):
                reading_result = {}
        reading_result = reading_result or {}

        created_at = reading.created_at
        created_str = (
            created_at.isoformat() if isinstance(created_at, datetime) else str(created_at or "")
        )

        return {
            "id": reading.id,
            "reading_type": "daily",
            "sign_value": reading.sign_value,
            "framework_result": reading_result,
            "ai_interpretation": {"full_text": reading.ai_interpretation or ""},
            "confidence": reading_result.get("confidence", {}),
            "patterns": (
                reading_result.get("patterns", {}).get("detected", [])
                if isinstance(reading_result.get("patterns"), dict)
                else []
            ),
            "fc60_stamp": (
                reading_result.get("fc60_stamp", {}).get("fc60", "")
                if isinstance(reading_result.get("fc60_stamp"), dict)
                else ""
            ),
            "numerology": reading_result.get("numerology"),
            "moon": reading_result.get("moon"),
            "ganzhi": reading_result.get("ganzhi"),
            "daily_insights": reading_result.get("daily_insights", {}),
            "locale": "en",
            "created_at": created_str,
            "_cached": True,
        }

    def _create_daily_cache(self, user_id: int, reading_date, reading_id: int) -> None:
        """Insert row into oracle_daily_readings. Handles race condition via unique constraint."""
        from app.orm.oracle_reading import OracleDailyReading
        from sqlalchemy.exc import IntegrityError

        try:
            cache_entry = OracleDailyReading(
                user_id=user_id,
                reading_date=reading_date,
                reading_id=reading_id,
            )
            self.db.add(cache_entry)
            self.db.flush()
        except IntegrityError:
            self.db.rollback()

    def _get_oracle_user(self, user_id: int):
        """Load oracle user or raise ValueError."""
        from app.orm.oracle_user import OracleUser

        oracle_user = (
            self.db.query(OracleUser)
            .filter(
                OracleUser.id == user_id,
                OracleUser.deleted_at.is_(None),
            )
            .first()
        )
        if not oracle_user:
            raise ValueError(f"Oracle user {user_id} not found")
        return oracle_user

    # ── Multi-user framework reading (Session 16) ──

    async def create_multi_user_framework_reading(
        self,
        user_ids: list[int],
        primary_user_index: int,
        date_str: str | None,
        locale: str,
        numerology_system: str,
        include_interpretation: bool,
        progress_callback=None,
    ) -> dict:
        """Create multi-user compatibility reading using framework pipeline."""
        user_profiles = []
        for uid in user_ids:
            oracle_user = self._get_oracle_user(uid)
            profile = self._build_user_profile(oracle_user, numerology_system)
            user_profiles.append(profile)

        target_date = _parse_datetime(date_str) if date_str else None

        from oracle_service.reading_orchestrator import ReadingOrchestrator

        orchestrator = ReadingOrchestrator(progress_callback=progress_callback)
        result = await orchestrator.generate_multi_user_reading(
            user_profiles,
            primary_user_index,
            target_date,
            locale,
            include_interpretation,
        )

        # Store main reading
        primary_uid = user_ids[primary_user_index]
        reading = self.store_multi_user_reading(
            primary_user_id=primary_uid,
            user_ids=user_ids,
            result_dict={
                "individual_results": result.get("individual_readings"),
                "compatibility_matrix": result.get("pairwise_compatibility"),
                "combined_energy": result.get("group_analysis"),
                "user_count": result["user_count"],
                "pair_count": result["pair_count"],
                "computation_ms": result["computation_ms"],
            },
            ai_interpretation=result.get("ai_interpretation"),
        )

        result["id"] = reading.id
        created_at = reading.created_at
        result["created_at"] = (
            created_at.isoformat() if isinstance(created_at, datetime) else str(created_at or "")
        )

        return result

    # ── Framework reading pipeline (Session 14+) ──

    def _build_user_profile(
        self,
        oracle_user: "OracleUser",
        numerology_system: str = "pythagorean",
    ) -> "UserProfile":
        """Convert OracleUser ORM to UserProfile dataclass for framework bridge."""
        from oracle_service.models.reading_types import (
            UserProfile as FrameworkUserProfile,
        )

        # Parse birthday to components
        bday = oracle_user.birthday
        if isinstance(bday, str):
            parts = bday.split("-")
            birth_year, birth_month, birth_day = (
                int(parts[0]),
                int(parts[1]),
                int(parts[2]),
            )
        elif hasattr(bday, "year"):
            birth_year, birth_month, birth_day = bday.year, bday.month, bday.day
        else:
            birth_year, birth_month, birth_day = 2000, 1, 1

        # Decrypt mother_name if encrypted
        mother_name = oracle_user.mother_name
        if self.enc and mother_name:
            mother_name = self.enc.decrypt_field(mother_name)

        return FrameworkUserProfile(
            user_id=oracle_user.id,
            full_name=oracle_user.name,
            birth_day=birth_day,
            birth_month=birth_month,
            birth_year=birth_year,
            mother_name=mother_name,
            gender=getattr(oracle_user, "gender", None),
            heart_rate_bpm=getattr(oracle_user, "heart_rate_bpm", None),
            timezone_hours=getattr(oracle_user, "timezone_hours", 0) or 0,
            timezone_minutes=getattr(oracle_user, "timezone_minutes", 0) or 0,
            numerology_system=numerology_system,
        )

    async def create_framework_reading(
        self,
        user_id: int,
        reading_type: str,
        sign_value: str,
        date_str: str | None,
        locale: str,
        numerology_system: str,
        progress_callback=None,
    ) -> dict:
        """Create a reading using the framework pipeline.

        Returns dict ready for FrameworkReadingResponse + the OracleReading DB row.
        """
        from app.orm.oracle_user import OracleUser

        # 1. Load oracle_user
        oracle_user = (
            self.db.query(OracleUser)
            .filter(
                OracleUser.id == user_id,
                OracleUser.deleted_at.is_(None),
            )
            .first()
        )
        if not oracle_user:
            raise ValueError(f"Oracle user {user_id} not found")

        # 2. Build UserProfile
        user_profile = self._build_user_profile(oracle_user, numerology_system)
        if numerology_system != "auto":
            user_profile.numerology_system = numerology_system

        # 3. Parse sign_value for time reading
        parts = sign_value.split(":")
        hour, minute, second = int(parts[0]), int(parts[1]), int(parts[2])
        target_date = _parse_datetime(date_str) if date_str else None

        # 4. Orchestrate reading
        from oracle_service.reading_orchestrator import ReadingOrchestrator

        orchestrator = ReadingOrchestrator(progress_callback=progress_callback)
        result = await orchestrator.generate_time_reading(
            user_profile, hour, minute, second, target_date, locale
        )

        # 5. Store in database
        ai_text = ""
        ai_interp = result.get("ai_interpretation")
        if isinstance(ai_interp, dict):
            ai_text = ai_interp.get("full_text", "")
        elif isinstance(ai_interp, str):
            ai_text = ai_interp

        reading = self.store_reading(
            user_id=user_id,
            sign_type="time",
            sign_value=sign_value,
            question=None,
            reading_result=result.get("framework_result"),
            ai_interpretation=ai_text or None,
        )

        result["id"] = reading.id
        created_at = reading.created_at
        if isinstance(created_at, datetime):
            result["created_at"] = created_at.isoformat()
        else:
            result["created_at"] = str(created_at) if created_at else ""

        return result

    # ── Framework name/question reading (Session 15) ──

    def get_name_reading_v2(
        self,
        name: str,
        user_id: int | None = None,
        numerology_system: str = "pythagorean",
        include_ai: bool = True,
    ) -> dict:
        """Name reading using framework via ReadingOrchestrator."""
        from oracle_service.reading_orchestrator import ReadingOrchestrator

        # Resolve user profile if user_id provided
        birth_day = birth_month = birth_year = None
        mother_name = gender = None
        if user_id:
            from app.orm.oracle_user import OracleUser

            oracle_user = (
                self.db.query(OracleUser)
                .filter(OracleUser.id == user_id, OracleUser.deleted_at.is_(None))
                .first()
            )
            if not oracle_user:
                raise ValueError(f"Oracle user {user_id} not found")
            bday = oracle_user.birthday
            if isinstance(bday, str):
                parts = bday.split("-")
                birth_year, birth_month, birth_day = (
                    int(parts[0]),
                    int(parts[1]),
                    int(parts[2]),
                )
            elif hasattr(bday, "year"):
                birth_year, birth_month, birth_day = bday.year, bday.month, bday.day
            mother_name = oracle_user.mother_name
            if self.enc and mother_name:
                mother_name = self.enc.decrypt_field(mother_name)
            gender = getattr(oracle_user, "gender", None)

        orchestrator = ReadingOrchestrator()
        return orchestrator.generate_name_reading(
            name=name,
            user_id=user_id,
            birth_day=birth_day,
            birth_month=birth_month,
            birth_year=birth_year,
            mother_name=mother_name,
            gender=gender,
            numerology_system=numerology_system,
            include_ai=include_ai,
        )

    def get_question_reading_v2(
        self,
        question: str,
        user_id: int | None = None,
        numerology_system: str = "auto",
        include_ai: bool = True,
    ) -> dict:
        """Question reading using framework via ReadingOrchestrator."""
        from oracle_service.reading_orchestrator import ReadingOrchestrator

        # Resolve user profile if user_id provided
        birth_day = birth_month = birth_year = None
        full_name = mother_name = gender = None
        if user_id:
            from app.orm.oracle_user import OracleUser

            oracle_user = (
                self.db.query(OracleUser)
                .filter(OracleUser.id == user_id, OracleUser.deleted_at.is_(None))
                .first()
            )
            if not oracle_user:
                raise ValueError(f"Oracle user {user_id} not found")
            bday = oracle_user.birthday
            if isinstance(bday, str):
                parts = bday.split("-")
                birth_year, birth_month, birth_day = (
                    int(parts[0]),
                    int(parts[1]),
                    int(parts[2]),
                )
            elif hasattr(bday, "year"):
                birth_year, birth_month, birth_day = bday.year, bday.month, bday.day
            full_name = oracle_user.name
            mother_name = oracle_user.mother_name
            if self.enc and mother_name:
                mother_name = self.enc.decrypt_field(mother_name)
            gender = getattr(oracle_user, "gender", None)

        orchestrator = ReadingOrchestrator()
        return orchestrator.generate_question_reading(
            question=question,
            user_id=user_id,
            birth_day=birth_day,
            birth_month=birth_month,
            birth_year=birth_year,
            full_name=full_name,
            mother_name=mother_name,
            gender=gender,
            numerology_system=numerology_system,
            include_ai=include_ai,
        )

    # ── DB storage methods ──

    def store_reading(
        self,
        user_id: int | None,
        sign_type: str,
        sign_value: str,
        question: str | None,
        reading_result: dict | None,
        ai_interpretation: str | None,
    ) -> OracleReading:
        """Create an OracleReading row with encrypted sensitive fields."""
        enc_question = question or ""
        enc_ai = ai_interpretation
        if self.enc:
            enc_question = self.enc.encrypt_field(enc_question) if enc_question else ""
            enc_ai = self.enc.encrypt_field(enc_ai) if enc_ai else enc_ai

        reading = OracleReading(
            user_id=user_id,
            sign_type=sign_type,
            sign_value=sign_value,
            question=enc_question,
            reading_result=json.dumps(reading_result) if reading_result else None,
            ai_interpretation=enc_ai,
        )
        self.db.add(reading)
        self.db.flush()
        return reading

    def get_reading_by_id(self, reading_id: int) -> dict | None:
        """Fetch a reading by ID, decrypt, and return as dict."""
        row = self.db.query(OracleReading).filter(OracleReading.id == reading_id).first()
        if not row:
            return None
        return self._decrypt_reading(row)

    def list_readings(
        self,
        user_id: int | None,
        is_admin: bool,
        limit: int,
        offset: int,
        sign_type: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        is_favorite: bool | None = None,
        search_query: str | None = None,
    ) -> tuple[list[dict], int]:
        """Query readings with filters + pagination. Excludes soft-deleted."""
        query = self.db.query(OracleReading).filter(OracleReading.deleted_at.is_(None))

        if sign_type:
            query = query.filter(OracleReading.sign_type == sign_type)
        if date_from:
            query = query.filter(OracleReading.created_at >= _parse_datetime(date_from))
        if date_to:
            query = query.filter(OracleReading.created_at <= _parse_datetime(date_to))
        if is_favorite is not None:
            query = query.filter(OracleReading.is_favorite == is_favorite)
        if search_query:
            from sqlalchemy import or_

            # LIKE fallback for SQLite / PostgreSQL without tsvector
            pattern = f"%{search_query}%"
            query = query.filter(
                or_(
                    OracleReading.question.like(pattern),
                    OracleReading.sign_value.like(pattern),
                )
            )

        total = query.count()
        rows = query.order_by(OracleReading.created_at.desc()).offset(offset).limit(limit).all()
        return [self._decrypt_reading(r) for r in rows], total

    def soft_delete_reading(self, reading_id: int) -> bool:
        """Soft-delete a reading by setting deleted_at timestamp."""
        row = (
            self.db.query(OracleReading)
            .filter(OracleReading.id == reading_id, OracleReading.deleted_at.is_(None))
            .first()
        )
        if not row:
            return False
        row.deleted_at = datetime.now(timezone.utc)
        self.db.flush()
        return True

    def toggle_favorite(self, reading_id: int) -> dict | None:
        """Toggle the is_favorite flag on a reading."""
        row = (
            self.db.query(OracleReading)
            .filter(OracleReading.id == reading_id, OracleReading.deleted_at.is_(None))
            .first()
        )
        if not row:
            return None
        row.is_favorite = not row.is_favorite
        self.db.flush()
        return self._decrypt_reading(row)

    def get_reading_stats(self) -> dict:
        """Aggregate reading statistics."""
        from sqlalchemy import func as sqla_func

        base = self.db.query(OracleReading).filter(OracleReading.deleted_at.is_(None))

        total = base.count()
        favorites = base.filter(OracleReading.is_favorite.is_(True)).count()

        # Count by sign_type
        type_counts = (
            base.with_entities(OracleReading.sign_type, sqla_func.count())
            .group_by(OracleReading.sign_type)
            .all()
        )
        by_type = {t: c for t, c in type_counts}

        # by_month and most_active_day use PostgreSQL-only functions (to_char)
        # Gracefully handle SQLite (test env) by catching OperationalError
        by_month: list[dict] = []
        most_active_day: str | None = None
        try:
            month_counts = (
                base.with_entities(
                    sqla_func.to_char(OracleReading.created_at, "YYYY-MM").label("month"),
                    sqla_func.count().label("count"),
                )
                .group_by("month")
                .order_by(sqla_func.to_char(OracleReading.created_at, "YYYY-MM"))
                .limit(12)
                .all()
            )
            by_month = [{"month": m, "count": c} for m, c in month_counts]

            day_counts = (
                base.with_entities(
                    sqla_func.to_char(OracleReading.created_at, "Day").label("day_name"),
                    sqla_func.count().label("count"),
                )
                .group_by("day_name")
                .order_by(sqla_func.count().desc())
                .first()
            )
            most_active_day = day_counts[0].strip() if day_counts else None
        except Exception:
            # SQLite fallback — skip date-based aggregates
            pass

        return {
            "total_readings": total,
            "by_type": by_type,
            "by_month": by_month,
            "favorites_count": favorites,
            "most_active_day": most_active_day,
        }

    def _decrypt_reading(self, row: OracleReading) -> dict:
        """ORM row → dict with decrypted fields + parsed JSON."""
        question = row.question
        ai_interpretation = row.ai_interpretation
        if self.enc:
            question = self.enc.decrypt_field(question) if question else question
            ai_interpretation = (
                self.enc.decrypt_field(ai_interpretation)
                if ai_interpretation
                else ai_interpretation
            )

        reading_result = None
        if row.reading_result:
            try:
                reading_result = json.loads(row.reading_result)
            except (json.JSONDecodeError, TypeError):
                reading_result = None

        created_at = row.created_at
        if isinstance(created_at, datetime):
            created_at = created_at.isoformat()
        else:
            created_at = str(created_at) if created_at else ""

        return {
            "id": row.id,
            "user_id": row.user_id,
            "sign_type": row.sign_type,
            "sign_value": row.sign_value,
            "question": question,
            "reading_result": reading_result,
            "ai_interpretation": ai_interpretation,
            "created_at": created_at,
            "is_favorite": getattr(row, "is_favorite", False),
            "deleted_at": (
                row.deleted_at.isoformat() if getattr(row, "deleted_at", None) else None
            ),
        }


def get_oracle_reading_service(
    db: Session = Depends(get_db),
    enc: EncryptionService | None = Depends(get_encryption_service),
) -> OracleReadingService:
    """FastAPI dependency — returns an OracleReadingService."""
    return OracleReadingService(db, enc)


# ─── WebSocket progress manager ─────────────────────────────────────────────


class OracleProgressManager:
    """Lightweight WS manager for oracle-specific progress events."""

    def __init__(self):
        self.connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.connections:
            self.connections.remove(websocket)

    async def send_progress(self, step: int, total: int, message: str, reading_type: str = "time"):
        payload = {
            "step": step,
            "total": total,
            "message": message,
            "reading_type": reading_type,
        }
        for ws in list(self.connections):
            try:
                await ws.send_json(payload)
            except Exception:
                self.disconnect(ws)


oracle_progress = OracleProgressManager()
