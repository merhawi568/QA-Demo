# Responsibilities:
- Read TT metadata (trade type, platform, account)
- Determine which validations needed based on trade type
- Decide order of agent execution
- Handle HITL communication
- Coordinate all other agents

# Key Decisions:
- "SP trade → need consent validation"
- "Madrid platform → need account number match"
- "If consent check fails → escalate immediately"
