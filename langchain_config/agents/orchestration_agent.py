"""
Orchestration Agent for the LangChain-based QA pipeline.
Coordinates the entire workflow, categorizes tickets, and manages the execution flow.
"""

from typing import Dict, Any, Optional, List
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.tools import BaseTool
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import HumanMessage, AIMessage
from langchain_config.schemas import TicketType, DEFAULT_TICKET_TYPE_SCHEMAS
from langchain_config.session_memory import session_manager
import json
import re

class TicketCategorizationTool(BaseTool):
    """Tool for categorizing tickets based on metadata and content"""
    
    name = "categorize_ticket"
    description = "Categorize a ticket based on its metadata and content to determine the test type"
    
    def _run(self, ticket_metadata: Dict[str, Any], ticket_content: str = "") -> str:
        """Categorize the ticket and return the determined ticket type"""
        try:
            # Extract key fields for categorization
            trade_type = ticket_metadata.get("trade_type", "").lower()
            platform = ticket_metadata.get("platform", "").lower()
            ticket_id = ticket_metadata.get("ticket_id", "")
            
            # Score each possible ticket type
            scores = {}
            for ticket_type, schema in DEFAULT_TICKET_TYPE_SCHEMAS.items():
                score = 0.0
                
                # Check metadata patterns
                patterns = schema.metadata_patterns
                for field, values in patterns.items():
                    field_value = ticket_metadata.get(field, "").lower()
                    for pattern in values:
                        if pattern.lower() in field_value:
                            score += 0.3
                
                # Check required fields presence
                required_fields = schema.required_fields
                present_fields = sum(1 for field in required_fields if field in ticket_metadata)
                field_score = present_fields / len(required_fields) if required_fields else 0
                score += field_score * 0.4
                
                # Check content patterns (if provided)
                if ticket_content:
                    content_lower = ticket_content.lower()
                    for pattern in ["fee", "rate", "modification", "change"]:
                        if pattern in content_lower and ticket_type == TicketType.FEE_MODIFICATION:
                            score += 0.1
                        elif pattern in content_lower and ticket_type == TicketType.ACCOUNT_OPENING:
                            score += 0.05
                
                scores[ticket_type] = score
            
            # Find the best match
            best_type = max(scores.items(), key=lambda x: x[1])
            confidence = best_type[1]
            
            if confidence >= DEFAULT_TICKET_TYPE_SCHEMAS[best_type[0]].confidence_threshold:
                return json.dumps({
                    "ticket_type": best_type[0].value,
                    "confidence": confidence,
                    "reasoning": f"Matched patterns with {confidence:.2f} confidence"
                })
            else:
                return json.dumps({
                    "ticket_type": TicketType.FEE_MODIFICATION.value,  # Default fallback
                    "confidence": confidence,
                    "reasoning": f"Low confidence ({confidence:.2f}), using default type"
                })
        
        except Exception as e:
            return json.dumps({
                "ticket_type": TicketType.FEE_MODIFICATION.value,
                "confidence": 0.0,
                "reasoning": f"Error during categorization: {str(e)}"
            })

class OrchestrationAgent:
    """Main orchestration agent that coordinates the QA workflow"""
    
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        self.tools = [TicketCategorizationTool()]
        self._setup_agent()
    
    def _setup_agent(self):
        """Setup the LangChain agent with tools and prompt"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an orchestration agent for a QA pipeline. Your responsibilities are:

1. Categorize tickets based on their metadata and content
2. Coordinate data extraction by calling the data agent
3. Manage test execution by calling the test management agent
4. Monitor overall workflow progress and handle exceptions

You have access to the following tools:
- categorize_ticket: Categorize a ticket to determine its test type

Always use the categorize_ticket tool first to determine the ticket type, then proceed with the appropriate workflow steps.

Current session context will be provided in the conversation history."""),
            ("human", "Process this ticket: {ticket_data}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
        
        agent = create_openai_tools_agent(self.llm, self.tools, prompt)
        self.agent_executor = AgentExecutor(agent=agent, tools=self.tools, verbose=True)
    
    def process_ticket(self, ticket_data: Dict[str, Any], session_id: str) -> Dict[str, Any]:
        """Process a ticket through the orchestration workflow"""
        try:
            # Update session with ticket data
            session_manager.store_extracted_data(session_id, "ticket", ticket_data)
            
            # Categorize the ticket
            categorization_result = self._categorize_ticket(ticket_data)
            ticket_type = TicketType(categorization_result["ticket_type"])
            
            # Update session with ticket type
            session_manager.update_ticket_type(session_id, ticket_type)
            session_manager.update_execution_status(session_id, "categorization_complete")
            
            # Prepare result
            result = {
                "session_id": session_id,
                "ticket_id": ticket_data.get("ticket_id"),
                "ticket_type": ticket_type.value,
                "categorization": categorization_result,
                "status": "categorization_complete",
                "next_steps": [
                    "Call data agent to extract required data",
                    "Call test management agent to determine test sequence",
                    "Execute tests in the determined order"
                ]
            }
            
            return result
        
        except Exception as e:
            session_manager.update_execution_status(session_id, "error")
            return {
                "session_id": session_id,
                "ticket_id": ticket_data.get("ticket_id"),
                "error": str(e),
                "status": "error"
            }
    
    def _categorize_ticket(self, ticket_data: Dict[str, Any]) -> Dict[str, Any]:
        """Categorize a ticket using the categorization tool"""
        try:
            # Extract metadata and content
            metadata = {k: v for k, v in ticket_data.items() if k != "content"}
            content = ticket_data.get("content", "")
            
            # Use the categorization tool
            result = self.tools[0]._run(metadata, content)
            return json.loads(result)
        
        except Exception as e:
            return {
                "ticket_type": TicketType.FEE_MODIFICATION.value,
                "confidence": 0.0,
                "reasoning": f"Error during categorization: {str(e)}"
            }
    
    def coordinate_data_extraction(self, session_id: str, data_agent) -> Dict[str, Any]:
        """Coordinate data extraction with the data agent"""
        try:
            session = session_manager.get_session(session_id)
            if not session:
                return {"error": "Session not found"}
            
            ticket_type = session.ticket_type
            if not ticket_type:
                return {"error": "Ticket type not determined"}
            
            # Call data agent to extract required data
            extraction_result = data_agent.extract_data(session_id, ticket_type)
            
            # Update session status
            session_manager.update_execution_status(session_id, "data_extraction_complete")
            
            return {
                "session_id": session_id,
                "status": "data_extraction_complete",
                "extraction_result": extraction_result
            }
        
        except Exception as e:
            session_manager.update_execution_status(session_id, "data_extraction_error")
            return {
                "session_id": session_id,
                "error": str(e),
                "status": "data_extraction_error"
            }
    
    def coordinate_test_execution(self, session_id: str, test_management_agent, test_execution_agent) -> Dict[str, Any]:
        """Coordinate test execution with test management and execution agents"""
        try:
            session = session_manager.get_session(session_id)
            if not session:
                return {"error": "Session not found"}
            
            ticket_type = session.ticket_type
            if not ticket_type:
                return {"error": "Ticket type not determined"}
            
            # Get test sequence from test management agent
            test_sequence = test_management_agent.get_test_sequence(session_id, ticket_type)
            
            # Execute tests
            execution_results = []
            for test_node in test_sequence:
                test_result = test_execution_agent.execute_test(session_id, test_node)
                execution_results.append(test_result)
                
                # Store result in session
                session_manager.store_test_result(session_id, test_node["test_id"], test_result)
            
            # Update session status
            session_manager.update_execution_status(session_id, "test_execution_complete")
            
            return {
                "session_id": session_id,
                "status": "test_execution_complete",
                "test_results": execution_results,
                "summary": self._generate_execution_summary(execution_results)
            }
        
        except Exception as e:
            session_manager.update_execution_status(session_id, "test_execution_error")
            return {
                "session_id": session_id,
                "error": str(e),
                "status": "test_execution_error"
            }
    
    def _generate_execution_summary(self, test_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate a summary of test execution results"""
        total_tests = len(test_results)
        passed_tests = sum(1 for result in test_results if result.get("passed", False))
        failed_tests = total_tests - passed_tests
        
        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "success_rate": passed_tests / total_tests if total_tests > 0 else 0,
            "overall_status": "PASS" if failed_tests == 0 else "FAIL"
        }
    
    def get_workflow_status(self, session_id: str) -> Dict[str, Any]:
        """Get the current status of the workflow for a session"""
        session = session_manager.get_session(session_id)
        if not session:
            return {"error": "Session not found"}
        
        return {
            "session_id": session_id,
            "ticket_id": session.ticket_id,
            "ticket_type": session.ticket_type.value if session.ticket_type else None,
            "execution_status": session.execution_status,
            "data_sources": list(session.extracted_data.keys()),
            "completed_tests": list(session.test_results.keys()),
            "created_at": session.created_at,
            "updated_at": session.updated_at
        }
