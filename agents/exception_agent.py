from typing import Dict, Any

class ExceptionAgent:
    def build_email(self, ticket: Dict[str, Any], failed_checks) -> Dict[str, Any]:
        body_lines = [
            f"Ticket: {ticket['ticket_id']}",
            f"Intent: {ticket.get('intent','')}",
            "",
            "The following checks failed:"
        ]
        for c in failed_checks:
            body_lines.append(f"- {c['id']}: {c['reason']}")
        return {
            "to": "controls-qa-exceptions@firm.com",
            "subject": f"[QA-EXCEPTION] {ticket['ticket_id']} ({ticket.get('intent','')})",
            "body": "\n".join(body_lines)
        }
