"""Entry point for the frozen desktop build."""

from __future__ import annotations

import sys

from engine.sandbox.constants import SANDBOX_WORKER_FLAG


def main() -> int:
    if len(sys.argv) >= 3 and sys.argv[1] == SANDBOX_WORKER_FLAG:
        from engine.sandbox.worker_loop import main as worker_main

        sys.argv = [sys.argv[0], sys.argv[2]]
        return worker_main()

    from engine.paths import default_results_dir, ensure_user_data_tree
    from ui.app import App

    ensure_user_data_tree()
    App(results_dir=default_results_dir()).run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
