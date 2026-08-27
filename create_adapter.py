from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
FRAMEWORK = ROOT / "data" / "framework"

sys.path.insert(0, str(FRAMEWORK))

from scripts.create_adapter import main  # noqa: E402


if __name__ == "__main__":
    main()
