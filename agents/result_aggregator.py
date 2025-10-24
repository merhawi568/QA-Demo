from typing import List, Dict, Any

class ResultAggregator:
    def aggregate(self, checks: List[Dict[str, Any]]) -> Dict[str, Any]:
        passed = sum(1 for c in checks if c["passed"])
        failed = sum(1 for c in checks if not c["passed"])
        return {
            "total": len(checks),
            "passed": passed,
            "failed": failed,
            "needs_review": 0,
            "failed_checks": [c for c in checks if not c["passed"]],
        }
