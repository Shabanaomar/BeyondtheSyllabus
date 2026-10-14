"""Entry point for running the planning engine as a Vercel service (see vercel.json).

The engine is internal: it has no public route, and only the website reaches it, through the
ENGINE_URL service binding. The path insert makes the import work whether or not the build
installs this project as a package.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "engine" / "src"))

from bts_engine.api import app

__all__ = ["app"]
