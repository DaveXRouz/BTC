"""Oracle Service — Engine Layer.

Computation engines are now provided by numerology_ai_framework via
framework_bridge. This __init__ re-exports the public API for backward
compatibility.  Oracle-specific engines (oracle.py, ai_interpreter.py,
translation_service.py, timing_advisor.py) remain in this package.
"""

# Core computation (via framework bridge) — explicit re-exports
from oracle_service.framework_bridge import token60 as token60
from oracle_service.framework_bridge import encode_fc60 as encode_fc60
from oracle_service.framework_bridge import numerology_reduce as numerology_reduce
from oracle_service.framework_bridge import life_path as life_path
from oracle_service.framework_bridge import name_to_number as name_to_number
from oracle_service.framework_bridge import personal_year as personal_year

# Oracle readings (function-based, not class-based)
from engines.oracle import read_sign as read_sign
from engines.oracle import read_name as read_name
from engines.oracle import question_sign as question_sign
from engines.oracle import daily_insight as daily_insight

# AI interpretation (T3-S3)
from engines.ai_interpreter import interpret_reading as interpret_reading
from engines.ai_interpreter import interpret_all_formats as interpret_all_formats
from engines.ai_interpreter import interpret_group as interpret_group
from engines.translation_service import translate as translate
from engines.translation_service import batch_translate as batch_translate
from engines.translation_service import detect_language as detect_language
