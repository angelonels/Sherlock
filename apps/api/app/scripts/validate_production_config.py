from __future__ import annotations

import os

from app.core.config import get_settings
from app.core.production_config import production_config_issues


def main() -> None:
    if os.getenv("ALLOW_INSECURE_PRODUCTION_CONFIG", "").lower() == "true":
        print("WARNING: insecure production configuration accepted for local smoke testing only.")
        return

    issues = production_config_issues(get_settings(), os.environ)
    if issues:
        formatted_issues = "\n- ".join(issues)
        raise SystemExit(f"Invalid production configuration:\n- {formatted_issues}")

    print("Production configuration preflight passed.")


if __name__ == "__main__":
    main()
