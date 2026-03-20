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

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from hydra_logger import create_sync_logger

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
    with create_sync_logger(
        config_path=CONFIG_REL,
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


if __name__ == "__main__":
    main()
