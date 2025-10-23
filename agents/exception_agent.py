# Drafts email for exception
def draft_exception_email(decision, results, metadata):
    # Uses LLM to write professional email
    
    return {
        "to": "compliance-team@company.com",
        "subject": "Trade TKT67890 - Compliance Exception",
        "body": """
        URGENT: Trade Compliance Issue
        
        Trade ID: TKT67890
        Issue: Pre-trade consent not obtained
        
        Details:
        - Consent call at 14:35
        - Trade executed at 14:30
        - Violation: MiFID II pre-trade consent requirement
        
        Evidence:
        [Attached findings]
        
        Recommended Action: Block settlement pending review
        """
    }
