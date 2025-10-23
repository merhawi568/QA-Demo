# Collects all tool results
{
  "total_checks": 5,
  "passed": 4,
  "failed": 1,
  "results": [
    {"check": "account_match", "passed": True, "reason": "..."},
    {"check": "consent_timing", "passed": False, "reason": "Consent after trade"}
  ],
  "overall_status": "FAIL",
  "critical_failures": ["consent_timing"]
}
