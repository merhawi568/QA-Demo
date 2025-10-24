from typing import Dict, Any, List

class DecisionAgent:
    def decide(self, ticket: Dict[str, Any], agg: Dict[str, Any]) -> Dict[str, Any]:
        decision = "PASS" if agg["failed"] == 0 else "FAIL"
        return {"ticket_id": ticket["ticket_id"], "decision": decision, "summary": agg}
