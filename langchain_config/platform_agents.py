"""
Specialized platform agents for the LangChain-based QA pipeline.
Each agent handles data extraction and validation for specific platforms.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import json
import re
from langchain_openai import ChatOpenAI
from langchain_config.enhanced_tools import EnhancedToolFactory
from langchain_config.schemas import DataSource

class PlatformConnectAgent:
    """Agent for Connect platform data extraction and validation"""
    
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        self.tool_factory = EnhancedToolFactory(llm)
    
    def extract_connect_data(self, order_id: str) -> Dict[str, Any]:
        """Extract data from Connect platform"""
        # Mock implementation - in production, this would call Connect APIs
        return {
            "order_id": order_id,
            "trade_inquiry": "Equity trade inquiry for client ABC",
            "order_restrictions": "No restrictions",
            "profile_canvas": "Standard client profile",
            "global_fee_transparency": "Fee structure disclosed",
            "fee_instruct_report": "FEE_INSTRUCT_2025_001",
            "product_type": "Equity",
            "transaction_type": "Buy",
            "execution_timestamps": "2025-10-23T14:35:00Z",
            "order_time": "2025-10-23T14:30:00Z",
            "engage_status": "Engage = Yes"  # This would be determined by LLM analysis
        }
    
    def validate_eligibility(self, order_id: str, product_type: str, transaction_type: str) -> Dict[str, Any]:
        """Validate if order is eligible for evaluation"""
        # Check if product type and transaction type are in scope
        in_scope_products = ["Equity", "ETF", "Listed Options", "FX", "Precious Metals"]
        in_scope_transactions = ["Buy", "Sell", "New Issuance"]
        
        eligible = (product_type in in_scope_products and 
                   transaction_type in in_scope_transactions)
        
        return {
            "eligible": eligible,
            "product_type": product_type,
            "transaction_type": transaction_type,
            "reasoning": f"Product {product_type} and transaction {transaction_type} are {'in' if eligible else 'out of'} scope"
        }
    
    def check_timely_execution(self, order_time: str, execution_time: str, 
                             max_delay_minutes: int = 15) -> Dict[str, Any]:
        """Check if order was executed within SLA"""
        # Ensure we have valid timestamps
        if not order_time or not execution_time:
            return {
                "within_sla": False,
                "message": "Missing order time or execution time",
                "details": {"order_time": order_time, "execution_time": execution_time}
            }
        
        result = self.tool_factory.execute_enhanced_tool(
            "timestamp_diff_check",
            "timely_execution_check",
            start_time=order_time,
            end_time=execution_time,
            max_delay_minutes=max_delay_minutes
        )
        
        return {
            "within_sla": result.passed,
            "message": result.message,
            "details": result.details
        }

class VoiceLogAgent:
    """Agent for voice log analysis and validation"""
    
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        self.tool_factory = EnhancedToolFactory(llm)
    
    def extract_voice_log_data(self, order_id: str) -> Dict[str, Any]:
        """Extract voice log data and metadata"""
        # Mock implementation - in production, this would integrate with voice recording systems
        return {
            "voice_log_details": "High quality voice recording available",
            "voice_log": "Voice log recorded and stored",
            "client_instructions": "Client provided specific instructions for trade execution",
            "fee_communication": "Fee structure communicated to client",
            "standing_bilateral_agreement_communication": "SBA terms discussed",
            "order_confirmation": "Order confirmed with client",
            "order_execution_time": "2025-10-23T14:35:00Z",
            "client_confirmation": "Client confirmed order details",
            "proposal_confirmation": "Proposal ID stated and attributes repeated",
            "mfo_guidance": "MFO guidance provided without client-specific advice",
            "call_duration": "5:23",
            "call_quality": "High",
            "participants": ["John Smith", "Client ABC"]
        }
    
    def validate_voice_log_presence(self, order_id: str) -> Dict[str, Any]:
        """Validate that voice log exists and has good quality"""
        voice_data = self.extract_voice_log_data(order_id)
        
        # Check if voice log exists and has good quality
        has_voice_log = voice_data.get("voice_log_details") is not None
        good_quality = voice_data.get("call_quality") == "High"
        
        return {
            "recorded": has_voice_log,
            "quality_acceptable": good_quality,
            "call_duration": voice_data.get("call_duration"),
            "participants": voice_data.get("participants", [])
        }
    
    def check_client_confirmation(self, order_id: str, engage_status: str) -> Dict[str, Any]:
        """Check if client confirmation was properly obtained"""
        voice_data = self.extract_voice_log_data(order_id)
        
        if engage_status == "Engage = No":
            # Check for direct client confirmation
            confirmation_text = voice_data.get("client_confirmation", "")
            expected_confirmation = "Client confirmed order details"
            
            result = self.tool_factory.execute_enhanced_tool(
                "compare_text_semantic",
                "client_confirmation_check",
                text_a=expected_confirmation,
                text_b=confirmation_text,
                comparison_type="confirmation_check"
            )
            
            return {
                "confirmed": result.passed,
                "confirmation_type": "direct_client",
                "message": result.message
            }
        else:  # Engage = Yes
            # Check for proposal confirmation
            proposal_text = voice_data.get("proposal_confirmation", "")
            expected_proposal = "Proposal ID stated and attributes repeated"
            
            result = self.tool_factory.execute_enhanced_tool(
                "compare_text_semantic",
                "proposal_confirmation_check",
                text_a=expected_proposal,
                text_b=proposal_text,
                comparison_type="confirmation_check"
            )
            
            return {
                "confirmed": result.passed,
                "confirmation_type": "proposal",
                "message": result.message
            }
    
    def check_unapproved_advice(self, order_id: str, trade_inquiry: str) -> Dict[str, Any]:
        """Check if advice was given on unapproved products"""
        voice_data = self.extract_voice_log_data(order_id)
        voice_log_text = voice_data.get("voice_log", "")
        
        result = self.tool_factory.execute_enhanced_tool(
            "compare_text_semantic",
            "advice_detection_check",
            text_a=trade_inquiry,
            text_b=voice_log_text,
            comparison_type="advice_detection"
        )
        
        return {
            "no_advice_given": not result.passed,  # Inverted because we want NO advice
            "message": result.message,
            "confidence": result.details.get("similarity_score", 0)
        }
    
    def check_mfo_advice(self, order_id: str) -> Dict[str, Any]:
        """Check if MFO provided client-specific advice"""
        voice_data = self.extract_voice_log_data(order_id)
        mfo_guidance = voice_data.get("mfo_guidance", "")
        
        # Check if guidance contains client-specific advice
        client_specific_indicators = ["client-specific", "personalized", "individual", "custom"]
        contains_client_advice = any(indicator in mfo_guidance.lower() for indicator in client_specific_indicators)
        
        return {
            "no_client_advice": not contains_client_advice,
            "guidance_text": mfo_guidance,
            "message": "MFO guidance checked for client-specific advice"
        }

class DocManagerAgent:
    """Agent for document management and validation"""
    
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        self.tool_factory = EnhancedToolFactory(llm)
    
    def extract_doc_manager_data(self, order_id: str) -> Dict[str, Any]:
        """Extract document management data"""
        # Mock implementation - in production, this would integrate with document management systems
        return {
            "syndicate_communication": "Syndicate communication sent",
            "bilateral_agreement": "Bilateral agreement signed",
            "a92_document_code": "A92_2025_001",
            "doc_manager": "Document management system active",
            "call_memo": "Call memo recorded",
            "engagement_status": "Engaged",
            "bilateral_agreement_doc": {
                "document_id": "BA_2025_001",
                "signature_date": "2025-10-20",
                "parties": ["Bank", "Client ABC"]
            },
            "scrf_doc": {
                "document_id": "SCRF_2025_001",
                "issue_date": "2025-10-15",
                "issuer": "Securities Commission"
            }
        }
    
    def validate_scrf_dre_documentation(self, order_id: str, order_type: str) -> Dict[str, Any]:
        """Validate SCRF or DRE documentation"""
        if order_type != "FVEQ New Issuance":
            return {"documented": True, "reason": "Not required for this order type"}
        
        doc_data = self.extract_doc_manager_data(order_id)
        scrf_doc = doc_data.get("scrf_doc", {})
        
        result = self.tool_factory.execute_enhanced_tool(
            "validate_document_presence",
            "scrf_dre_validation",
            document_type="SCRF",
            document_data=scrf_doc
        )
        
        return {
            "documented": result.passed,
            "message": result.message,
            "document_details": scrf_doc
        }
    
    def validate_bilateral_agreement(self, order_id: str) -> Dict[str, Any]:
        """Validate bilateral agreement documentation"""
        doc_data = self.extract_doc_manager_data(order_id)
        bilateral_doc = doc_data.get("bilateral_agreement_doc", {})
        
        result = self.tool_factory.execute_enhanced_tool(
            "validate_document_presence",
            "bilateral_agreement_validation",
            document_type="Bilateral Agreement",
            document_data=bilateral_doc
        )
        
        return {
            "documented": result.passed,
            "message": result.message,
            "document_details": bilateral_doc
        }
    
    def check_engagement_status(self, order_id: str) -> Dict[str, Any]:
        """Check engagement status from documents"""
        doc_data = self.extract_doc_manager_data(order_id)
        engagement_text = doc_data.get("engagement_status", "")
        
        result = self.tool_factory.execute_enhanced_tool(
            "classification_check",
            "engagement_status_check",
            text=engagement_text,
            classification_type="engage_status"
        )
        
        return {
            "status": result.details.get("classification", "Unknown"),
            "confidence": result.details.get("confidence", 0),
            "message": result.message
        }

class BrokerageBlotterAgent:
    """Agent for Brokerage Blotter 2.0 data extraction and validation"""
    
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        self.tool_factory = EnhancedToolFactory(llm)
    
    def extract_brokerage_blotter_data(self, order_id: str) -> Dict[str, Any]:
        """Extract data from Brokerage Blotter 2.0"""
        # Mock implementation - in production, this would call Brokerage Blotter APIs
        return {
            "syndicate_allocation": "50% primary, 50% secondary",
            "new_subscription": "Yes",
            "order_taker": "John Smith",
            "order_receipt_date_time": "2025-10-23T14:30:00Z",
            "solicitation_tagging": "Solicited",
            "vl_details": "VL123456",
            "order_taker_name": "John Smith",
            "order_placer_details": "Authorized trader - John Smith",
            "client_profile": "High net worth client profile",
            "trade_ticket": "TKT123456",
            "brokerage_blotter": "Blotter entry completed",
            "trade_blotter": "Trade details recorded",
            "ticket_fields": "All required fields completed",
            "order_type": "FVEQ New Issuance"  # This would be determined by analysis
        }
    
    def validate_order_placer_authorization(self, order_id: str) -> Dict[str, Any]:
        """Validate order placer authorization"""
        blotter_data = self.extract_brokerage_blotter_data(order_id)
        placer_details = blotter_data.get("order_placer_details", "")
        client_profile = blotter_data.get("client_profile", "")
        
        # Check if placer is authorized
        authorized_indicators = ["authorized", "licensed", "certified", "approved"]
        is_authorized = any(indicator in placer_details.lower() for indicator in authorized_indicators)
        
        return {
            "authorized": is_authorized,
            "placer_details": placer_details,
            "client_profile": client_profile,
            "message": f"Order placer {'is' if is_authorized else 'is not'} authorized"
        }
    
    def validate_syndicate_allocation(self, order_id: str, order_type: str) -> Dict[str, Any]:
        """Validate syndicate allocation for FVEQ New Issuance"""
        if order_type != "FVEQ New Issuance":
            return {"correct": True, "reason": "Not applicable for this order type"}
        
        blotter_data = self.extract_brokerage_blotter_data(order_id)
        allocation = blotter_data.get("syndicate_allocation", "")
        
        # Check if allocation is properly formatted
        has_percentages = "%" in allocation
        has_primary_secondary = "primary" in allocation.lower() and "secondary" in allocation.lower()
        
        return {
            "correct": has_percentages and has_primary_secondary,
            "allocation": allocation,
            "message": f"Syndicate allocation {'is' if has_percentages and has_primary_secondary else 'is not'} properly formatted"
        }
    
    def validate_new_subscription_status(self, order_id: str, order_type: str) -> Dict[str, Any]:
        """Validate new subscription status for FI New Issuance"""
        if order_type != "FI New Issuance":
            return {"correct": True, "reason": "Not applicable for this order type"}
        
        blotter_data = self.extract_brokerage_blotter_data(order_id)
        subscription_status = blotter_data.get("new_subscription", "")
        
        return {
            "correct": subscription_status.lower() in ["yes", "no"],
            "status": subscription_status,
            "message": f"New subscription status {'is' if subscription_status.lower() in ['yes', 'no'] else 'is not'} valid"
        }
    
    def validate_trade_solicitation(self, order_id: str) -> Dict[str, Any]:
        """Validate trade solicitation documentation"""
        blotter_data = self.extract_brokerage_blotter_data(order_id)
        solicitation_tagging = blotter_data.get("solicitation_tagging", "")
        
        return {
            "documented": solicitation_tagging.lower() in ["solicited", "unsolicited"],
            "tagging": solicitation_tagging,
            "message": f"Trade solicitation {'is' if solicitation_tagging.lower() in ['solicited', 'unsolicited'] else 'is not'} properly tagged"
        }
    
    def validate_trade_documentation(self, order_id: str) -> Dict[str, Any]:
        """Validate trade documentation completeness"""
        blotter_data = self.extract_brokerage_blotter_data(order_id)
        
        required_fields = ["vl_details", "trade_ticket", "brokerage_blotter", "ticket_fields"]
        
        result = self.tool_factory.execute_enhanced_tool(
            "field_completeness_check",
            "trade_documentation_check",
            data=blotter_data,
            required_fields=required_fields
        )
        
        return {
            "complete_and_accurate": result.passed,
            "message": result.message,
            "details": result.details
        }

class ACESAgent:
    """Agent for ACES system validation"""
    
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        self.tool_factory = EnhancedToolFactory(llm)
    
    def extract_aces_data(self, order_id: str) -> Dict[str, Any]:
        """Extract ACES data"""
        # Mock implementation - in production, this would integrate with ACES system
        return {
            "control_tab_questions": "All control questions answered",
            "all_reviews_tab_questions": "Review questions completed",
            "language_tab": "English language selected",
            "productivity_tab": "Productivity metrics recorded",
            "aces_completeness": {
                "control_tab": True,
                "reviews_tab": True,
                "language_tab": True,
                "productivity_tab": True
            }
        }
    
    def validate_aces_completeness(self, order_id: str) -> Dict[str, Any]:
        """Validate that all required ACES fields are complete"""
        aces_data = self.extract_aces_data(order_id)
        completeness_data = aces_data.get("aces_completeness", {})
        
        required_fields = ["control_tab", "reviews_tab", "language_tab", "productivity_tab"]
        
        result = self.tool_factory.execute_enhanced_tool(
            "field_completeness_check",
            "aces_completeness_check",
            data=completeness_data,
            required_fields=required_fields
        )
        
        return {
            "complete": result.passed,
            "message": result.message,
            "details": result.details
        }

class SCRIBEAgent:
    """Agent for SCRIBE system validation"""
    
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        self.tool_factory = EnhancedToolFactory(llm)
    
    def extract_scribe_data(self, order_id: str) -> Dict[str, Any]:
        """Extract SCRIBE data"""
        # Mock implementation - in production, this would integrate with SCRIBE system
        return {
            "resource_navigation_awm": "AWM navigation completed",
            "aces_disable_replace_process": "ACES disable process executed",
            "aces_error_identification_communication": "Error identification completed",
            "remediation_logs": "All remediation steps completed successfully"
        }
    
    def validate_scribe_processes(self, order_id: str) -> Dict[str, Any]:
        """Validate SCRIBE processes completion"""
        scribe_data = self.extract_scribe_data(order_id)
        
        required_processes = [
            "resource_navigation_awm",
            "aces_disable_replace_process", 
            "aces_error_identification_communication"
        ]
        
        result = self.tool_factory.execute_enhanced_tool(
            "field_completeness_check",
            "scribe_processes_check",
            data=scribe_data,
            required_fields=required_processes
        )
        
        return {
            "processes_complete": result.passed,
            "message": result.message,
            "details": result.details
        }
