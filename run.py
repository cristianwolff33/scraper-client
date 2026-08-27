from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
FRAMEWORK = ROOT / "data" / "framework"

sys.path.insert(0, str(FRAMEWORK))

from main import main  # noqa: E402


if __name__ == "__main__":
    exit_code = main()
    if exit_code == 0:
        from image_links import add_public_image_links

        add_public_image_links()
    raise SystemExit(exit_code)
