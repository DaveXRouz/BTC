"""NPS Oracle Service.

Path shims:
1. oracle_service/ directory on sys.path — allows `from engines.xxx` imports
2. Project root on sys.path — allows `from numerology_ai_framework.xxx` imports
"""

import sys
from pathlib import Path

# Allow legacy-style `from engines.xxx` imports to resolve
_pkg_dir = str(Path(__file__).parent)
if _pkg_dir not in sys.path:
    sys.path.insert(0, _pkg_dir)

# Allow `from numerology_ai_framework.xxx` imports
_project_root = str(Path(__file__).resolve().parents[3])  # NPS/
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)
