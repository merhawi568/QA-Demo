# Decides: Should we raise an exception?
def decide(aggregated_results, trade_metadata):
    # Uses LLM to reason:
    # - Are failures critical?
    # - What's the risk level?
    # - Does regulation require escalation?
    
    return {
        "raise_exception": True,
        "severity": "HIGH",
        "reason": "Pre-trade consent not obtained - regulatory violation",
        "recommended_action": "Block trade settlement"
    }
