"""NPS V4 Oracle Service.

Shim: V3 engines use `from engines.xxx import ...`. By adding this package's
directory to sys.path, those imports resolve to `oracle_service/engines/xxx`
without touching the 30+ copied V3 files.
"""

import sys
from pathlib import Path

# Allow V3-style `from engines.xxx` imports to resolve
_pkg_dir = str(Path(__file__).parent)
if _pkg_dir not in sys.path:
    sys.path.insert(0, _pkg_dir)
