"""
NPS V4 Oracle Service — gRPC server.

Wraps V3 engines (fc60, numerology, oracle, timing_advisor) with gRPC interface.
These engines are near-zero rewrite — they are pure computation with no I/O.

To run:
    python -m oracle_service.server
"""

import logging
import os
import signal
import sys
import time
from concurrent import futures
from datetime import datetime, timezone

import grpc
from grpc_health.v1 import health, health_pb2, health_pb2_grpc

import oracle_service  # triggers sys.path shim
from oracle_service.grpc_gen import oracle_pb2, oracle_pb2_grpc

# V3 engines (resolved via sys.path shim in oracle_service/__init__.py)
from engines.fc60 import (
    encode_fc60,
    ganzhi_year,
    ANIMAL_NAMES,
    ELEMENT_NAMES,
    STEM_ELEMENTS,
    STEM_POLARITY,
    STEM_NAMES,
)
from engines.numerology import (
    life_path,
    numerology_reduce,
    name_to_number,
    name_soul_urge,
    name_personality,
    personal_year,
    LETTER_VALUES,
    LIFE_PATH_MEANINGS,
)
from engines.oracle import (
    read_sign,
    read_name,
    question_sign,
    daily_insight,
    _get_zodiac,
)
from logic.timing_advisor import get_current_quality, get_optimal_hours_today

# Structured logging (graceful fallback if devops package not available)
try:
    from devops.logging.oracle_logger import setup_oracle_logger

    setup_oracle_logger()
except ImportError:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
logger = logging.getLogger(__name__)

# Metrics collection (graceful fallback if devops package not available)
try:
    from devops.monitoring.oracle_metrics import metrics as _metrics

    _metrics_available = True
except ImportError:
    _metrics_available = False
    _metrics = None

_start_time = time.time()
_VERSION = "4.0.0"


class _track_rpc:
    """Context manager that times an RPC call and records metrics."""

    def __init__(self, name):
        self.name = name
        self.t0 = None

    def __enter__(self):
        self.t0 = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration_ms = (time.perf_counter() - self.t0) * 1000
        if _metrics_available:
            if exc_type is not None:
                _metrics.record_error(self.name, exc_type.__name__)
            else:
                _metrics.record_rpc(self.name, duration_ms)
        return False


def _parse_datetime(dt_str):
    """Parse ISO 8601 string to datetime, defaulting to now UTC."""
    if not dt_str:
        return datetime.now(timezone.utc)
    try:
        # Try ISO 8601 with timezone
        if "T" in dt_str:
            return datetime.fromisoformat(dt_str)
        # Date-only
        return datetime.strptime(dt_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        return datetime.now(timezone.utc)


class OracleServiceImpl(oracle_pb2_grpc.OracleServiceServicer):
    """Implements oracle.proto OracleService — 8 RPCs wrapping V3 engines."""

    def HealthCheck(self, request, context):
        with _track_rpc("HealthCheck"):
            uptime = int(time.time() - _start_time)

            checks = {}
            try:
                from engines.fc60 import self_test

                results = self_test()
                passed = sum(1 for r in results if r[1])
                checks["fc60"] = f"{passed}/{len(results)} vectors"
            except Exception as e:
                checks["fc60"] = f"error: {e}"

            try:
                name_to_number("TEST")
                checks["numerology"] = "ok"
            except Exception as e:
                checks["numerology"] = f"error: {e}"

            try:
                read_sign("test")
                checks["oracle"] = "ok"
            except Exception as e:
                checks["oracle"] = f"error: {e}"

            try:
                get_current_quality()
                checks["timing"] = "ok"
            except Exception as e:
                checks["timing"] = f"error: {e}"

            all_ok = all("error" not in v for v in checks.values())

            return oracle_pb2.HealthResponse(
                status="healthy" if all_ok else "degraded",
                version=_VERSION,
                uptime_seconds=uptime,
                checks=checks,
            )

    def GetReading(self, request, context):
        with _track_rpc("GetReading"):
            logger.info("GetReading called: datetime=%s", request.datetime)
            dt = _parse_datetime(request.datetime)
            y, m, d = dt.year, dt.month, dt.day
            h, mi, s = dt.hour, dt.minute, dt.second
            tz_h = dt.utcoffset().seconds // 3600 if dt.utcoffset() else 0
            tz_m = (dt.utcoffset().seconds % 3600) // 60 if dt.utcoffset() else 0

            # FC60 encoding
            fc60_result = encode_fc60(y, m, d, h, mi, s, tz_h, tz_m)

            # Ganzhi for Chinese calendar
            stem_idx, branch_idx = ganzhi_year(y)

            # FC60Reading proto
            element_name = ELEMENT_NAMES[branch_idx % 5]
            fc60_reading = oracle_pb2.FC60Reading(
                cycle=fc60_result.get("jdn", 0) % 60,
                element=STEM_ELEMENTS[stem_idx],
                polarity=STEM_POLARITY[stem_idx],
                stem=STEM_NAMES[stem_idx],
                branch=ANIMAL_NAMES[branch_idx],
                year_number=numerology_reduce(sum(int(c) for c in str(y))),
                month_number=numerology_reduce(m),
                day_number=numerology_reduce(d),
                energy_level=fc60_result.get("moon_illumination", 50.0) / 100.0,
                element_balance={
                    "Wood": 0.2,
                    "Fire": 0.2,
                    "Earth": 0.2,
                    "Metal": 0.2,
                    "Water": 0.2,
                },
            )
            # Boost the dominant element
            fc60_reading.element_balance[STEM_ELEMENTS[stem_idx]] = 0.4

            # Numerology
            lp = life_path(y, m, d)
            day_vib = numerology_reduce(d)
            py = personal_year(m, d, y)
            pm = numerology_reduce(m + numerology_reduce(sum(int(c) for c in str(y))))
            pd = numerology_reduce(
                d + m + numerology_reduce(sum(int(c) for c in str(y)))
            )

            lp_info = LIFE_PATH_MEANINGS.get(lp, ("", ""))
            numerology_reading = oracle_pb2.NumerologyReading(
                life_path=lp,
                day_vibration=day_vib,
                personal_year=py,
                personal_month=pm,
                personal_day=pd,
                interpretation=f"{lp_info[0]}: {lp_info[1]}" if lp_info[0] else "",
            )

            # Zodiac
            zodiac_info = _get_zodiac(m, d)
            zodiac = oracle_pb2.ZodiacInfo(
                sign=zodiac_info.get("sign", ""),
                element=zodiac_info.get("element", ""),
                ruling_planet=zodiac_info.get("ruling_planet", ""),
            )

            # Chinese calendar
            chinese = oracle_pb2.ChineseCalendar(
                animal=ANIMAL_NAMES[branch_idx],
                element=STEM_ELEMENTS[stem_idx],
                yin_yang=STEM_POLARITY[stem_idx],
            )

            # Summary via oracle.read_sign
            date_str = f"{y:04d}-{m:02d}-{d:02d}"
            time_str = f"{h:02d}:{mi:02d}"
            sign_result = read_sign(time_str, date=date_str, time_str=time_str)
            summary = sign_result.get("interpretation", "")

            return oracle_pb2.ReadingResponse(
                fc60=fc60_reading,
                numerology=numerology_reading,
                zodiac=zodiac,
                chinese=chinese,
                summary=summary,
                generated_at=int(time.time()),
            )

    def GetNameReading(self, request, context):
        with _track_rpc("GetNameReading"):
            logger.info("GetNameReading called: name=%s", request.name)
            if not request.name:
                context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
                context.set_details("name is required")
                return oracle_pb2.NameResponse()

            name = request.name
            result = read_name(name)

            # Letter analysis
            letters = []
            element_cycle = ["Fire", "Earth", "Metal", "Water", "Wood"]
            for ch in name.upper():
                if ch.isalpha():
                    val = LETTER_VALUES.get(ch, 0)
                    elem = element_cycle[(val - 1) % 5] if val > 0 else ""
                    letters.append(
                        oracle_pb2.LetterAnalysis(
                            letter=ch,
                            value=val,
                            element=elem,
                        )
                    )

            return oracle_pb2.NameResponse(
                name=name,
                destiny_number=result.get("expression", 0),
                soul_urge=result.get("soul_urge", 0),
                personality=result.get("personality", 0),
                letters=letters,
                interpretation=result.get("interpretation", ""),
            )

    def GetQuestionSign(self, request, context):
        with _track_rpc("GetQuestionSign"):
            logger.info("GetQuestionSign called: question=%s", request.question)
            if not request.question:
                context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
                context.set_details("question is required")
                return oracle_pb2.QuestionResponse()

            result = question_sign(request.question)

            # Determine answer from numerology
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
                # Use question length as fallback
                qlen = sum(1 for c in request.question if c.isalpha())
                sign_number = numerology_reduce(qlen) if qlen > 0 else 7
                if sign_number in (11, 22, 33):
                    answer = "maybe"
                elif sign_number % 2 == 1:
                    answer = "yes"
                else:
                    answer = "no"

            interpretation = result.get("reading", "") or result.get("advice", "")
            confidence = 0.7 if result.get("numerology", {}).get("meanings") else 0.5

            return oracle_pb2.QuestionResponse(
                question=request.question,
                answer=answer,
                sign_number=sign_number,
                interpretation=interpretation,
                confidence=confidence,
            )

    def GetDailyInsight(self, request, context):
        with _track_rpc("GetDailyInsight"):
            logger.info("GetDailyInsight called: date=%s", request.date)
            dt = (
                _parse_datetime(request.date)
                if request.date
                else datetime.now(timezone.utc)
            )

            result = daily_insight(dt)

            # Build FC60 reading for the day
            y, m, d = dt.year, dt.month, dt.day
            fc60_result = encode_fc60(y, m, d, include_time=False)
            stem_idx, branch_idx = ganzhi_year(y)

            fc60_reading = oracle_pb2.FC60Reading(
                cycle=fc60_result.get("jdn", 0) % 60,
                element=STEM_ELEMENTS[stem_idx],
                polarity=STEM_POLARITY[stem_idx],
                stem=STEM_NAMES[stem_idx],
                branch=ANIMAL_NAMES[branch_idx],
                year_number=numerology_reduce(sum(int(c) for c in str(y))),
                month_number=numerology_reduce(m),
                day_number=numerology_reduce(d),
                energy_level=fc60_result.get("moon_illumination", 50.0) / 100.0,
            )

            # Numerology
            lp = life_path(y, m, d)
            day_vib = numerology_reduce(d)
            lp_info = LIFE_PATH_MEANINGS.get(lp, ("", ""))
            numerology_reading = oracle_pb2.NumerologyReading(
                life_path=lp,
                day_vibration=day_vib,
                personal_year=personal_year(m, d, y),
                interpretation=f"{lp_info[0]}: {lp_info[1]}" if lp_info[0] else "",
            )

            lucky = [str(n) for n in result.get("lucky_numbers", [])]

            return oracle_pb2.DailyResponse(
                date=result.get("date", dt.strftime("%Y-%m-%d")),
                insight=result.get("insight", ""),
                fc60=fc60_reading,
                numerology=numerology_reading,
                lucky_numbers=lucky,
                optimal_activity=result.get("energy", ""),
            )

    def GetTimingAlignment(self, request, context):
        with _track_rpc("GetTimingAlignment"):
            logger.info("GetTimingAlignment called")
            quality_result = get_current_quality()
            hours_result = get_optimal_hours_today()

            # Build optimal hours (top 5)
            optimal_hours = []
            for hour, score in hours_result[:5]:
                optimal_hours.append(
                    oracle_pb2.OptimalHour(
                        hour=hour,
                        score=score,
                        reason=f"Hour {hour} numerological alignment",
                    )
                )

            # Parse factors from reasoning
            factors = {}
            reasoning = quality_result.get("reasoning", "")
            for part in reasoning.split("; "):
                if "score" in part:
                    key = part.split(":")[0].strip() if ":" in part else part[:20]
                    try:
                        score_str = part.split("score ")[-1].rstrip(")")
                        factors[key] = float(score_str)
                    except (ValueError, IndexError):
                        pass

            return oracle_pb2.TimingResponse(
                alignment_score=quality_result.get("score", 0.0),
                quality=quality_result.get("quality", "fair"),
                optimal_hours=optimal_hours,
                moon_phase=quality_result.get("moon_phase", ""),
                factors=factors,
            )

    def SuggestRange(self, request, context):
        with _track_rpc("SuggestRange"):
            logger.info(
                "SuggestRange called: puzzle=%d level=%d",
                request.puzzle_number,
                request.ai_level,
            )

            # Use timing quality to influence strategy
            timing = get_current_quality()
            score = timing.get("score", 0.5)

            # Determine strategy based on AI level and timing
            level = request.ai_level or 1
            if score >= 0.8:
                strategy = "cosmic"
                confidence = 0.8
            elif level >= 3:
                strategy = "gap_fill"
                confidence = 0.7
            else:
                strategy = "random"
                confidence = 0.5

            # Calculate range based on puzzle number
            puzzle = request.puzzle_number or 66
            if puzzle > 0 and puzzle <= 160:
                # Bitcoin puzzle key space: 2^(puzzle-1) to 2^puzzle - 1
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

            return oracle_pb2.RangeResponse(
                range_start=hex(range_start),
                range_end=hex(range_end),
                strategy=strategy,
                confidence=confidence,
                reasoning=reasoning,
            )

    def AnalyzeSession(self, request, context):
        with _track_rpc("AnalyzeSession"):
            logger.info("AnalyzeSession called: session_id=%s", request.session_id)

            insights = []
            recommendations = []

            # Basic statistical insights from session data
            if request.keys_tested > 0:
                insights.append(
                    f"Tested {request.keys_tested:,} keys in {request.elapsed:.1f}s"
                )
            if request.seeds_tested > 0:
                insights.append(f"Tested {request.seeds_tested:,} seeds")
            if request.speed > 0:
                insights.append(f"Speed: {request.speed:.0f} keys/sec")
            if request.hits > 0:
                insights.append(f"Found {request.hits} hit(s)")
            if request.mode:
                insights.append(f"Mode: {request.mode}")

            if not insights:
                insights.append("No session data provided")

            # Basic recommendations
            if request.speed > 0 and request.speed < 1000:
                recommendations.append(
                    "Consider using batch mode for higher throughput"
                )
            if request.elapsed > 3600:
                recommendations.append(
                    "Long session detected — consider checkpointing more frequently"
                )
            if request.hits == 0 and request.keys_tested > 1_000_000:
                recommendations.append(
                    "No hits after 1M+ keys — consider changing strategy or range"
                )

            if not recommendations:
                recommendations.append("Continue scanning with current parameters")

            return oracle_pb2.AnalysisResponse(
                insights=insights,
                recommendations=recommendations,
                adjustments={},
                xp_earned=0,
            )


def serve(port=None):
    """Start the gRPC server."""
    if port is None:
        port = int(os.environ.get("ORACLE_PORT", "50052"))

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    # Register Oracle service
    oracle_pb2_grpc.add_OracleServiceServicer_to_server(OracleServiceImpl(), server)

    # Register gRPC health checking service
    health_servicer = health.HealthServicer()
    health_pb2_grpc.add_HealthServicer_to_server(health_servicer, server)
    health_servicer.set(
        "nps.oracle.OracleService",
        health_pb2.HealthCheckResponse.SERVING,
    )

    server.add_insecure_port(f"[::]:{port}")
    server.start()
    logger.info("Oracle service v%s listening on port %d", _VERSION, port)

    # Start HTTP monitoring sidecar (graceful fallback)
    try:
        from devops.monitoring.http_server import start_http_server

        _oracle_impl = OracleServiceImpl()

        def _health_fn():
            """Reuse HealthCheck RPC logic for HTTP /health endpoint."""
            try:
                from engines.fc60 import self_test

                checks = {}
                results = self_test()
                passed = sum(1 for r in results if r[1])
                checks["fc60"] = f"{passed}/{len(results)} vectors"

                name_to_number("TEST")
                checks["numerology"] = "ok"

                read_sign("test")
                checks["oracle"] = "ok"

                get_current_quality()
                checks["timing"] = "ok"

                all_ok = all("error" not in v for v in checks.values())
                return {
                    "status": "healthy" if all_ok else "degraded",
                    "version": _VERSION,
                    "uptime_seconds": int(time.time() - _start_time),
                    "checks": checks,
                }
            except Exception as e:
                return {
                    "status": "degraded",
                    "version": _VERSION,
                    "uptime_seconds": int(time.time() - _start_time),
                    "error": str(e),
                }

        _metrics_fn = _metrics.get_snapshot if _metrics_available else lambda: {}
        http_port = int(os.environ.get("ORACLE_HTTP_PORT", "9090"))
        start_http_server(_health_fn, _metrics_fn, port=http_port)
    except ImportError:
        logger.debug("devops.monitoring not available, HTTP sidecar disabled")
    except Exception as e:
        logger.warning("Failed to start HTTP monitoring sidecar: %s", e)

    # Graceful shutdown
    def _shutdown(signum, frame):
        logger.info("Received signal %d, shutting down...", signum)
        health_servicer.set(
            "nps.oracle.OracleService",
            health_pb2.HealthCheckResponse.NOT_SERVING,
        )
        server.stop(grace=5)

    signal.signal(signal.SIGTERM, _shutdown)
    signal.signal(signal.SIGINT, _shutdown)

    server.wait_for_termination()


if __name__ == "__main__":
    serve()
