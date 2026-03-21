"""
Role: Orchestrator — regenerate all tutorial notebooks from shared factory core.
Used By:
 - Bulk refresh after ``nb_factory_core`` / ``scenarios`` changes.
Depends On:
 - factory_import_setup
 - nb_factory_core
Notes:
 - **Per-notebook**: run ``generate_<stem>.py`` in this directory for less friction.
 - This file stays until explicitly retired (see project workflow).
"""

from __future__ import annotations

import factory_import_setup  # noqa: F401 — import for side effect (sys.path)
from nb_factory_core import (
    NOTEBOOKS_DIR,
    ROOT,
    TUTORIAL_SPECS,
    build_tutorial_notebook,
    write_notebook_json,
)


def main() -> None:
    NOTEBOOKS_DIR.mkdir(parents=True, exist_ok=True)
    for spec in TUTORIAL_SPECS:
        notebook = build_tutorial_notebook(spec)
        output_path = NOTEBOOKS_DIR / spec["filename"]
        write_notebook_json(notebook, output_path)
        print(f"Wrote {output_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
