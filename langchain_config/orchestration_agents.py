"""
Orchestration agents for the LangChain-based QA pipeline.
Manages test mapping and policy rules for dynamic test execution.
"""

from typing import Dict, Any, Optional, List
import json
from langchain_openai import ChatOpenAI
from langchain_config.platform_agents import (
    PlatformConnectAgent, VoiceLogAgent, DocManagerAgent, 
    BrokerageBlotterAgent, ACESAgent, SCRIBEAgent
)
from langchain_config.schemas import TestDAGNode, TestToolConfig, TestType, OperationType

class TestMapperAgent:
    """Agent that maps test objectives to required platform agents and tools"""
    
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        self.test_mapping = self._initialize_test_mapping()
    
    def _initialize_test_mapping(self) -> Dict[str, Dict[str, Any]]:
        """Initialize the mapping of test objectives to required agents and tools"""
        return {
            "test_1_eligibility_validation": {
                "objective": "Validate eligibility of sample record for evaluation",
                "required_agents": ["PlatformConnectAgent"],
                "required_tools": ["eligibility_check"],
                "data_points": ["product_type", "transaction_type"],
                "validation_logic": "Pass if eligible, Fail if not",
                "error_code": "N/A",
                "condition": "All products except out-of-scope transactions",
                "sop_reference": "Validate Eligibility",
                "primary_platform": "Connect"
            },
            "test_2_voice_log_validation": {
                "objective": "Confirm Voice Log recorded for order",
                "required_agents": ["VoiceLogAgent"],
                "required_tools": ["voice_log_presence_check"],
                "data_points": ["voice_log_details"],
                "validation_logic": "Pass if recorded, Fail if not",
                "error_code": "Voice Log could not be located / Poor call recording quality",
                "condition": "Always",
                "sop_reference": "All Reviews Tab Q #1",
                "primary_platform": "Voice Logs"
            },
            "test_3_order_placer_authorization": {
                "objective": "Verify order placer authorization",
                "required_agents": ["BrokerageBlotterAgent"],
                "required_tools": ["authorization_check"],
                "data_points": ["order_placer_details", "client_profile"],
                "validation_logic": "Pass if authorized, Fail if not",
                "error_code": "Order placer was not authorized",
                "condition": "Always",
                "sop_reference": "All Reviews Tab Q #2",
                "primary_platform": "Brokerage Blotter 2.0, Connect"
            },
            "test_4_client_confirmation_no_engage": {
                "objective": "Confirm order with client (if Engage = No)",
                "required_agents": ["VoiceLogAgent"],
                "required_tools": ["client_confirmation_check"],
                "data_points": ["voice_log", "client_confirmation"],
                "validation_logic": "Pass if confirmed, Fail if not",
                "error_code": "Trade Order was not confirmed with Client",
                "condition": "Engage = No",
                "sop_reference": "All Reviews Tab Q #3",
                "primary_platform": "Voice Logs"
            },
            "test_5_client_confirmation_engage": {
                "objective": "Confirm order with client (if Engage = Yes)",
                "required_agents": ["VoiceLogAgent"],
                "required_tools": ["proposal_confirmation_check"],
                "data_points": ["voice_log", "proposal_confirmation"],
                "validation_logic": "Pass if confirmed, Fail if not",
                "error_code": "Proposal ID not stated or attributes not repeated",
                "condition": "Engage = Yes",
                "sop_reference": "All Reviews Tab Q #4",
                "primary_platform": "Voice Logs"
            },
            "test_6_unapproved_products_advice": {
                "objective": "Ensure no advice on unapproved products",
                "required_agents": ["VoiceLogAgent", "BrokerageBlotterAgent"],
                "required_tools": ["advice_detection_check"],
                "data_points": ["voice_log", "trade_inquiry"],
                "validation_logic": "Pass if no advice given, Fail if advice given",
                "error_code": "Investor gave advice for unapproved products",
                "condition": "Order Type ≠ Approved",
                "sop_reference": "All Reviews Tab Q #5",
                "primary_platform": "Brokerage Blotter 2.0, Voice Logs"
            },
            "test_7_scrf_dre_documentation": {
                "objective": "Validate SCRF or DRE documentation",
                "required_agents": ["DocManagerAgent"],
                "required_tools": ["document_presence_check"],
                "data_points": ["doc_manager", "call_memo"],
                "validation_logic": "Pass if on file, Fail if not",
                "error_code": "SCRF/DRE not on file",
                "condition": "Order Type = FVEQ New Issuance",
                "sop_reference": "All Reviews Tab Q #6",
                "primary_platform": "Doc Manager"
            },
            "test_8_trade_solicitation_documentation": {
                "objective": "Confirm trade solicitation documentation",
                "required_agents": ["BrokerageBlotterAgent"],
                "required_tools": ["solicitation_check"],
                "data_points": ["trade_ticket", "brokerage_blotter"],
                "validation_logic": "Pass if documented/correct, Fail if not",
                "error_code": "Trade solicitation inaccurately tagged / not documented",
                "condition": "Always",
                "sop_reference": "All Reviews Tab Q #7",
                "primary_platform": "Brokerage Blotter 2.0"
            },
            "test_9_trade_documentation_verification": {
                "objective": "Verify trade documentation on blotter/ticket",
                "required_agents": ["BrokerageBlotterAgent"],
                "required_tools": ["documentation_completeness_check"],
                "data_points": ["trade_blotter", "ticket_fields"],
                "validation_logic": "Pass if complete and accurate, Fail if not",
                "error_code": "VL details inaccurate/not documented",
                "condition": "Always",
                "sop_reference": "All Reviews Tab Q #8",
                "primary_platform": "Brokerage Blotter 2.0"
            },
            "test_10_mfo_advice_validation": {
                "objective": "Avoid client-specific advice for MFO",
                "required_agents": ["VoiceLogAgent"],
                "required_tools": ["mfo_advice_check"],
                "data_points": ["mfo_guidance", "voice_log"],
                "validation_logic": "Pass if not given, Fail if found",
                "error_code": "Client-specific advice was provided",
                "condition": "Order taken by MFO",
                "sop_reference": "All Reviews Tab Q #9",
                "primary_platform": "Voice Logs"
            },
            "test_11_timely_execution_check": {
                "objective": "Check timely order execution",
                "required_agents": ["PlatformConnectAgent"],
                "required_tools": ["timestamp_diff_check"],
                "data_points": ["execution_timestamps", "order_time", "profile_canvas"],
                "validation_logic": "Pass if within 15 mins, Fail if not",
                "error_code": "Order not executed timely",
                "condition": "Product class = Equity, ETF, Listed Options, FX, Precious Metals",
                "sop_reference": "All Reviews Tab Q #10",
                "primary_platform": "Connect"
            },
            "test_12_engagement_status_verification": {
                "objective": "Verify engagement status for account",
                "required_agents": ["PlatformConnectAgent", "DocManagerAgent"],
                "required_tools": ["engagement_status_check"],
                "data_points": ["global_fee_transparency", "engagement_status"],
                "validation_logic": "Pass if Engage status matches",
                "error_code": "N/A",
                "condition": "—",
                "sop_reference": "Control Tab Q #3",
                "primary_platform": "Connect, Doc Manager"
            },
            "test_13_bilateral_agreement_documentation": {
                "objective": "Check bilateral agreement documentation",
                "required_agents": ["DocManagerAgent"],
                "required_tools": ["bilateral_agreement_check"],
                "data_points": ["bilateral_agreement"],
                "validation_logic": "Pass if documented, Fail if not",
                "error_code": "Agreement not documented",
                "condition": "Products in scope for bilateral agreement",
                "sop_reference": "All Reviews Tab Q #1",
                "primary_platform": "Doc Manager"
            },
            "test_14_syndicate_allocation_validation": {
                "objective": "Validate if Syndicate Allocation is correct",
                "required_agents": ["BrokerageBlotterAgent"],
                "required_tools": ["syndicate_allocation_check"],
                "data_points": ["syndicate_allocation"],
                "validation_logic": "Pass if correct, Fail if not",
                "error_code": "Incorrect Syndicate Allocation tagging",
                "condition": "Order Type = FVEQ New Issuance",
                "sop_reference": "Control Tab Q #2",
                "primary_platform": "Brokerage Blotter 2.0"
            },
            "test_15_new_subscription_status": {
                "objective": "Check New Subscription status",
                "required_agents": ["BrokerageBlotterAgent"],
                "required_tools": ["new_subscription_check"],
                "data_points": ["new_subscription"],
                "validation_logic": "Pass if correct, Fail if not",
                "error_code": "Incorrect New Subscription status",
                "condition": "Order Type = FI New Issuance",
                "sop_reference": "Control Tab Q #2",
                "primary_platform": "Brokerage Blotter 2.0"
            },
            "test_16_aces_fields_completeness": {
                "objective": "Ensure all required ACES fields are complete",
                "required_agents": ["ACESAgent"],
                "required_tools": ["aces_completeness_check"],
                "data_points": ["control_tab_questions", "all_reviews_tab_questions", "language_tab", "productivity_tab"],
                "validation_logic": "Pass if complete, Fail if not",
                "error_code": "Incomplete ACES fields",
                "condition": "Always",
                "sop_reference": "Final Steps",
                "primary_platform": "ACES"
            }
        }
    
    def get_test_requirements(self, test_id: str) -> Dict[str, Any]:
        """Get the requirements for a specific test"""
        return self.test_mapping.get(test_id, {})
    
    def map_test_to_agents(self, test_id: str) -> List[str]:
        """Map a test to its required platform agents"""
        requirements = self.get_test_requirements(test_id)
        return requirements.get("required_agents", [])
    
    def map_test_to_tools(self, test_id: str) -> List[str]:
        """Map a test to its required tools"""
        requirements = self.get_test_requirements(test_id)
        return requirements.get("required_tools", [])
    
    def get_test_condition(self, test_id: str) -> str:
        """Get the condition for when a test should be executed"""
        requirements = self.get_test_requirements(test_id)
        return requirements.get("condition", "Always")
    
    def should_execute_test(self, test_id: str, context: Dict[str, Any]) -> bool:
        """Determine if a test should be executed based on context"""
        condition = self.get_test_condition(test_id)
        
        if condition == "Always":
            return True
        elif condition == "Engage = No":
            return context.get("engage_status", "").lower() == "no"
        elif condition == "Engage = Yes":
            return context.get("engage_status", "").lower() == "yes"
        elif condition == "Order Type = FVEQ New Issuance":
            return context.get("order_type", "") == "FVEQ New Issuance"
        elif condition == "Order Type = FI New Issuance":
            return context.get("order_type", "") == "FI New Issuance"
        elif condition == "Order Type ≠ Approved":
            return context.get("order_type", "") != "Approved"
        elif condition == "Order taken by MFO":
            return context.get("order_taker_type", "") == "MFO"
        elif condition == "Products in scope for bilateral agreement":
            return context.get("product_type", "") in ["Equity", "Fixed Income"]
        elif condition.startswith("Product class ="):
            product_classes = condition.split("=")[1].strip().split(", ")
            return context.get("product_class", "") in product_classes
        
        return True  # Default to executing the test

class PolicyRulesAgent:
    """Agent that manages policy rules and test matrix configuration"""
    
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        self.test_matrix = self._load_test_matrix()
    
    def _load_test_matrix(self) -> Dict[str, Any]:
        """Load the QA test matrix configuration"""
        return {
            "test_categories": {
                "eligibility": {
                    "tests": ["test_1_eligibility_validation"],
                    "priority": "high",
                    "mandatory": True
                },
                "voice_logs": {
                    "tests": ["test_2_voice_log_validation"],
                    "priority": "high",
                    "mandatory": True
                },
                "authorization": {
                    "tests": ["test_3_order_placer_authorization"],
                    "priority": "high",
                    "mandatory": True
                },
                "client_confirmation": {
                    "tests": ["test_4_client_confirmation_no_engage", "test_5_client_confirmation_engage"],
                    "priority": "high",
                    "mandatory": True,
                    "mutually_exclusive": True
                },
                "advice_validation": {
                    "tests": ["test_6_unapproved_products_advice", "test_10_mfo_advice_validation"],
                    "priority": "medium",
                    "mandatory": False
                },
                "documentation": {
                    "tests": ["test_7_scrf_dre_documentation", "test_8_trade_solicitation_documentation", 
                             "test_9_trade_documentation_verification", "test_13_bilateral_agreement_documentation"],
                    "priority": "medium",
                    "mandatory": True
                },
                "execution_validation": {
                    "tests": ["test_11_timely_execution_check"],
                    "priority": "high",
                    "mandatory": True
                },
                "status_verification": {
                    "tests": ["test_12_engagement_status_verification"],
                    "priority": "medium",
                    "mandatory": False
                },
                "allocation_validation": {
                    "tests": ["test_14_syndicate_allocation_validation", "test_15_new_subscription_status"],
                    "priority": "medium",
                    "mandatory": False
                },
                "completeness_check": {
                    "tests": ["test_16_aces_fields_completeness"],
                    "priority": "high",
                    "mandatory": True
                }
            },
            "execution_rules": {
                "parallel_execution": {
                    "enabled": True,
                    "max_concurrent": 8,
                    "excluded_tests": ["test_16_aces_fields_completeness"]
                },
                "retry_policy": {
                    "max_retries": 3,
                    "retry_delay": 1,
                    "exponential_backoff": True
                },
                "timeout_policy": {
                    "default_timeout": 60,
                    "llm_timeout": 120,
                    "api_timeout": 30
                }
            },
            "quality_gates": {
                "minimum_pass_rate": 0.8,
                "critical_test_failure": "blocking",
                "warning_threshold": 0.9
            }
        }
    
    def get_test_categories(self) -> Dict[str, Any]:
        """Get all test categories and their configurations"""
        return self.test_matrix.get("test_categories", {})
    
    def get_execution_rules(self) -> Dict[str, Any]:
        """Get execution rules for test runs"""
        return self.test_matrix.get("execution_rules", {})
    
    def get_quality_gates(self) -> Dict[str, Any]:
        """Get quality gate configurations"""
        return self.test_matrix.get("quality_gates", {})
    
    def get_mandatory_tests(self) -> List[str]:
        """Get list of mandatory tests"""
        mandatory_tests = []
        for category, config in self.test_matrix.get("test_categories", {}).items():
            if config.get("mandatory", False):
                mandatory_tests.extend(config.get("tests", []))
        return mandatory_tests
    
    def get_high_priority_tests(self) -> List[str]:
        """Get list of high priority tests"""
        high_priority_tests = []
        for category, config in self.test_matrix.get("test_categories", {}).items():
            if config.get("priority") == "high":
                high_priority_tests.extend(config.get("tests", []))
        return high_priority_tests
    
    def should_retry_test(self, test_id: str, attempt_count: int) -> bool:
        """Determine if a test should be retried"""
        retry_policy = self.test_matrix.get("execution_rules", {}).get("retry_policy", {})
        max_retries = retry_policy.get("max_retries", 3)
        return attempt_count < max_retries
    
    def get_test_timeout(self, test_id: str) -> int:
        """Get timeout for a specific test"""
        timeout_policy = self.test_matrix.get("execution_rules", {}).get("timeout_policy", {})
        
        # Check if test involves LLM operations
        if "llm" in test_id.lower() or "semantic" in test_id.lower():
            return timeout_policy.get("llm_timeout", 120)
        elif "api" in test_id.lower():
            return timeout_policy.get("api_timeout", 30)
        else:
            return timeout_policy.get("default_timeout", 60)
    
    def evaluate_quality_gate(self, test_results: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate if quality gates are met"""
        quality_gates = self.get_quality_gates()
        minimum_pass_rate = quality_gates.get("minimum_pass_rate", 0.8)
        
        total_tests = len(test_results)
        passed_tests = sum(1 for result in test_results.values() if result.get("passed", False))
        pass_rate = passed_tests / total_tests if total_tests > 0 else 0
        
        return {
            "pass_rate": pass_rate,
            "meets_quality_gate": pass_rate >= minimum_pass_rate,
            "minimum_required": minimum_pass_rate,
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": total_tests - passed_tests
        }

class EnhancedTestExecutionAgent:
    """Enhanced test execution agent that uses platform agents and orchestration"""
    
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        self.test_mapper = TestMapperAgent(llm)
        self.policy_rules = PolicyRulesAgent(llm)
        
        # Initialize platform agents
        self.connect_agent = PlatformConnectAgent(llm)
        self.voice_log_agent = VoiceLogAgent(llm)
        self.doc_manager_agent = DocManagerAgent(llm)
        self.brokerage_blotter_agent = BrokerageBlotterAgent(llm)
        self.aces_agent = ACESAgent(llm)
        self.scribe_agent = SCRIBEAgent(llm)
        
        self.agent_map = {
            "PlatformConnectAgent": self.connect_agent,
            "VoiceLogAgent": self.voice_log_agent,
            "DocManagerAgent": self.doc_manager_agent,
            "BrokerageBlotterAgent": self.brokerage_blotter_agent,
            "ACESAgent": self.aces_agent,
            "SCRIBEAgent": self.scribe_agent
        }
    
    def execute_enhanced_test(self, test_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a test using the enhanced platform agents"""
        try:
            # Get test requirements
            requirements = self.test_mapper.get_test_requirements(test_id)
            if not requirements:
                return {
                    "test_id": test_id,
                    "passed": False,
                    "message": f"Test {test_id} not found in mapping",
                    "error": "Unknown test"
                }
            
            # Check if test should be executed based on context
            if not self.test_mapper.should_execute_test(test_id, context):
                return {
                    "test_id": test_id,
                    "passed": True,
                    "message": f"Test {test_id} skipped - condition not met",
                    "skipped": True
                }
            
            # Execute the test based on its type
            result = self._execute_test_by_type(test_id, requirements, context)
            
            return {
                "test_id": test_id,
                "passed": result.get("passed", False),
                "message": result.get("message", ""),
                "details": result.get("details", {}),
                "objective": requirements.get("objective", ""),
                "sop_reference": requirements.get("sop_reference", ""),
                "primary_platform": requirements.get("primary_platform", "")
            }
        
        except Exception as e:
            return {
                "test_id": test_id,
                "passed": False,
                "message": f"Test execution failed: {str(e)}",
                "error": str(e)
            }
    
    def _execute_test_by_type(self, test_id: str, requirements: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute test based on its specific type and requirements"""
        objective = requirements.get("objective", "")
        
        if "eligibility" in objective.lower():
            return self._execute_eligibility_test(test_id, context)
        elif "voice log" in objective.lower():
            return self._execute_voice_log_test(test_id, context)
        elif "authorization" in objective.lower():
            return self._execute_authorization_test(test_id, context)
        elif "confirmation" in objective.lower():
            return self._execute_confirmation_test(test_id, context)
        elif "advice" in objective.lower():
            return self._execute_advice_test(test_id, context)
        elif "documentation" in objective.lower():
            return self._execute_documentation_test(test_id, context)
        elif "timely" in objective.lower():
            return self._execute_timely_execution_test(test_id, context)
        elif "engagement" in objective.lower():
            return self._execute_engagement_test(test_id, context)
        elif "syndicate" in objective.lower():
            return self._execute_syndicate_test(test_id, context)
        elif "subscription" in objective.lower():
            return self._execute_subscription_test(test_id, context)
        elif "aces" in objective.lower():
            return self._execute_aces_test(test_id, context)
        else:
            return {
                "passed": False,
                "message": f"Unknown test type for {test_id}",
                "details": {}
            }
    
    def _execute_eligibility_test(self, test_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute eligibility validation test"""
        order_id = context.get("order_id", "")
        product_type = context.get("product_type", "Equity")
        transaction_type = context.get("transaction_type", "Buy")
        
        result = self.connect_agent.validate_eligibility(order_id, product_type, transaction_type)
        
        return {
            "passed": result["eligible"],
            "message": result["reasoning"],
            "details": result
        }
    
    def _execute_voice_log_test(self, test_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute voice log validation test"""
        order_id = context.get("order_id", "")
        
        result = self.voice_log_agent.validate_voice_log_presence(order_id)
        
        return {
            "passed": result["recorded"] and result["quality_acceptable"],
            "message": f"Voice log {'recorded' if result['recorded'] else 'not recorded'} with {'good' if result['quality_acceptable'] else 'poor'} quality",
            "details": result
        }
    
    def _execute_authorization_test(self, test_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute order placer authorization test"""
        order_id = context.get("order_id", "")
        
        result = self.brokerage_blotter_agent.validate_order_placer_authorization(order_id)
        
        return {
            "passed": result["authorized"],
            "message": result["message"],
            "details": result
        }
    
    def _execute_confirmation_test(self, test_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute client confirmation test"""
        order_id = context.get("order_id", "")
        engage_status = context.get("engage_status", "Engage = No")
        
        result = self.voice_log_agent.check_client_confirmation(order_id, engage_status)
        
        return {
            "passed": result["confirmed"],
            "message": result["message"],
            "details": result
        }
    
    def _execute_advice_test(self, test_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute advice validation test"""
        order_id = context.get("order_id", "")
        
        if "unapproved" in test_id:
            trade_inquiry = context.get("trade_inquiry", "")
            result = self.voice_log_agent.check_unapproved_advice(order_id, trade_inquiry)
        else:  # MFO advice
            result = self.voice_log_agent.check_mfo_advice(order_id)
        
        return {
            "passed": result.get("no_advice_given", result.get("no_client_advice", False)),
            "message": result["message"],
            "details": result
        }
    
    def _execute_documentation_test(self, test_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute documentation validation test"""
        order_id = context.get("order_id", "")
        order_type = context.get("order_type", "")
        
        if "scrf" in test_id or "dre" in test_id:
            result = self.doc_manager_agent.validate_scrf_dre_documentation(order_id, order_type)
        elif "solicitation" in test_id:
            result = self.brokerage_blotter_agent.validate_trade_solicitation(order_id)
        elif "trade_documentation" in test_id:
            result = self.brokerage_blotter_agent.validate_trade_documentation(order_id)
        elif "bilateral" in test_id:
            result = self.doc_manager_agent.validate_bilateral_agreement(order_id)
        else:
            result = {"documented": False, "message": "Unknown documentation test"}
        
        return {
            "passed": result.get("documented", result.get("complete_and_accurate", False)),
            "message": result["message"],
            "details": result
        }
    
    def _execute_timely_execution_test(self, test_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute timely execution test"""
        order_id = context.get("order_id", "")
        order_time = context.get("order_time", "")
        execution_time = context.get("execution_time", "")
        
        result = self.connect_agent.check_timely_execution(order_time, execution_time)
        
        return {
            "passed": result["within_sla"],
            "message": result["message"],
            "details": result
        }
    
    def _execute_engagement_test(self, test_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute engagement status test"""
        order_id = context.get("order_id", "")
        
        result = self.doc_manager_agent.check_engagement_status(order_id)
        
        return {
            "passed": result["status"] in ["Yes", "No"],
            "message": result["message"],
            "details": result
        }
    
    def _execute_syndicate_test(self, test_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute syndicate allocation test"""
        order_id = context.get("order_id", "")
        order_type = context.get("order_type", "")
        
        result = self.brokerage_blotter_agent.validate_syndicate_allocation(order_id, order_type)
        
        return {
            "passed": result["correct"],
            "message": result["message"],
            "details": result
        }
    
    def _execute_subscription_test(self, test_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute new subscription test"""
        order_id = context.get("order_id", "")
        order_type = context.get("order_type", "")
        
        result = self.brokerage_blotter_agent.validate_new_subscription_status(order_id, order_type)
        
        return {
            "passed": result["correct"],
            "message": result["message"],
            "details": result
        }
    
    def _execute_aces_test(self, test_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute ACES completeness test"""
        order_id = context.get("order_id", "")
        
        result = self.aces_agent.validate_aces_completeness(order_id)
        
        return {
            "passed": result["complete"],
            "message": result["message"],
            "details": result
        }
