# Labeling guide (synthetic deal-doc threads)

100% synthetic. No real companies, customers, employers, or personal data.

## Enums

### doc_type (exactly one per document record)
- `nda`
- `msa`
- `sow`
- `dpa`
- `security_questionnaire`
- `soc2`

### holder (who currently has the ball)
- `our_rep`
- `our_legal`
- `our_security`
- `cust_legal`
- `cust_procurement`
- `cust_security`

### status
- `not_started`
- `requested`
- `sent`
- `in_review`
- `redlines_with_us`
- `redlines_with_customer`
- `signed`
- `blocked`

## Date rules
- **last_movement_date**: date of the last message that changed that document's state (not the last message in the thread).
- **deadline**: only if explicitly stated or clearly implied (e.g. "by Friday" resolved from that message's send date). Otherwise `null`.

## Evidence
- `evidence_quote` must be a verbatim substring of a message body in the thread.
- If you cannot quote evidence, set `needs_review` true and lower confidence.

## One record per document type per deal
If the same doc type appears multiple times (e.g. MSA redline v2), keep **one** record with the **latest** holder/status after the full thread.
