"""V4 Oracle Service — Engine Layer.

All V3 engines copied as-is for Phase 2 Oracle service.
Pure computation modules (fc60, numerology, math_analysis, scoring) are
used directly. Operational modules (logger, health, config, etc.) will
be adapted to V4 patterns (environment variables, gRPC, PostgreSQL)
during later phases.
"""

# Core computation engines (V3 portable, no adaptation needed)
from engines.fc60 import (
    token60,
    encode_fc60,
    format_full_output,
    parse_input,
)
from engines.numerology import (
    life_path,
    name_to_number,
    numerology_reduce,
    personal_year,
)
from engines.math_analysis import math_profile, entropy
from engines.scoring import hybrid_score, score_batch

# Oracle readings (function-based, not class-based)
from engines.oracle import read_sign, read_name, question_sign, daily_insight

# AI interpretation (T3-S3)
from engines.ai_interpreter import (
    interpret_reading,
    interpret_all_formats,
    interpret_group,
)
from engines.translation_service import translate, batch_translate, detect_language
