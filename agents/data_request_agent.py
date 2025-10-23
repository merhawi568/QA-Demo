# Responsibilities:
- Receives: "I need account_number from CRM for ACC12345"
- Converts to: API call specification
- Routes to data loader (folder-based for demo)
- Returns structured data

# Demo Mode:
- Reads from mock_data/crm_accounts/ACC12345.json

# Real Mode (commented code):
- Makes actual API call to CRM
- Handles auth, retries, errors
