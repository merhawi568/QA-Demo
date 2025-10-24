from typing import TypedDict, List, Any

class Ticket(TypedDict):
    ticket_id: str
    intent: str
    account_id: str
    effective_date: str

class CheckResult(TypedDict):
    id: str
    passed: bool
    reason: str

class QAReport(TypedDict):
    ticket: Ticket
    checks: List[CheckResult]
    decision: Any

