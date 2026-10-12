#!/usr/bin/env python3
"""Seeded synthetic deal specs (answer key A). No real company/customer/employer data."""
from __future__ import annotations

import hashlib
import json
import random
from datetime import date, timedelta
from pathlib import Path

SEED = 20261012
N = 40
DEV_N = 12  # 12/28 split; first DEV_N after shuffle go to dev

DOC_TYPES = [
    "nda",
    "msa",
    "sow",
    "dpa",
    "security_questionnaire",
    "soc2",
]
HOLDERS = [
    "our_rep",
    "our_legal",
    "our_security",
    "cust_legal",
    "cust_procurement",
    "cust_security",
]
STATUSES = [
    "requested",
    "sent",
    "in_review",
    "redlines_with_us",
    "redlines_with_customer",
    "signed",
    "blocked",
]

# Slice tags for stratified coverage
SLICES = [
    "happy_path_signed",
    "msa_redlines_with_customer",
    "security_stall_cust",
    "legal_stall_our",
    "procurement_block",
    "multi_doc_mixed",
    "deadline_explicit",
    "deadline_implied",
    "soc2_expired_request",
    "nda_only_early",
]

FAKE_SELLERS = [
    ("Northline Analytics", "northline.test", "Jordan Hale", "jordan.hale"),
    ("Pinnacle Ops", "pinnacleops.test", "Casey Ng", "casey.ng"),
    ("Bright Harbor Software", "brightharbor.test", "Riley Santos", "riley.santos"),
    ("Cedar Peak Systems", "cedarpeak.test", "Avery Quinn", "avery.quinn"),
]
FAKE_BUYERS = [
    ("Meridian Retail Group", "meridian-retail.test", "Sam Ortiz", "sam.ortiz"),
    ("Lakeview Health Partners", "lakeviewhealth.test", "Taylor Brooks", "taylor.brooks"),
    ("Summit Freight Co", "summitfreight.test", "Morgan Lee", "morgan.lee"),
    ("Atlas Civic Tech", "atlascivic.test", "Jamie Patel", "jamie.patel"),
    ("Harbor Mutual Bank", "harbormutual.test", "Drew Kim", "drew.kim"),
    ("Polaris Manufacturing", "polarismfg.test", "Chris Alvarez", "chris.alvarez"),
]


def seeded_rng() -> random.Random:
    return random.Random(SEED)


def deal_id(i: int) -> str:
    return f"deal_{i:03d}"


def pick_docs(rng: random.Random, slice_name: str) -> list[str]:
    if slice_name == "nda_only_early":
        return ["nda"]
    if slice_name == "soc2_expired_request":
        return ["nda", "msa", "soc2"]
    if slice_name == "security_stall_cust":
        return ["nda", "msa", "security_questionnaire"]
    if slice_name == "procurement_block":
        return ["msa", "sow", "dpa"]
    base = ["nda", "msa"]
    extras = [d for d in DOC_TYPES if d not in base]
    k = rng.randint(1, 3)
    return base + rng.sample(extras, k)


def asof_for_doc(rng: random.Random, slice_name: str, doc: str, start: date) -> dict:
    # Default mid-funnel
    holder = rng.choice(HOLDERS)
    status = rng.choice(STATUSES)
    last_move = start + timedelta(days=rng.randint(0, 18))
    deadline = None

    if slice_name == "happy_path_signed":
        holder, status = "our_rep", "signed"
    elif slice_name == "msa_redlines_with_customer" and doc == "msa":
        holder, status = "cust_legal", "redlines_with_customer"
    elif slice_name == "security_stall_cust" and doc == "security_questionnaire":
        holder, status = "cust_security", "in_review"
    elif slice_name == "legal_stall_our" and doc in ("msa", "dpa"):
        holder, status = "our_legal", "redlines_with_us"
    elif slice_name == "procurement_block" and doc == "sow":
        holder, status = "cust_procurement", "blocked"
    elif slice_name == "soc2_expired_request" and doc == "soc2":
        holder, status = "our_security", "requested"
    elif slice_name == "nda_only_early" and doc == "nda":
        holder, status = "cust_legal", "in_review"

    if slice_name == "deadline_explicit":
        deadline = last_move + timedelta(days=rng.choice([3, 5, 7, 10]))
    elif slice_name == "deadline_implied" and rng.random() < 0.7:
        # Friday-after style: store ISO; renderer will phrase "by Friday"
        deadline = last_move + timedelta(days=(4 - last_move.weekday()) % 7 or 7)

    # Signed docs sit with our_rep
    if status == "signed":
        holder = "our_rep"

    events = []
    # Build a short event timeline ending at as-of
    cursor = start
    path = [
        ("our_rep", "requested"),
        ("our_legal", "sent") if doc in ("nda", "msa", "dpa", "sow") else ("our_security", "sent"),
        (holder, status),
    ]
    # Dedupe consecutive
    cleaned = []
    for h, s in path:
        if cleaned and cleaned[-1] == (h, s):
            continue
        cleaned.append((h, s))
    for h, s in cleaned:
        cursor = cursor + timedelta(days=rng.randint(0, 4))
        if cursor > last_move:
            cursor = last_move
        events.append(
            {
                "date": cursor.isoformat(),
                "holder": h,
                "status": s,
                "note": f"{doc} moved to {h} / {s}",
            }
        )
    if events:
        events[-1]["date"] = last_move.isoformat()
        events[-1]["holder"] = holder
        events[-1]["status"] = status

    return {
        "doc_type": doc,
        "holder": holder,
        "status": status,
        "last_movement_date": last_move.isoformat(),
        "deadline": deadline.isoformat() if deadline else None,
        "events": events,
    }


def main() -> None:
    rng = seeded_rng()
    out_dir = Path(__file__).resolve().parents[1] / "data" / "scenarios"
    out_dir.mkdir(parents=True, exist_ok=True)

    indices = list(range(1, N + 1))
    rng.shuffle(indices)
    split = {deal_id(i): ("dev" if rank < DEV_N else "test") for rank, i in enumerate(indices)}

    # Re-seed for generation so shuffle and content stay stable independently
    rng = seeded_rng()
    scenarios = []
    for i in range(1, N + 1):
        did = deal_id(i)
        slice_name = SLICES[(i - 1) % len(SLICES)]
        seller = FAKE_SELLERS[(i - 1) % len(FAKE_SELLERS)]
        buyer = FAKE_BUYERS[(i - 1) % len(FAKE_BUYERS)]
        start = date(2026, 8, 3) + timedelta(days=rng.randint(0, 50))
        docs = pick_docs(rng, slice_name)
        asof = [asof_for_doc(rng, slice_name, d, start) for d in docs]
        scenario = {
            "deal_id": did,
            "split": split[did],
            "slice": slice_name,
            "synthetic": True,
            "seller": {
                "company": seller[0],
                "domain": seller[1],
                "rep_name": seller[2],
                "rep_email": f"{seller[3]}@{seller[1]}",
            },
            "buyer": {
                "company": buyer[0],
                "domain": buyer[1],
                "champion_name": buyer[2],
                "champion_email": f"{buyer[3]}@{buyer[1]}",
            },
            "opportunity_name": f"{buyer[0]} - {seller[0]} FY26",
            "thread_start_date": start.isoformat(),
            "documents": asof,
            "noise_flags": {
                "cc_noise": rng.random() < 0.4,
                "scheduling_aside": rng.random() < 0.35,
                "attachment_mentioned_not_attached": rng.random() < 0.2,
                "forwarded_snippet": rng.random() < 0.25,
            },
        }
        scenarios.append(scenario)
        (out_dir / f"{did}.json").write_text(
            json.dumps(scenario, indent=2) + "\n", encoding="utf-8"
        )

    # Manifest of scenario hashes (not final thread manifest)
    lines = []
    for s in sorted(scenarios, key=lambda x: x["deal_id"]):
        raw = (out_dir / f"{s['deal_id']}.json").read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        lines.append(f"{digest}  scenarios/{s['deal_id']}.json")
    man = Path(__file__).resolve().parents[1] / "data" / "SCENARIOS.sha256"
    man.write_text("\n".join(lines) + "\n", encoding="utf-8")

    split_counts = {"dev": 0, "test": 0}
    for s in scenarios:
        split_counts[s["split"]] += 1
    print(f"Wrote {N} scenarios to {out_dir}")
    print(f"Split: {split_counts} (target {DEV_N}/{N - DEV_N})")
    print(f"Manifest: {man}")


if __name__ == "__main__":
    main()
