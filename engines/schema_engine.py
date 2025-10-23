# Stores:
{
  "CRM_API": {
    "endpoint": "/api/v1/accounts/{account_id}",
    "fields": ["account_number", "account_name", "email", "status"],
    "auth_type": "bearer_token",
    "base_url": "https://crm.company.com"
  },
  "TradeTicket_API": {
    "endpoint": "/api/v1/tickets/{ticket_id}",
    "fields": ["account_id", "trade_type", "execution_time", "platform"]
  }
}

# Tables metadata, field types, relationships
