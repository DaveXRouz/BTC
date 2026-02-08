"""V4 Oracle Service — Logic Layer.

Intelligence modules for smart scanning decisions.
All V3 logic files copied as-is. These provide strategy, timing,
pattern analysis, scoring, and range optimization.
"""

from oracle_service.logic.strategy_engine import StrategyEngine
from oracle_service.logic.pattern_tracker import PatternTracker
from oracle_service.logic.key_scorer import KeyScorer
from oracle_service.logic.history_manager import HistoryManager
from oracle_service.logic.timing_advisor import (
    get_current_quality,
    get_optimal_hours_today,
    get_cosmic_alignment,
)
from oracle_service.logic.range_optimizer import RangeOptimizer
