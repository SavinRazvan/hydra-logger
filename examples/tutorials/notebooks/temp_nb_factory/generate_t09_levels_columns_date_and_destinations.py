#!/usr/bin/env python3
"""
Role: Regenerate t09_levels_columns_date_and_destinations.ipynb only.
Used By:
 - Maintainers iterating on this notebook template.
Depends On:
 - factory_import_setup
 - nb_factory_core
Notes:
 - Run: ``python3 examples/tutorials/notebooks/temp_nb_factory/generate_t09_levels_columns_date_and_destinations.py`` (repo root).
"""

from __future__ import annotations

import factory_import_setup  # noqa: F401 — side effect: sys.path

from nb_factory_core import (
    NOTEBOOKS_DIR,
    ROOT,
    build_tutorial_notebook,
    spec_by_filename,
    write_notebook_json,
)

NOTEBOOK_FILENAME = "t09_levels_columns_date_and_destinations.ipynb"


def main() -> None:
    spec = spec_by_filename(NOTEBOOK_FILENAME)
    notebook = build_tutorial_notebook(spec)
    out = NOTEBOOKS_DIR / NOTEBOOK_FILENAME
    write_notebook_json(notebook, out)
    print(f"Wrote {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
