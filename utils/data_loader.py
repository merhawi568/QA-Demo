import json
from pathlib import Path
from typing import Dict, Any

ROOT = Path(__file__).resolve().parents[1]
MOCK = ROOT / "mock_data"

def load_ticket(ticket_id: str) -> Dict[str, Any]:
    p = MOCK / "trade_tickets" / f"{ticket_id}.json"
    if not p.exists():
        raise FileNotFoundError(f"Ticket not found: {p}")
    return json.loads(p.read_text())

def get_workhub_fee_mod(account_id: str) -> Dict[str, Any]:
    # tune to your TKT67890 effective_date (2025-10-01 in your mock)
    return {
        "account_id": account_id,
        "old_rate": 0.70,
        "new_rate": 0.65,
        "modified_timestamp": "2025-10-02T10:15:00",
        "modified_by": "ops_user_1",
    }

def get_feeapp_fees(account_id: str, scenario: str = "happy") -> Dict[str, Any]:
    # Use different data based on account ID for more realistic scenarios
    if account_id == "ACC67891":  # Failure ticket
        return {"approved_rate": 0.60, "approval_id": "APR-999", "approval_date": "2025-09-30", "approver": "mgr_b"}
    elif scenario == "fail":
        return {"approved_rate": 0.60, "approval_id": "APR-999", "approval_date": "2025-09-30", "approver": "mgr_b"}
    return {"approved_rate": 0.65, "approval_id": "APR-123", "approval_date": "2025-09-30", "approver": "mgr_a"}

def get_email_approval_exists(account_id: str) -> bool:
    return True
