"""
Schema definitions for the LangChain-based QA pipeline.
These schemas define ticket types, data extraction requirements, API configurations, and test DAGs.
"""

from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from enum import Enum

class TicketType(str, Enum):
    """Supported ticket types for categorization"""
    FEE_MODIFICATION = "fee_modification"
    ACCOUNT_OPENING = "account_opening"
    DOCUMENT_VERIFICATION = "document_verification"
    COMPLIANCE_CHECK = "compliance_check"
    TRADE_VALIDATION = "trade_validation"

class DataSource(str, Enum):
    """Available data sources"""
    CONNECT = "connect"
    BROKERAGE_BLOTTER = "brokerage_blotter"
    DOC_MANAGER = "doc_manager"
    VOICE_LOGS = "voice_logs"
    ACES = "aces"
    SCRIBE = "scribe"

class TestType(str, Enum):
    """Available test types"""
    COMPARE = "compare"
    VALIDATE_PRESENCE = "validate_presence"
    DATE_RANGE_CHECK = "date_range_check"
    EQUALITY_CHECK = "equality_check"
    ROUNDED_EQUALITY = "rounded_equality"

class OperationType(str, Enum):
    """Operations for generic tools"""
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    IN_RANGE = "in_range"
    CONTAINS = "contains"
    EXISTS = "exists"
    NOT_EXISTS = "not_exists"
    ROUNDED_EQUALITY = "rounded_equality"

class TicketTypeSchema(BaseModel):
    """Schema for ticket type categorization"""
    ticket_type: TicketType
    description: str
    metadata_patterns: Dict[str, Any] = Field(description="Patterns to match in ticket metadata")
    required_fields: List[str] = Field(description="Required fields in ticket for this type")
    confidence_threshold: float = Field(default=0.8, description="Minimum confidence for categorization")

class DataExtractionSchema(BaseModel):
    """Schema defining what data to extract for each test type"""
    test_type: TicketType
    required_data_points: List[Dict[str, Any]] = Field(description="Data points needed for this test type")
    data_sources: List[DataSource] = Field(description="Sources to extract data from")
    validation_rules: Optional[Dict[str, Any]] = Field(default=None, description="Validation rules for extracted data")

class APIConfigSchema(BaseModel):
    """API configuration for data sources"""
    source: DataSource
    base_url: str
    endpoints: Dict[str, str] = Field(description="Endpoint paths for different operations")
    headers: Dict[str, str] = Field(default_factory=dict)
    authentication: Optional[Dict[str, Any]] = Field(default=None)
    rate_limits: Optional[Dict[str, int]] = Field(default=None)
    timeout: int = Field(default=30)

class TestToolConfig(BaseModel):
    """Configuration for generic test tools"""
    tool_name: str
    tool_type: TestType
    operation: OperationType
    parameters: Dict[str, Any] = Field(description="Tool-specific parameters")
    success_criteria: Dict[str, Any] = Field(description="Criteria for test success")
    error_handling: Optional[Dict[str, Any]] = Field(default=None)

class TestDAGNode(BaseModel):
    """Node in the test execution DAG"""
    test_id: str
    tool_config: TestToolConfig
    dependencies: List[str] = Field(default_factory=list, description="Test IDs this test depends on")
    parallel_execution: bool = Field(default=False, description="Can run in parallel with other tests")
    retry_count: int = Field(default=0, description="Number of retries on failure")
    timeout: int = Field(default=60, description="Test timeout in seconds")

class TestDAGSchema(BaseModel):
    """Complete test DAG for a ticket type"""
    ticket_type: TicketType
    dag_id: str
    description: str
    nodes: List[TestDAGNode] = Field(description="All test nodes in the DAG")
    execution_strategy: str = Field(default="sequential", description="Overall execution strategy")
    max_parallel_tests: int = Field(default=1, description="Maximum parallel test execution")

class SessionMemorySchema(BaseModel):
    """Schema for session memory storage"""
    session_id: str
    ticket_id: str
    ticket_type: Optional[TicketType] = None
    extracted_data: Dict[str, Any] = Field(default_factory=dict)
    test_results: Dict[str, Any] = Field(default_factory=dict)
    execution_status: str = Field(default="pending")
    created_at: str
    updated_at: str

# Default configurations
DEFAULT_TICKET_TYPE_SCHEMAS = {
    TicketType.FEE_MODIFICATION: TicketTypeSchema(
        ticket_type=TicketType.FEE_MODIFICATION,
        description="Fee modification requests",
        metadata_patterns={
            "trade_type": ["fee_modification", "rate_change"],
            "platform": ["workhub", "feeapp"]
        },
        required_fields=["ticket_id", "account_id", "trade_type", "platform"],
        confidence_threshold=0.8
    ),
    TicketType.ACCOUNT_OPENING: TicketTypeSchema(
        ticket_type=TicketType.ACCOUNT_OPENING,
        description="New account opening requests",
        metadata_patterns={
            "trade_type": ["account_opening", "new_account"],
            "platform": ["crm", "workhub"]
        },
        required_fields=["ticket_id", "account_id", "client_name", "trade_type"],
        confidence_threshold=0.8
    )
}

DEFAULT_DATA_EXTRACTION_SCHEMAS = {
    TicketType.FEE_MODIFICATION: DataExtractionSchema(
        test_type=TicketType.FEE_MODIFICATION,
        required_data_points=[
            {
                "name": "connect_data", 
                "source": DataSource.CONNECT, 
                "fields": [
                    "order_id", "trade_inquiry", "order_restrictions", 
                    "profile_canvas", "global_fee_transparency", "fee_instruct_report",
                    "product_type", "transaction_type", "execution_timestamps", "order_time"
                ]
            },
            {
                "name": "brokerage_blotter_data", 
                "source": DataSource.BROKERAGE_BLOTTER, 
                "fields": [
                    "syndicate_allocation", "new_subscription", "order_taker", 
                    "order_receipt_date_time", "solicitation_tagging", "vl_details", "order_taker_name",
                    "order_placer_details", "client_profile", "trade_ticket", "brokerage_blotter",
                    "trade_blotter", "ticket_fields"
                ]
            },
            {
                "name": "doc_manager_data", 
                "source": DataSource.DOC_MANAGER, 
                "fields": [
                    "syndicate_communication", "bilateral_agreement", "a92_document_code",
                    "doc_manager", "call_memo", "engagement_status"
                ]
            },
            {
                "name": "voice_logs_data", 
                "source": DataSource.VOICE_LOGS, 
                "fields": [
                    "client_instructions", "fee_communication", "standing_bilateral_agreement_communication", 
                    "order_confirmation", "order_execution_time", "voice_log_details", "voice_log",
                    "client_confirmation", "proposal_confirmation", "mfo_guidance"
                ]
            },
            {
                "name": "aces_data", 
                "source": DataSource.ACES, 
                "fields": [
                    "control_tab_questions", "all_reviews_tab_questions", "language_tab", "productivity_tab"
                ]
            },
            {
                "name": "scribe_data", 
                "source": DataSource.SCRIBE, 
                "fields": [
                    "resource_navigation_awm", "aces_disable_replace_process", "aces_error_identification_communication"
                ]
            }
        ],
        data_sources=[
            DataSource.CONNECT, DataSource.BROKERAGE_BLOTTER, DataSource.DOC_MANAGER,
            DataSource.VOICE_LOGS, DataSource.ACES, DataSource.SCRIBE
        ]
    )
}

DEFAULT_API_CONFIGS = {
    DataSource.CONNECT: APIConfigSchema(
        source=DataSource.CONNECT,
        base_url="https://api.connect.example.com",
        endpoints={
            "order_data": "/api/v1/orders/{order_id}",
            "trade_inquiry": "/api/v1/trade-inquiry/{order_id}",
            "fee_transparency": "/api/v1/fee-transparency/{order_id}"
        },
        headers={"Content-Type": "application/json"},
        timeout=30
    ),
    DataSource.BROKERAGE_BLOTTER: APIConfigSchema(
        source=DataSource.BROKERAGE_BLOTTER,
        base_url="https://api.brokerage.example.com",
        endpoints={
            "syndicate_data": "/api/v1/syndicate/{order_id}",
            "order_details": "/api/v1/orders/{order_id}/details",
            "vl_details": "/api/v1/vl-details/{order_id}"
        },
        headers={"Content-Type": "application/json"},
        timeout=30
    ),
    DataSource.DOC_MANAGER: APIConfigSchema(
        source=DataSource.DOC_MANAGER,
        base_url="https://api.docmanager.example.com",
        endpoints={
            "documents": "/api/v1/documents/{order_id}",
            "syndicate_comm": "/api/v1/syndicate-communication/{order_id}",
            "bilateral_agreement": "/api/v1/bilateral-agreement/{order_id}"
        },
        headers={"Content-Type": "application/json"},
        timeout=30
    ),
    DataSource.VOICE_LOGS: APIConfigSchema(
        source=DataSource.VOICE_LOGS,
        base_url="https://api.voicelogs.example.com",
        endpoints={
            "client_instructions": "/api/v1/client-instructions/{order_id}",
            "fee_communication": "/api/v1/fee-communication/{order_id}",
            "order_confirmation": "/api/v1/order-confirmation/{order_id}"
        },
        headers={"Content-Type": "application/json"},
        timeout=30
    ),
    DataSource.ACES: APIConfigSchema(
        source=DataSource.ACES,
        base_url="https://api.aces.example.com",
        endpoints={
            "control_tab": "/api/v1/control-tab/{order_id}",
            "reviews_tab": "/api/v1/reviews-tab/{order_id}",
            "language_tab": "/api/v1/language-tab/{order_id}",
            "productivity_tab": "/api/v1/productivity-tab/{order_id}"
        },
        headers={"Content-Type": "application/json"},
        timeout=30
    ),
    DataSource.SCRIBE: APIConfigSchema(
        source=DataSource.SCRIBE,
        base_url="https://api.scribe.example.com",
        endpoints={
            "resource_navigation": "/api/v1/resource-navigation/{order_id}",
            "aces_process": "/api/v1/aces-process/{order_id}",
            "error_identification": "/api/v1/error-identification/{order_id}"
        },
        headers={"Content-Type": "application/json"},
        timeout=30
    )
}

DEFAULT_TEST_DAGS = {
    TicketType.FEE_MODIFICATION: TestDAGSchema(
        ticket_type=TicketType.FEE_MODIFICATION,
        dag_id="comprehensive_qa_validation",
        description="Comprehensive QA validation flow based on 16 specific test objectives",
        nodes=[
            # Test 1: Validate eligibility of sample record for evaluation
            TestDAGNode(
                test_id="test_1_eligibility_validation",
                tool_config=TestToolConfig(
                    tool_name="eligibility_validation_tool",
                    tool_type=TestType.VALIDATE_PRESENCE,
                    operation=OperationType.EXISTS,
                    parameters={
                        "data_source": "connect_data",
                        "fields": ["product_type", "transaction_type"],
                        "objective": "Validate eligibility of sample record for evaluation",
                        "error_code": "N/A",
                        "condition": "All products except out-of-scope transactions",
                        "sop_reference": "Validate Eligibility",
                        "primary_platform": "Connect"
                    },
                    success_criteria={"eligible": True}
                ),
                dependencies=[],
                parallel_execution=True
            ),
            # Test 2: Confirm Voice Log recorded for order
            TestDAGNode(
                test_id="test_2_voice_log_validation",
                tool_config=TestToolConfig(
                    tool_name="voice_log_validation_tool",
                    tool_type=TestType.VALIDATE_PRESENCE,
                    operation=OperationType.EXISTS,
                    parameters={
                        "data_source": "voice_logs_data",
                        "fields": ["voice_log_details"],
                        "objective": "Confirm Voice Log recorded for order",
                        "error_code": "Voice Log could not be located / Poor call recording quality",
                        "condition": "Always",
                        "sop_reference": "All Reviews Tab Q #1",
                        "primary_platform": "Voice Logs"
                    },
                    success_criteria={"recorded": True}
                ),
                dependencies=[],
                parallel_execution=True
            ),
            # Test 3: Verify order placer authorization
            TestDAGNode(
                test_id="test_3_order_placer_authorization",
                tool_config=TestToolConfig(
                    tool_name="authorization_validation_tool",
                    tool_type=TestType.VALIDATE_PRESENCE,
                    operation=OperationType.EXISTS,
                    parameters={
                        "data_source": "brokerage_blotter_data",
                        "fields": ["order_placer_details", "client_profile"],
                        "objective": "Verify order placer authorization",
                        "error_code": "Order placer was not authorized",
                        "condition": "Always",
                        "sop_reference": "All Reviews Tab Q #2",
                        "primary_platform": "Brokerage Blotter 2.0, Connect"
                    },
                    success_criteria={"authorized": True}
                ),
                dependencies=[],
                parallel_execution=True
            ),
            # Test 4: Confirm order with client (if Engage = No)
            TestDAGNode(
                test_id="test_4_client_confirmation_no_engage",
                tool_config=TestToolConfig(
                    tool_name="client_confirmation_tool",
                    tool_type=TestType.VALIDATE_PRESENCE,
                    operation=OperationType.EXISTS,
                    parameters={
                        "data_source": "voice_logs_data",
                        "fields": ["voice_log", "client_confirmation"],
                        "objective": "Confirm order with client (if Engage = No)",
                        "error_code": "Trade Order was not confirmed with Client",
                        "condition": "Engage = No",
                        "sop_reference": "All Reviews Tab Q #3",
                        "primary_platform": "Voice Logs"
                    },
                    success_criteria={"confirmed": True}
                ),
                dependencies=[],
                parallel_execution=True
            ),
            # Test 5: Confirm order with client (if Engage = Yes)
            TestDAGNode(
                test_id="test_5_client_confirmation_engage",
                tool_config=TestToolConfig(
                    tool_name="proposal_confirmation_tool",
                    tool_type=TestType.VALIDATE_PRESENCE,
                    operation=OperationType.EXISTS,
                    parameters={
                        "data_source": "voice_logs_data",
                        "fields": ["voice_log", "proposal_confirmation"],
                        "objective": "Confirm order with client (if Engage = Yes)",
                        "error_code": "Proposal ID not stated or attributes not repeated",
                        "condition": "Engage = Yes",
                        "sop_reference": "All Reviews Tab Q #4",
                        "primary_platform": "Voice Logs"
                    },
                    success_criteria={"confirmed": True}
                ),
                dependencies=[],
                parallel_execution=True
            ),
            # Test 6: Ensure no advice on unapproved products
            TestDAGNode(
                test_id="test_6_unapproved_products_advice",
                tool_config=TestToolConfig(
                    tool_name="advice_validation_tool",
                    tool_type=TestType.VALIDATE_PRESENCE,
                    operation=OperationType.NOT_EXISTS,
                    parameters={
                        "data_source": "voice_logs_data",
                        "fields": ["voice_log", "trade_inquiry"],
                        "objective": "Ensure no advice on unapproved products",
                        "error_code": "Investor gave advice for unapproved products",
                        "condition": "Order Type ≠ Approved",
                        "sop_reference": "All Reviews Tab Q #5",
                        "primary_platform": "Brokerage Blotter 2.0, Voice Logs"
                    },
                    success_criteria={"no_advice": True}
                ),
                dependencies=[],
                parallel_execution=True
            ),
            # Test 7: Validate SCRF or DRE documentation
            TestDAGNode(
                test_id="test_7_scrf_dre_documentation",
                tool_config=TestToolConfig(
                    tool_name="documentation_validation_tool",
                    tool_type=TestType.VALIDATE_PRESENCE,
                    operation=OperationType.EXISTS,
                    parameters={
                        "data_source": "doc_manager_data",
                        "fields": ["doc_manager", "call_memo"],
                        "objective": "Validate SCRF or DRE documentation",
                        "error_code": "SCRF/DRE not on file",
                        "condition": "Order Type = FVEQ New Issuance",
                        "sop_reference": "All Reviews Tab Q #6",
                        "primary_platform": "Doc Manager"
                    },
                    success_criteria={"documented": True}
                ),
                dependencies=[],
                parallel_execution=True
            ),
            # Test 8: Confirm trade solicitation documentation
            TestDAGNode(
                test_id="test_8_trade_solicitation_documentation",
                tool_config=TestToolConfig(
                    tool_name="solicitation_validation_tool",
                    tool_type=TestType.VALIDATE_PRESENCE,
                    operation=OperationType.EXISTS,
                    parameters={
                        "data_source": "brokerage_blotter_data",
                        "fields": ["trade_ticket", "brokerage_blotter"],
                        "objective": "Confirm trade solicitation documentation",
                        "error_code": "Trade solicitation inaccurately tagged / not documented",
                        "condition": "Always",
                        "sop_reference": "All Reviews Tab Q #7",
                        "primary_platform": "Brokerage Blotter 2.0"
                    },
                    success_criteria={"documented": True}
                ),
                dependencies=[],
                parallel_execution=True
            ),
            # Test 9: Verify trade documentation on blotter/ticket
            TestDAGNode(
                test_id="test_9_trade_documentation_verification",
                tool_config=TestToolConfig(
                    tool_name="trade_documentation_tool",
                    tool_type=TestType.VALIDATE_PRESENCE,
                    operation=OperationType.EXISTS,
                    parameters={
                        "data_source": "brokerage_blotter_data",
                        "fields": ["trade_blotter", "ticket_fields"],
                        "objective": "Verify trade documentation on blotter/ticket",
                        "error_code": "VL details inaccurate/not documented",
                        "condition": "Always",
                        "sop_reference": "All Reviews Tab Q #8",
                        "primary_platform": "Brokerage Blotter 2.0"
                    },
                    success_criteria={"complete_and_accurate": True}
                ),
                dependencies=[],
                parallel_execution=True
            ),
            # Test 10: Avoid client-specific advice for MFO
            TestDAGNode(
                test_id="test_10_mfo_advice_validation",
                tool_config=TestToolConfig(
                    tool_name="mfo_advice_validation_tool",
                    tool_type=TestType.VALIDATE_PRESENCE,
                    operation=OperationType.NOT_EXISTS,
                    parameters={
                        "data_source": "voice_logs_data",
                        "fields": ["mfo_guidance", "voice_log"],
                        "objective": "Avoid client-specific advice for MFO",
                        "error_code": "Client-specific advice was provided",
                        "condition": "Order taken by MFO",
                        "sop_reference": "All Reviews Tab Q #9",
                        "primary_platform": "Voice Logs"
                    },
                    success_criteria={"no_client_advice": True}
                ),
                dependencies=[],
                parallel_execution=True
            ),
            # Test 11: Check timely order execution
            TestDAGNode(
                test_id="test_11_timely_execution_check",
                tool_config=TestToolConfig(
                    tool_name="timely_execution_tool",
                    tool_type=TestType.DATE_RANGE_CHECK,
                    operation=OperationType.IN_RANGE,
                    parameters={
                        "data_source": "connect_data",
                        "fields": ["execution_timestamps", "order_time", "profile_canvas"],
                        "objective": "Check timely order execution",
                        "error_code": "Order not executed timely",
                        "condition": "Product class = Equity, ETF, Listed Options, FX, Precious Metals",
                        "sop_reference": "All Reviews Tab Q #10",
                        "primary_platform": "Connect",
                        "max_delay_minutes": 15
                    },
                    success_criteria={"within_15_mins": True}
                ),
                dependencies=[],
                parallel_execution=True
            ),
            # Test 12: Verify engagement status for account
            TestDAGNode(
                test_id="test_12_engagement_status_verification",
                tool_config=TestToolConfig(
                    tool_name="engagement_status_tool",
                    tool_type=TestType.COMPARE,
                    operation=OperationType.EQUALS,
                    parameters={
                        "data_source_a": "connect_data",
                        "data_source_b": "doc_manager_data",
                        "fields_a": ["global_fee_transparency"],
                        "fields_b": ["engagement_status"],
                        "objective": "Verify engagement status for account",
                        "error_code": "N/A",
                        "condition": "—",
                        "sop_reference": "Control Tab Q #3",
                        "primary_platform": "Connect, Doc Manager"
                    },
                    success_criteria={"status_matches": True}
                ),
                dependencies=[],
                parallel_execution=True
            ),
            # Test 13: Check bilateral agreement documentation
            TestDAGNode(
                test_id="test_13_bilateral_agreement_documentation",
                tool_config=TestToolConfig(
                    tool_name="bilateral_agreement_tool",
                    tool_type=TestType.VALIDATE_PRESENCE,
                    operation=OperationType.EXISTS,
                    parameters={
                        "data_source": "doc_manager_data",
                        "fields": ["bilateral_agreement"],
                        "objective": "Check bilateral agreement documentation",
                        "error_code": "Agreement not documented",
                        "condition": "Products in scope for bilateral agreement",
                        "sop_reference": "All Reviews Tab Q #1",
                        "primary_platform": "Doc Manager"
                    },
                    success_criteria={"documented": True}
                ),
                dependencies=[],
                parallel_execution=True
            ),
            # Test 14: Validate if Syndicate Allocation is correct
            TestDAGNode(
                test_id="test_14_syndicate_allocation_validation",
                tool_config=TestToolConfig(
                    tool_name="syndicate_allocation_tool",
                    tool_type=TestType.VALIDATE_PRESENCE,
                    operation=OperationType.EXISTS,
                    parameters={
                        "data_source": "brokerage_blotter_data",
                        "fields": ["syndicate_allocation"],
                        "objective": "Validate if Syndicate Allocation is correct",
                        "error_code": "Incorrect Syndicate Allocation tagging",
                        "condition": "Order Type = FVEQ New Issuance",
                        "sop_reference": "Control Tab Q #2",
                        "primary_platform": "Brokerage Blotter 2.0"
                    },
                    success_criteria={"correct": True}
                ),
                dependencies=[],
                parallel_execution=True
            ),
            # Test 15: Check New Subscription status
            TestDAGNode(
                test_id="test_15_new_subscription_status",
                tool_config=TestToolConfig(
                    tool_name="new_subscription_tool",
                    tool_type=TestType.VALIDATE_PRESENCE,
                    operation=OperationType.EXISTS,
                    parameters={
                        "data_source": "brokerage_blotter_data",
                        "fields": ["new_subscription"],
                        "objective": "Check New Subscription status",
                        "error_code": "Incorrect New Subscription status",
                        "condition": "Order Type = FI New Issuance",
                        "sop_reference": "Control Tab Q #2",
                        "primary_platform": "Brokerage Blotter 2.0"
                    },
                    success_criteria={"correct": True}
                ),
                dependencies=[],
                parallel_execution=True
            ),
            # Test 16: Ensure all required ACES fields are complete
            TestDAGNode(
                test_id="test_16_aces_fields_completeness",
                tool_config=TestToolConfig(
                    tool_name="aces_completeness_tool",
                    tool_type=TestType.VALIDATE_PRESENCE,
                    operation=OperationType.EXISTS,
                    parameters={
                        "data_source": "aces_data",
                        "fields": ["control_tab_questions", "all_reviews_tab_questions", "language_tab", "productivity_tab"],
                        "objective": "Ensure all required ACES fields are complete",
                        "error_code": "Incomplete ACES fields",
                        "condition": "Always",
                        "sop_reference": "Final Steps",
                        "primary_platform": "ACES"
                    },
                    success_criteria={"complete": True}
                ),
                dependencies=[
                    "test_1_eligibility_validation", "test_2_voice_log_validation", "test_3_order_placer_authorization",
                    "test_4_client_confirmation_no_engage", "test_5_client_confirmation_engage", "test_6_unapproved_products_advice",
                    "test_7_scrf_dre_documentation", "test_8_trade_solicitation_documentation", "test_9_trade_documentation_verification",
                    "test_10_mfo_advice_validation", "test_11_timely_execution_check", "test_12_engagement_status_verification",
                    "test_13_bilateral_agreement_documentation", "test_14_syndicate_allocation_validation", "test_15_new_subscription_status"
                ],
                parallel_execution=False
            )
        ],
        execution_strategy="hybrid",
        max_parallel_tests=8
    )
}
