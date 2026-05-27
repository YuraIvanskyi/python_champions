"""Entry point for the frozen desktop build."""

from __future__ import annotations

import sys

from engine.paths import default_results_dir
from ui.app import App


def main() -> int:
    App(results_dir=default_results_dir()).run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
