from typing import Dict, Any
from utils import data_loader

class DataRequestAgent:
    """
    Mock 'data extraction/API agent' that pulls from mock_data via data_loader.
    Swap these functions to hit real APIs later.
    """
    def __init__(self):
        pass

    def fetch_workhub_fee_mod(self, account_id: str) -> Dict[str, Any]:
        return data_loader.get_workhub_fee_mod(account_id)

    def fetch_feeapp_fees(self, account_id: str, scenario: str = "happy") -> Dict[str, Any]:
        return data_loader.get_feeapp_fees(account_id, scenario=scenario)

    def email_approval_exists(self, account_id: str) -> bool:
        return data_loader.get_email_approval_exists(account_id)
