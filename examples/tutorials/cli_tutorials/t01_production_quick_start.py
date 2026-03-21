#!/usr/bin/env python3
"""
Role: Production quick-start tutorial — YAML logger, DI-style service, layered logs.
Used By:
 - Engineers following `examples/tutorials/README.md` onboarding tracks.
 - `examples/run_all_examples.py` smoke runner.
Depends On:
 - dataclasses
 - pathlib
 - hydra_logger
Notes:
 - Same story as `t01_production_quick_start.ipynb`: YAML → `create_sync_logger` → inject logger,
   log with `layer` / `context` / `extra`. Run from repo root so paths in YAML resolve.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

_TUTORIALS_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _TUTORIALS_ROOT not in sys.path:
    sys.path.insert(0, _TUTORIALS_ROOT)

from hydra_logger import create_sync_logger
from hydra_logger.config.loader import load_logging_config
from shared.cli_tutorial_footer import print_cli_tutorial_footer

CONFIG_REL = Path("examples/config/tutorial_t01_enterprise_layers.yaml")


@dataclass
class PaymentRequest:
    order_id: str
    user_id: str
    amount: float
    currency: str = "USD"


class PaymentService:
    def __init__(self, logger: Any) -> None:
        self.logger = logger

    def process(self, req: PaymentRequest) -> dict[str, Any]:
        self.logger.info(
            "payment request received",
            layer="app",
            context={"order_id": req.order_id, "user_id": req.user_id},
            extra={"amount": req.amount, "currency": req.currency},
        )
        if req.amount <= 0:
            self.logger.warning(
                "invalid payment amount",
                layer="audit",
                context={"order_id": req.order_id, "user_id": req.user_id},
                extra={"amount": req.amount},
            )
            raise ValueError("Amount must be > 0")
        if req.amount > 10000:
            self.logger.error(
                "payment exceeds policy threshold",
                layer="error",
                context={"order_id": req.order_id, "user_id": req.user_id},
                extra={"amount": req.amount, "threshold": 10000},
            )
            raise RuntimeError("Risk policy blocked this payment")
        self.logger.info(
            "payment approved",
            layer="app",
            context={"order_id": req.order_id},
            extra={"status": "approved"},
        )
        return {"ok": True, "order_id": req.order_id, "status": "approved"}


def main() -> None:
    # Presets under examples/config target notebook output (examples/logs/notebooks/); CLI keeps cli-tutorials.
    cfg = load_logging_config(CONFIG_REL, strict_unknown_fields=True)
    cfg = cfg.model_copy(update={"log_dir_name": "cli-tutorials"})
    with create_sync_logger(
        cfg,
        strict_unknown_fields=True,
        name="t01-tutorial",
    ) as logger:
        svc = PaymentService(logger)
        svc.process(PaymentRequest(order_id="ORD-1001", user_id="U-1", amount=99.5))
        # Demo: audit layer + warning, then error layer — exceptions stop the flow only here.
        try:
            svc.process(PaymentRequest(order_id="ORD-1002", user_id="U-2", amount=0))
        except ValueError:
            pass
        try:
            svc.process(PaymentRequest(order_id="ORD-1003", user_id="U-3", amount=15000))
        except RuntimeError:
            pass

    print_cli_tutorial_footer(
        code="T01",
        title="Production quick start (YAML + layered logger)",
        console="Hydra console lines from `app` and `error` layers; audit events are file-only.",
        artifacts=[
            "examples/logs/cli-tutorials/t01_app.jsonl",
            "examples/logs/cli-tutorials/t01_audit.log",
            "examples/logs/cli-tutorials/t01_error.jsonl",
        ],
        takeaway="Same story as the T01 notebook: YAML → create_sync_logger → layer/context/extra.",
        notebook_rel="examples/tutorials/notebooks/t01_production_quick_start.ipynb",
    )


if __name__ == "__main__":
    main()
