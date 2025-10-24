"""
Main LangChain Pipeline for QA workflow.
Coordinates all agents and manages the complete workflow execution.
"""

from typing import Dict, Any, Optional, List
from langchain_openai import ChatOpenAI
from langchain_config.agents.orchestration_agent import OrchestrationAgent
from langchain_config.agents.data_agent import DataAgent
from langchain_config.agents.test_management_agent import TestManagementAgent
from langchain_config.agents.test_execution_agent import TestExecutionAgent
from langchain_config.session_memory import session_manager
from langchain_config.schemas import TicketType
import json
import time
from datetime import datetime

class LangChainPipeline:
    """Main pipeline that coordinates all LangChain agents"""
    
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        self.orchestration_agent = OrchestrationAgent(llm)
        self.data_agent = DataAgent(llm)
        self.test_management_agent = TestManagementAgent(llm)
        self.test_execution_agent = TestExecutionAgent(llm)
    
    def process_ticket(self, ticket_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a ticket through the complete LangChain pipeline"""
        try:
            # Create new session
            session_id = session_manager.create_session(
                ticket_id=ticket_data.get("ticket_id", "unknown"),
                ticket_type=None
            )
            
            # Step 1: Orchestration - Categorize ticket
            print(f"🔍 Step 1: Categorizing ticket {ticket_data.get('ticket_id')}")
            categorization_result = self.orchestration_agent.process_ticket(ticket_data, session_id)
            
            if categorization_result.get("status") == "error":
                return {
                    "session_id": session_id,
                    "status": "error",
                    "error": categorization_result.get("error"),
                    "step": "categorization"
                }
            
            ticket_type = TicketType(categorization_result["ticket_type"])
            print(f"✅ Ticket categorized as: {ticket_type.value}")
            
            # Step 2: Data Extraction
            print(f"📊 Step 2: Extracting data for {ticket_type.value}")
            data_result = self.data_agent.extract_data(session_id, ticket_type)
            
            if data_result.get("status") == "error":
                return {
                    "session_id": session_id,
                    "status": "error",
                    "error": data_result.get("error"),
                    "step": "data_extraction"
                }
            
            print(f"✅ Data extraction completed")
            
            # Step 3: Test Management - Get test sequence
            print(f"🧪 Step 3: Determining test sequence for {ticket_type.value}")
            test_sequence = self.test_management_agent.get_test_sequence(session_id, ticket_type)
            
            if not test_sequence:
                return {
                    "session_id": session_id,
                    "status": "error",
                    "error": "No test sequence determined",
                    "step": "test_management"
                }
            
            print(f"✅ Test sequence determined: {len(test_sequence)} tests")
            
            # Step 4: Test Execution
            print(f"⚡ Step 4: Executing tests")
            execution_results = []
            
            for test_info in test_sequence:
                print(f"  Running test: {test_info['test_id']}")
                test_result = self.test_execution_agent.execute_test(session_id, test_info)
                execution_results.append(test_result)
                
                status = "✅ PASS" if test_result.get("passed", False) else "❌ FAIL"
                print(f"    {status}: {test_result.get('message', 'No message')}")
            
            # Step 5: Generate final summary
            print(f"📋 Step 5: Generating final summary")
            final_summary = self._generate_final_summary(session_id, execution_results)
            
            # Update session status
            session_manager.update_execution_status(session_id, "completed")
            
            return {
                "session_id": session_id,
                "status": "completed",
                "ticket_id": ticket_data.get("ticket_id"),
                "ticket_type": ticket_type.value,
                "categorization": categorization_result,
                "data_extraction": data_result,
                "test_sequence": test_sequence,
                "execution_results": execution_results,
                "final_summary": final_summary,
                "workflow_duration": self._calculate_workflow_duration(session_id)
            }
        
        except Exception as e:
            session_manager.update_execution_status(session_id, "error")
            return {
                "session_id": session_id,
                "status": "error",
                "error": str(e),
                "step": "pipeline_execution"
            }
    
    def _generate_final_summary(self, session_id: str, execution_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate a comprehensive summary of the workflow execution"""
        try:
            # Get test execution summary
            test_summary = self.test_execution_agent.get_test_summary(session_id)
            
            # Get data extraction summary
            data_summary = self.data_agent.get_extracted_data_summary(session_id)
            
            # Get session summary
            session_summary = session_manager.get_session_summary(session_id)
            
            # Calculate overall status
            overall_status = "PASS" if test_summary["failed_tests"] == 0 else "FAIL"
            
            return {
                "overall_status": overall_status,
                "ticket_id": session_summary["ticket_id"],
                "ticket_type": session_summary["ticket_type"],
                "execution_status": session_summary["execution_status"],
                "test_summary": test_summary,
                "data_summary": data_summary,
                "session_info": session_summary,
                "timestamp": datetime.now().isoformat()
            }
        
        except Exception as e:
            return {
                "overall_status": "ERROR",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _calculate_workflow_duration(self, session_id: str) -> float:
        """Calculate the total duration of the workflow"""
        try:
            session = session_manager.get_session(session_id)
            if session:
                start_time = datetime.fromisoformat(session.created_at)
                end_time = datetime.fromisoformat(session.updated_at)
                return (end_time - start_time).total_seconds()
            return 0.0
        except Exception:
            return 0.0
    
    def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """Get the current status of a session"""
        return session_manager.get_session_summary(session_id)
    
    def list_active_sessions(self) -> List[Dict[str, Any]]:
        """List all active sessions"""
        return session_manager.list_sessions()
    
    def export_session_data(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Export complete session data"""
        return session_manager.export_session(session_id)
    
    def clear_session(self, session_id: str) -> bool:
        """Clear a session from memory"""
        return session_manager.clear_session(session_id)

def create_langchain_pipeline(api_key: str, model: str = "gpt-4o") -> LangChainPipeline:
    """Factory function to create a LangChain pipeline"""
    llm = ChatOpenAI(
        model=model,
        temperature=0,
        api_key=api_key
    )
    return LangChainPipeline(llm)
