"""
Data Agent for the LangChain-based QA pipeline.
Handles data extraction from various sources based on ticket type and schemas.
"""

from typing import Dict, Any, Optional, List
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.tools import BaseTool
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_config.schemas import (
    TicketType, DataSource, DEFAULT_DATA_EXTRACTION_SCHEMAS, 
    DEFAULT_API_CONFIGS, DataExtractionSchema, APIConfigSchema
)
from langchain_config.session_memory import session_manager
import json
import requests
from datetime import datetime

class DataExtractionTool(BaseTool):
    """Tool for extracting data from various sources"""
    
    name = "extract_data"
    description = "Extract data from specified sources based on ticket type and data extraction schema"
    
    def _run(self, ticket_type: str, data_sources: List[str], session_id: str) -> str:
        """Extract data from specified sources"""
        try:
            ticket_type_enum = TicketType(ticket_type)
            extraction_schema = DEFAULT_DATA_EXTRACTION_SCHEMAS.get(ticket_type_enum)
            
            if not extraction_schema:
                return json.dumps({
                    "error": f"No extraction schema found for ticket type: {ticket_type}",
                    "extracted_data": {}
                })
            
            extracted_data = {}
            
            # Extract data from each required source
            for data_point in extraction_schema.required_data_points:
                source = DataSource(data_point["source"])
                source_data = self._extract_from_source(source, data_point, session_id)
                extracted_data[data_point["name"]] = source_data
            
            # Store extracted data in session
            for source_name, data in extracted_data.items():
                session_manager.store_extracted_data(session_id, source_name, data)
            
            return json.dumps({
                "success": True,
                "extracted_data": extracted_data,
                "sources_processed": data_sources
            })
        
        except Exception as e:
            return json.dumps({
                "error": str(e),
                "extracted_data": {}
            })
    
    def _extract_from_source(self, source: DataSource, data_point: Dict[str, Any], session_id: str) -> Dict[str, Any]:
        """Extract data from a specific source"""
        try:
            if source == DataSource.CONNECT:
                return self._extract_from_connect(data_point, session_id)
            elif source == DataSource.BROKERAGE_BLOTTER:
                return self._extract_from_brokerage_blotter(data_point, session_id)
            elif source == DataSource.DOC_MANAGER:
                return self._extract_from_doc_manager(data_point, session_id)
            elif source == DataSource.VOICE_LOGS:
                return self._extract_from_voice_logs(data_point, session_id)
            elif source == DataSource.ACES:
                return self._extract_from_aces(data_point, session_id)
            elif source == DataSource.SCRIBE:
                return self._extract_from_scribe(data_point, session_id)
            else:
                return {"error": f"Unsupported data source: {source}"}
        
        except Exception as e:
            return {"error": f"Failed to extract from {source}: {str(e)}"}
    
    def _extract_from_connect(self, data_point: Dict[str, Any], session_id: str) -> Dict[str, Any]:
        """Extract data from Connect platform (mock implementation)"""
        # Get ticket data from session
        ticket_data = session_manager.get_extracted_data(session_id, "ticket")
        order_id = ticket_data.get("ticket_id")  # Using ticket_id as order_id for now
        
        # Mock Connect API call
        api_config = DEFAULT_API_CONFIGS[DataSource.CONNECT]
        endpoint = api_config.endpoints["order_data"].format(order_id=order_id)
        
        # Mock data for Connect platform
        mock_data = {
            "order_id": order_id,
            "trade_inquiry": "Equity trade inquiry for client ABC",
            "order_restrictions": "No restrictions",
            "profile_canvas": "Standard client profile",
            "global_fee_transparency": "Fee structure disclosed",
            "fee_instruct_report": "FEE_INSTRUCT_2025_001",
            "product_type": "Equity",
            "transaction_type": "Buy",
            "execution_timestamps": "2025-10-23T14:35:00Z",
            "order_time": "2025-10-23T14:30:00Z"
        }
        
        # Extract only the required fields
        required_fields = data_point.get("fields", [])
        extracted = {}
        for field in required_fields:
            if field in mock_data:
                extracted[field] = mock_data[field]
        
        return {
            "source": "connect",
            "data": extracted,
            "timestamp": datetime.now().isoformat(),
            "status": "success"
        }
    
    def _extract_from_brokerage_blotter(self, data_point: Dict[str, Any], session_id: str) -> Dict[str, Any]:
        """Extract data from Brokerage Blotter 2.0 (mock implementation)"""
        # Get ticket data from session
        ticket_data = session_manager.get_extracted_data(session_id, "ticket")
        order_id = ticket_data.get("ticket_id")
        
        # Mock Brokerage Blotter API call
        api_config = DEFAULT_API_CONFIGS[DataSource.BROKERAGE_BLOTTER]
        endpoint = api_config.endpoints["syndicate_data"].format(order_id=order_id)
        
        # Mock data for Brokerage Blotter
        mock_data = {
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
            "ticket_fields": "All required fields completed"
        }
        
        # Extract only the required fields
        required_fields = data_point.get("fields", [])
        extracted = {}
        for field in required_fields:
            if field in mock_data:
                extracted[field] = mock_data[field]
        
        return {
            "source": "brokerage_blotter",
            "data": extracted,
            "timestamp": datetime.now().isoformat(),
            "status": "success"
        }
    
    def _extract_from_doc_manager(self, data_point: Dict[str, Any], session_id: str) -> Dict[str, Any]:
        """Extract data from Doc Manager (mock implementation)"""
        # Get ticket data from session
        ticket_data = session_manager.get_extracted_data(session_id, "ticket")
        order_id = ticket_data.get("ticket_id")
        
        # Mock Doc Manager API call
        api_config = DEFAULT_API_CONFIGS[DataSource.DOC_MANAGER]
        endpoint = api_config.endpoints["documents"].format(order_id=order_id)
        
        # Mock data for Doc Manager
        mock_data = {
            "syndicate_communication": "Syndicate communication sent",
            "bilateral_agreement": "Bilateral agreement signed",
            "a92_document_code": "A92_2025_001",
            "doc_manager": "Document management system active",
            "call_memo": "Call memo recorded",
            "engagement_status": "Engage = Yes"
        }
        
        # Extract only the required fields
        required_fields = data_point.get("fields", [])
        extracted = {}
        for field in required_fields:
            if field in mock_data:
                extracted[field] = mock_data[field]
        
        return {
            "source": "doc_manager",
            "data": extracted,
            "timestamp": datetime.now().isoformat(),
            "status": "success"
        }
    
    def _extract_from_voice_logs(self, data_point: Dict[str, Any], session_id: str) -> Dict[str, Any]:
        """Extract data from Voice Logs (mock implementation)"""
        # Get ticket data from session
        ticket_data = session_manager.get_extracted_data(session_id, "ticket")
        order_id = ticket_data.get("ticket_id")
        
        # Mock Voice Logs API call
        api_config = DEFAULT_API_CONFIGS[DataSource.VOICE_LOGS]
        endpoint = api_config.endpoints["client_instructions"].format(order_id=order_id)
        
        # Mock data for Voice Logs
        mock_data = {
            "client_instructions": "Client provided specific instructions for trade execution",
            "fee_communication": "Fee structure communicated to client",
            "standing_bilateral_agreement_communication": "SBA terms discussed",
            "order_confirmation": "Order confirmed with client",
            "order_execution_time": "2025-10-23T14:35:00Z",
            "voice_log_details": "High quality voice recording available",
            "voice_log": "Voice log recorded and stored",
            "client_confirmation": "Client confirmed order details",
            "proposal_confirmation": "Proposal ID stated and attributes repeated",
            "mfo_guidance": "MFO guidance provided without client-specific advice"
        }
        
        # Extract only the required fields
        required_fields = data_point.get("fields", [])
        extracted = {}
        for field in required_fields:
            if field in mock_data:
                extracted[field] = mock_data[field]
        
        return {
            "source": "voice_logs",
            "data": extracted,
            "timestamp": datetime.now().isoformat(),
            "status": "success"
        }
    
    def _extract_from_aces(self, data_point: Dict[str, Any], session_id: str) -> Dict[str, Any]:
        """Extract data from ACES (mock implementation)"""
        # Get ticket data from session
        ticket_data = session_manager.get_extracted_data(session_id, "ticket")
        order_id = ticket_data.get("ticket_id")
        
        # Mock ACES API call
        api_config = DEFAULT_API_CONFIGS[DataSource.ACES]
        endpoint = api_config.endpoints["control_tab"].format(order_id=order_id)
        
        # Mock data for ACES
        mock_data = {
            "control_tab_questions": "All control questions answered",
            "all_reviews_tab_questions": "Review questions completed",
            "language_tab": "English language selected",
            "productivity_tab": "Productivity metrics recorded"
        }
        
        # Extract only the required fields
        required_fields = data_point.get("fields", [])
        extracted = {}
        for field in required_fields:
            if field in mock_data:
                extracted[field] = mock_data[field]
        
        return {
            "source": "aces",
            "data": extracted,
            "timestamp": datetime.now().isoformat(),
            "status": "success"
        }
    
    def _extract_from_scribe(self, data_point: Dict[str, Any], session_id: str) -> Dict[str, Any]:
        """Extract data from SCRIBE (mock implementation)"""
        # Get ticket data from session
        ticket_data = session_manager.get_extracted_data(session_id, "ticket")
        order_id = ticket_data.get("ticket_id")
        
        # Mock SCRIBE API call
        api_config = DEFAULT_API_CONFIGS[DataSource.SCRIBE]
        endpoint = api_config.endpoints["resource_navigation"].format(order_id=order_id)
        
        # Mock data for SCRIBE
        mock_data = {
            "resource_navigation_awm": "AWM navigation completed",
            "aces_disable_replace_process": "ACES disable process executed",
            "aces_error_identification_communication": "Error identification completed"
        }
        
        # Extract only the required fields
        required_fields = data_point.get("fields", [])
        extracted = {}
        for field in required_fields:
            if field in mock_data:
                extracted[field] = mock_data[field]
        
        return {
            "source": "scribe",
            "data": extracted,
            "timestamp": datetime.now().isoformat(),
            "status": "success"
        }

class DataAgent:
    """Data extraction agent that coordinates data gathering from various sources"""
    
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        self.tools = [DataExtractionTool()]
        self._setup_agent()
    
    def _setup_agent(self):
        """Setup the LangChain agent with tools and prompt"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a data extraction agent for a QA pipeline. Your responsibilities are:

1. Extract data from various sources based on ticket type
2. Use the data extraction schemas to determine what data to collect
3. Store extracted data in session memory for use by other agents
4. Handle data extraction errors gracefully

You have access to the following tools:
- extract_data: Extract data from specified sources based on ticket type

Always use the extract_data tool to gather the required data points for the given ticket type."""),
            ("human", "Extract data for ticket type: {ticket_type}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
        
        agent = create_openai_tools_agent(self.llm, self.tools, prompt)
        self.agent_executor = AgentExecutor(agent=agent, tools=self.tools, verbose=True)
    
    def extract_data(self, session_id: str, ticket_type: TicketType) -> Dict[str, Any]:
        """Extract data for the given ticket type"""
        try:
            # Get extraction schema for the ticket type
            extraction_schema = DEFAULT_DATA_EXTRACTION_SCHEMAS.get(ticket_type)
            if not extraction_schema:
                return {
                    "error": f"No extraction schema found for ticket type: {ticket_type}",
                    "extracted_data": {}
                }
            
            # Get data sources to extract from
            data_sources = [source.value for source in extraction_schema.data_sources]
            
            # Use the extraction tool
            result = self.tools[0]._run(ticket_type.value, data_sources, session_id)
            extraction_result = json.loads(result)
            
            # Update session status
            session_manager.update_execution_status(session_id, "data_extraction_complete")
            
            return {
                "session_id": session_id,
                "ticket_type": ticket_type.value,
                "extraction_result": extraction_result,
                "status": "data_extraction_complete"
            }
        
        except Exception as e:
            session_manager.update_execution_status(session_id, "data_extraction_error")
            return {
                "session_id": session_id,
                "error": str(e),
                "status": "data_extraction_error"
            }
    
    def get_extracted_data_summary(self, session_id: str) -> Dict[str, Any]:
        """Get a summary of extracted data for a session"""
        session = session_manager.get_session(session_id)
        if not session:
            return {"error": "Session not found"}
        
        extracted_data = session.extracted_data
        summary = {
            "session_id": session_id,
            "ticket_id": session.ticket_id,
            "data_sources": list(extracted_data.keys()),
            "extraction_status": "complete" if extracted_data else "pending",
            "data_points": {}
        }
        
        # Count data points per source
        for source, data in extracted_data.items():
            if isinstance(data, dict) and "data" in data:
                summary["data_points"][source] = len(data["data"])
            else:
                summary["data_points"][source] = 0
        
        return summary
    
    def validate_extracted_data(self, session_id: str, ticket_type: TicketType) -> Dict[str, Any]:
        """Validate that all required data has been extracted"""
        try:
            extraction_schema = DEFAULT_DATA_EXTRACTION_SCHEMAS.get(ticket_type)
            if not extraction_schema:
                return {
                    "valid": False,
                    "error": f"No extraction schema found for ticket type: {ticket_type}"
                }
            
            session = session_manager.get_session(session_id)
            if not session:
                return {"valid": False, "error": "Session not found"}
            
            extracted_data = session.extracted_data
            validation_results = []
            
            # Check each required data point
            for data_point in extraction_schema.required_data_points:
                source_name = data_point["name"]
                required_fields = data_point.get("fields", [])
                
                if source_name not in extracted_data:
                    validation_results.append({
                        "data_point": source_name,
                        "status": "missing",
                        "message": f"Data point {source_name} not found"
                    })
                    continue
                
                source_data = extracted_data[source_name]
                if not isinstance(source_data, dict) or "data" not in source_data:
                    validation_results.append({
                        "data_point": source_name,
                        "status": "invalid",
                        "message": f"Data point {source_name} has invalid structure"
                    })
                    continue
                
                # Check required fields
                missing_fields = []
                for field in required_fields:
                    if field not in source_data["data"]:
                        missing_fields.append(field)
                
                if missing_fields:
                    validation_results.append({
                        "data_point": source_name,
                        "status": "incomplete",
                        "message": f"Missing fields: {missing_fields}"
                    })
                else:
                    validation_results.append({
                        "data_point": source_name,
                        "status": "complete",
                        "message": "All required fields present"
                    })
            
            # Determine overall validation status
            all_valid = all(result["status"] == "complete" for result in validation_results)
            
            return {
                "valid": all_valid,
                "validation_results": validation_results,
                "summary": {
                    "total_data_points": len(extraction_schema.required_data_points),
                    "complete_data_points": sum(1 for r in validation_results if r["status"] == "complete"),
                    "missing_data_points": sum(1 for r in validation_results if r["status"] == "missing"),
                    "incomplete_data_points": sum(1 for r in validation_results if r["status"] == "incomplete")
                }
            }
        
        except Exception as e:
            return {
                "valid": False,
                "error": str(e)
            }
