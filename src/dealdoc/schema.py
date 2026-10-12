"""Pydantic models for deal-document extraction (no defaults on labeled fields)."""
from __future__ import annotations

from datetime import date
from typing import Literal, Optional

from pydantic import BaseModel, Field

DocType = Literal[
    "nda",
    "msa",
    "sow",
    "dpa",
    "security_questionnaire",
    "soc2",
]
Holder = Literal[
    "our_rep",
    "our_legal",
    "our_security",
    "cust_legal",
    "cust_procurement",
    "cust_security",
]
Status = Literal[
    "not_started",
    "requested",
    "sent",
    "in_review",
    "redlines_with_us",
    "redlines_with_customer",
    "signed",
    "blocked",
]


class DocRecord(BaseModel):
    doc_type: DocType
    holder: Holder
    status: Status
    last_movement_date: date
    deadline: Optional[date]
    confidence: float = Field(ge=0.0, le=1.0)
    evidence_quote: str
    needs_review: bool


class DealSummary(BaseModel):
    deal_id: str
    ball_summary: str
    documents: list[DocRecord]
