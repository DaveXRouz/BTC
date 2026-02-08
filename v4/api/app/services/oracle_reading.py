"""Oracle reading service — computation via V3 engines + DB persistence."""

import json
import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import Depends, WebSocket
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.orm.oracle_reading import OracleReading
from app.services.security import EncryptionService, get_encryption_service

logger = logging.getLogger(__name__)

# ─── Engine imports via sys.path shim (same approach as gRPC server) ─────────
#
# Two paths needed:
# 1. Parent of oracle_service/ so `import oracle_service` works (for logic/__init__.py)
# 2. Inside oracle_service/ so `from engines.xxx` works (V3-style imports)

_ORACLE_PARENT_DIR = str(Path(__file__).resolve().parents[3] / "services" / "oracle")
_ORACLE_SERVICE_DIR = str(
    Path(__file__).resolve().parents[3] / "services" / "oracle" / "oracle_service"
)
if _ORACLE_PARENT_DIR not in sys.path:
    sys.path.insert(0, _ORACLE_PARENT_DIR)
if _ORACLE_SERVICE_DIR not in sys.path:
    sys.path.insert(0, _ORACLE_SERVICE_DIR)

import oracle_service  # noqa: E402, F401 — triggers shim for absolute imports

from engines.fc60 import (  # noqa: E402
    ANIMAL_NAMES,
    ELEMENT_NAMES,
    STEM_ELEMENTS,
    STEM_NAMES,
    STEM_POLARITY,
    encode_fc60,
    ganzhi_year,
)
from engines.numerology import (  # noqa: E402
    LETTER_VALUES,
    LIFE_PATH_MEANINGS,
    life_path,
    name_to_number,
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
from logic.timing_advisor import (
    get_current_quality,
    get_optimal_hours_today,
)  # noqa: E402

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

        # Summary via oracle.read_sign
        date_str = f"{y:04d}-{m:02d}-{d:02d}"
        time_str = f"{h:02d}:{mi:02d}"
        sign_result = read_sign(time_str, date=date_str, time_str=time_str)
        summary = sign_result.get("interpretation", "")

        return {
            "fc60": fc60_data,
            "numerology": numerology_data,
            "zodiac": zodiac,
            "chinese": chinese,
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
        row = (
            self.db.query(OracleReading).filter(OracleReading.id == reading_id).first()
        )
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
    ) -> tuple[list[dict], int]:
        """Query readings with filters + pagination."""
        query = self.db.query(OracleReading)

        if sign_type:
            query = query.filter(OracleReading.sign_type == sign_type)

        total = query.count()
        rows = (
            query.order_by(OracleReading.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        return [self._decrypt_reading(r) for r in rows], total

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

    async def send_progress(self, step: int, total: int, message: str):
        payload = {"step": step, "total": total, "message": message}
        for ws in list(self.connections):
            try:
                await ws.send_json(payload)
            except Exception:
                self.disconnect(ws)


oracle_progress = OracleProgressManager()
