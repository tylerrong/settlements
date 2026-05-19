from __future__ import annotations
from datetime import datetime, timezone
from typing import Optional
from db.models import get_conn


def upsert_settlement(data: dict) -> tuple[bool, int]:
    """Insert or update a settlement. Returns (is_new, row_id)."""
    now = datetime.now(timezone.utc).isoformat()
    data.setdefault("date_discovered", now)
    data["last_checked"] = now

    fields = [
        "title", "company", "defendant", "case_name", "case_number",
        "category", "eligibility_summary", "state_scope", "proof_required",
        "claim_required", "claim_deadline", "exclusion_deadline",
        "objection_deadline", "fairness_hearing_date", "estimated_payout",
        "max_payout", "settlement_fund", "claim_form_url", "official_website_url",
        "documents_url", "administrator", "source_url", "date_discovered",
        "last_checked", "status", "confidence_score", "raw_text",
    ]
    row = {f: data.get(f) for f in fields}

    conn = get_conn()
    existing = conn.execute(
        "SELECT id FROM settlements WHERE title = ? AND source_url = ?",
        (row["title"], row["source_url"]),
    ).fetchone()

    if existing:
        set_clause = ", ".join(f"{f} = ?" for f in fields if f not in ("title", "source_url", "date_discovered"))
        vals = [row[f] for f in fields if f not in ("title", "source_url", "date_discovered")]
        conn.execute(
            f"UPDATE settlements SET {set_clause} WHERE id = ?",
            vals + [existing["id"]],
        )
        conn.commit()
        conn.close()
        return False, existing["id"]
    else:
        placeholders = ", ".join("?" * len(fields))
        cols = ", ".join(fields)
        conn.execute(
            f"INSERT INTO settlements ({cols}) VALUES ({placeholders})",
            [row[f] for f in fields],
        )
        conn.commit()
        row_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.close()
        return True, row_id


def get_settlement(row_id: int) -> dict | None:
    conn = get_conn()
    row = conn.execute("SELECT * FROM settlements WHERE id = ?", (row_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def list_settlements(
    status: str | None = None,
    category: str | None = None,
    proof_required: str | None = None,
    days_until_deadline: int | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[dict]:
    conn = get_conn()
    where = []
    params = []

    if status:
        where.append("status = ?")
        params.append(status)
    if category:
        where.append("category = ?")
        params.append(category)
    if proof_required:
        where.append("LOWER(proof_required) = ?")
        params.append(proof_required.lower())
    if days_until_deadline is not None:
        where.append(
            "claim_deadline IS NOT NULL AND "
            "julianday(claim_deadline) - julianday('now') BETWEEN 0 AND ?"
        )
        params.append(days_until_deadline)

    sql = "SELECT * FROM settlements"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY date_discovered DESC LIMIT ? OFFSET ?"
    params += [limit, offset]

    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def log_crawl(source_url: str, settlements_found: int, error: str | None = None):
    conn = get_conn()
    conn.execute(
        "INSERT INTO crawl_log (source_url, crawled_at, settlements_found, error) VALUES (?, ?, ?, ?)",
        (source_url, datetime.now(timezone.utc).isoformat(), settlements_found, error),
    )
    conn.commit()
    conn.close()


def mark_expired():
    """Set status=expired for settlements whose claim_deadline has passed."""
    conn = get_conn()
    conn.execute(
        """UPDATE settlements SET status = 'expired'
           WHERE claim_deadline IS NOT NULL
           AND claim_deadline < date('now')
           AND status NOT IN ('expired', 'payment_pending')"""
    )
    conn.commit()
    conn.close()


def mark_closing_soon(days: int = 7):
    """Set status=closing_soon for settlements with deadline within N days."""
    conn = get_conn()
    conn.execute(
        """UPDATE settlements SET status = 'closing_soon'
           WHERE claim_deadline IS NOT NULL
           AND julianday(claim_deadline) - julianday('now') BETWEEN 0 AND ?
           AND status = 'open'""",
        (days,),
    )
    conn.commit()
    conn.close()
