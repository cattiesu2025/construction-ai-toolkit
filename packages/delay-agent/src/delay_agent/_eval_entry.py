"""Entry point that bridges the evals/ directory into the delay-agent package."""
import sys
from pathlib import Path
import delay_agent._pathsetup  # noqa: F401 — ensures workspace packages are importable


def main() -> None:
    evals_dir = Path(__file__).parents[4] / "evals"
    sys.path.insert(0, str(evals_dir.parent))
    from evals.run_eval import run_eval
    max_n = int(sys.argv[1]) if len(sys.argv) > 1 else None
    run_eval(max_cases=max_n)


if __name__ == "__main__":
    main()
