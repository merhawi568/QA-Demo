# SQLite database storing:
- Workflow state
- Each agent's input/output
- Decision history
- Audit trail

# Queryable for debugging and auditing
```

## HITL Communication

Using **Rich** library for beautiful console output:
```
╭─────────────────────────────────────────────────────────╮
│ 🤖 QA VALIDATION WORKFLOW STARTED                       │
│ Trade: TKT67890 | Type: SP | Platform: Madrid          │
╰─────────────────────────────────────────────────────────╯

[14:22:01] 🎯 Orchestration Agent
           ├─ Reading trade ticket metadata...
           ├─ Trade Type: SP (Structured Product)
           ├─ Required checks: consent, account_match, attestation
           └─ Creating execution plan...

[14:22:02] 📊 Data Request Agent
           ├─ Need: account_number from CRM for ACC12345
           ├─ Converting to API specification...
           ├─ Loading from mock_data/crm_accounts/ACC12345.json
           └─ ✓ Data retrieved successfully

[14:22:03] ⚖️  Compare Tool: Account Number Match
           ├─ Comparing: CRM.account_number vs Ticket.account_number
           ├─ Left:  'ACC12345'
           ├─ Right: 'ACC-12345'
           ├─ After normalization: MATCH
           └─ ✅ PASSED: Account numbers match

[14:22:04] 📅 Date Compare Tool: Consent Timing
           ├─ Comparing: consent_time vs execution_time
           ├─ Consent: 2025-10-23 14:35:00
           ├─ Trade:   2025-10-23 14:30:00
           └─ ❌ FAILED: Consent obtained AFTER trade execution

[14:22:05] 📊 Result Aggregator
           ├─ Total checks: 5
           ├─ Passed: 4 | Failed: 1
           └─ Overall: FAILED

[14:22:06] 🧠 Decision Agent
           ├─ Analyzing failure severity...
           ├─ Failed check: consent_timing (CRITICAL)
           ├─ Regulation: MiFID II requires pre-trade consent
           └─ Decision: RAISE EXCEPTION (Severity: HIGH)

[14:22:07] 📧 Exception Agent
           ├─ Drafting exception email...
           ├─ To: compliance-team@company.com
           ├─ Subject: Trade TKT67890 - Compliance Exception
           └─ ✓ Email drafted (saved to exceptions/TKT67890_email.txt)

╭─────────────────────────────────────────────────────────╮
│ ❌ WORKFLOW COMPLETED: EXCEPTION RAISED                 │
│ Duration: 5.2s | Checks: 5 | Failed: 1                 │
╰─────────────────────────────────────────────────────────╯
