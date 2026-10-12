#!/usr/bin/env python3
"""Deterministic template renderer for synthetic threads (answer-key A evidence).

Uses templates only (no LLM) so Day 1 can start without API keys.
A later LLM pass can rewrite tone; keep this as the ground-truth-aligned baseline.
"""
from __future__ import annotations

import json
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCEN = ROOT / "data" / "scenarios"


def parse_d(s: str) -> date:
    return date.fromisoformat(s)


def holder_phrase(holder: str) -> str:
    return {
        "our_rep": "our account team",
        "our_legal": "our legal team",
        "our_security": "our security / trust team",
        "cust_legal": "your legal team",
        "cust_procurement": "your procurement team",
        "cust_security": "your security team",
    }[holder]


def status_line(doc: str, holder: str, status: str, deadline: str | None) -> str:
    nice = doc.replace("_", " ")
    base = {
        "requested": f"Could you please share the {nice} when you have a chance?",
        "sent": f"I've sent over the {nice} for review.",
        "in_review": f"The {nice} is currently with {holder_phrase(holder)} for review.",
        "redlines_with_us": f"We have redlines on the {nice} back with {holder_phrase(holder)}.",
        "redlines_with_customer": f"Redlines on the {nice} are with {holder_phrase(holder)}.",
        "signed": f"The {nice} is fully signed and complete.",
        "blocked": f"The {nice} is blocked pending {holder_phrase(holder)}.",
        "not_started": f"We have not started the {nice} yet.",
    }[status]
    if deadline:
        base += f" Please aim to finish by {deadline}."
    return base


def render_one(scenario: dict) -> dict:
    seller = scenario["seller"]
    buyer = scenario["buyer"]
    start = parse_d(scenario["thread_start_date"])
    messages = []
    mid = 0

    # Kickoff
    mid += 1
    messages.append(
        {
            "message_id": f"{scenario['deal_id']}_m{mid:02d}",
            "date": start.isoformat(),
            "from": f"{seller['rep_name']} <{seller['rep_email']}>",
            "to": [f"{buyer['champion_name']} <{buyer['champion_email']}>"],
            "subject": f"{scenario['opportunity_name']} - next steps on paperwork",
            "body": (
                f"Hi {buyer['champion_name'].split()[0]},\n\n"
                f"Great call today on {buyer['company']} evaluating {seller['company']}. "
                f"I'll start lining up the usual deal documents on our side.\n\n"
                f"Thanks,\n{seller['rep_name']}"
            ),
        }
    )

    if scenario["noise_flags"].get("scheduling_aside"):
        mid += 1
        messages.append(
            {
                "message_id": f"{scenario['deal_id']}_m{mid:02d}",
                "date": (start + timedelta(days=1)).isoformat(),
                "from": f"{buyer['champion_name']} <{buyer['champion_email']}>",
                "to": [f"{seller['rep_name']} <{seller['rep_email']}>"],
                "subject": f"Re: {scenario['opportunity_name']} - next steps on paperwork",
                "body": (
                    f"Hi {seller['rep_name'].split()[0]},\n\n"
                    "Can we move Thursday's working session to 2pm ET? "
                    "No doc updates from me yet.\n\n"
                    f"{buyer['champion_name']}"
                ),
            }
        )

    for doc in scenario["documents"]:
        for ev in doc["events"]:
            mid += 1
            d = parse_d(ev["date"])
            line = status_line(doc["doc_type"], ev["holder"], ev["status"], None)
            # Final event may carry deadline wording
            if ev is doc["events"][-1] and doc.get("deadline"):
                line = status_line(
                    doc["doc_type"], doc["holder"], doc["status"], doc["deadline"]
                )
            our_side = ev["holder"].startswith("our_") or ev["holder"] == "our_rep"
            if our_side:
                frm = f"{seller['rep_name']} <{seller['rep_email']}>"
                to = [f"{buyer['champion_name']} <{buyer['champion_email']}>"]
                greet = buyer["champion_name"].split()[0]
                sign = seller["rep_name"]
            else:
                frm = f"{buyer['champion_name']} <{buyer['champion_email']}>"
                to = [f"{seller['rep_name']} <{seller['rep_email']}>"]
                greet = seller["rep_name"].split()[0]
                sign = buyer["champion_name"]
            body = f"Hi {greet},\n\n{line}\n\n{sign}"
            messages.append(
                {
                    "message_id": f"{scenario['deal_id']}_m{mid:02d}",
                    "date": d.isoformat(),
                    "from": frm,
                    "to": to,
                    "subject": f"Re: {scenario['opportunity_name']} - next steps on paperwork",
                    "body": body,
                }
            )

    # Gold labels = as-of documents (answer key A mirrored into labels)
    labels = []
    for doc in scenario["documents"]:
        # Pick evidence from last event message body line
        evidence = status_line(
            doc["doc_type"], doc["holder"], doc["status"], doc.get("deadline")
        )
        labels.append(
            {
                "doc_type": doc["doc_type"],
                "holder": doc["holder"],
                "status": doc["status"],
                "last_movement_date": doc["last_movement_date"],
                "deadline": doc["deadline"],
                "confidence": 1.0,
                "evidence_quote": evidence,
                "needs_review": False,
                "source": "answer_key_A",
            }
        )

    return {
        "deal_id": scenario["deal_id"],
        "split": scenario["split"],
        "slice": scenario["slice"],
        "synthetic": True,
        "subject": f"{scenario['opportunity_name']} - next steps on paperwork",
        "messages": messages,
        "attachments": [],
        "gold_labels_A": labels,
    }


def main() -> None:
    for path in sorted(SCEN.glob("deal_*.json")):
        scenario = json.loads(path.read_text(encoding="utf-8"))
        thread = render_one(scenario)
        split = thread["split"]
        out = ROOT / "data" / "threads" / split / f"{thread['deal_id']}.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(thread, indent=2) + "\n", encoding="utf-8")
        lab = ROOT / "data" / "labels" / split / f"{thread['deal_id']}.json"
        lab.parent.mkdir(parents=True, exist_ok=True)
        lab.write_text(
            json.dumps(
                {
                    "deal_id": thread["deal_id"],
                    "split": split,
                    "labels": thread["gold_labels_A"],
                    "note": "Answer key A from scenario spec. Blind hand-label B still required.",
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
    print("Rendered threads + labels_A for all scenarios")


if __name__ == "__main__":
    main()
