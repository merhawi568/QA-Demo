"""
Enhanced LangChain Pipeline with specialized platform agents and orchestration.
Uses the new platform agents and enhanced tools for more sophisticated test execution.
"""

from typing import Dict, Any, Optional, List
from langchain_openai import ChatOpenAI
from langchain_config.agents.orchestration_agent import OrchestrationAgent
from langchain_config.agents.data_agent import DataAgent
from langchain_config.agents.test_management_agent import TestManagementAgent
from langchain_config.orchestration_agents import EnhancedTestExecutionAgent
from langchain_config.session_memory import session_manager
from langchain_config.schemas import TicketType
import json
import time
from datetime import datetime

class EnhancedLangChainPipeline:
    """Enhanced pipeline using specialized platform agents and orchestration"""
    
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        self.orchestration_agent = OrchestrationAgent(llm)
        self.data_agent = DataAgent(llm)
        self.test_management_agent = TestManagementAgent(llm)
        self.enhanced_test_execution_agent = EnhancedTestExecutionAgent(llm)
    
    def process_ticket(self, ticket_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a ticket through the enhanced LangChain pipeline"""
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
            
            # Step 4: Enhanced Test Execution
            print(f"⚡ Step 4: Executing enhanced tests")
            execution_results = []
            
            # Prepare context for enhanced test execution
            context = self._prepare_execution_context(ticket_data, data_result)
            
            for test_info in test_sequence:
                print(f"  Running test: {test_info['test_id']}")
                test_result = self.enhanced_test_execution_agent.execute_enhanced_test(
                    test_info['test_id'], context
                )
                execution_results.append(test_result)
                
                status = "✅ PASS" if test_result.get("passed", False) else "❌ FAIL"
                print(f"    {status}: {test_result.get('message', 'No message')}")
            
            # Step 5: Generate final summary
            print(f"📋 Step 5: Generating final summary")
            final_summary = self._generate_enhanced_summary(session_id, execution_results, context)
            
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
    
    def _prepare_execution_context(self, ticket_data: Dict[str, Any], data_result: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare context for enhanced test execution"""
        try:
            # Extract key data from the data extraction result
            extracted_data = data_result.get("extracted_data", {})
            
            # Get Connect data for context
            connect_data = extracted_data.get("connect_data", {})
            brokerage_data = extracted_data.get("brokerage_blotter_data", {})
            voice_data = extracted_data.get("voice_logs_data", {})
            doc_data = extracted_data.get("doc_manager_data", {})
            
            context = {
                "order_id": ticket_data.get("ticket_id", ""),
                "product_type": connect_data.get("product_type", "Equity"),
                "transaction_type": connect_data.get("transaction_type", "Buy"),
                "order_type": brokerage_data.get("order_type", "FVEQ New Issuance"),
                "engage_status": connect_data.get("engage_status", "Engage = Yes"),  # Default to Yes for testing
                "order_time": connect_data.get("order_time", "2025-10-23T14:30:00Z"),
                "execution_time": connect_data.get("execution_timestamps", "2025-10-23T14:35:00Z"),
                "trade_inquiry": connect_data.get("trade_inquiry", ""),
                "order_taker_type": "MFO" if "MFO" in voice_data.get("mfo_guidance", "") else "Regular",
                "product_class": connect_data.get("product_type", "Equity")
            }
            
            return context
        
        except Exception as e:
            return {
                "order_id": ticket_data.get("ticket_id", ""),
                "product_type": "Equity",
                "transaction_type": "Buy",
                "order_type": "FVEQ New Issuance",
                "engage_status": "Engage = No"
            }
    
    def _generate_enhanced_summary(self, session_id: str, execution_results: List[Dict[str, Any]], 
                                 context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate an enhanced summary of the workflow execution"""
        try:
            # Calculate test statistics
            total_tests = len(execution_results)
            passed_tests = sum(1 for result in execution_results if result.get("passed", False))
            failed_tests = total_tests - passed_tests
            success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
            
            # Categorize results by test type
            test_categories = {}
            for result in execution_results:
                test_id = result.get("test_id", "")
                category = self._categorize_test(test_id)
                if category not in test_categories:
                    test_categories[category] = {"passed": 0, "failed": 0, "total": 0}
                
                test_categories[category]["total"] += 1
                if result.get("passed", False):
                    test_categories[category]["passed"] += 1
                else:
                    test_categories[category]["failed"] += 1
            
            # Get session summary
            session_summary = session_manager.get_session_summary(session_id)
            
            # Determine overall status
            overall_status = "PASS" if failed_tests == 0 else "FAIL"
            
            # Generate detailed test results
            detailed_results = []
            for result in execution_results:
                detailed_results.append({
                    "test_id": result.get("test_id", ""),
                    "status": "PASS" if result.get("passed", False) else "FAIL",
                    "message": result.get("message", ""),
                    "objective": result.get("objective", ""),
                    "sop_reference": result.get("sop_reference", ""),
                    "primary_platform": result.get("primary_platform", ""),
                    "details": result.get("details", {})
                })
            
            return {
                "overall_status": overall_status,
                "ticket_id": session_summary["ticket_id"],
                "ticket_type": session_summary["ticket_type"],
                "execution_status": session_summary["execution_status"],
                "test_statistics": {
                    "total_tests": total_tests,
                    "passed_tests": passed_tests,
                    "failed_tests": failed_tests,
                    "success_rate": round(success_rate, 2)
                },
                "test_categories": test_categories,
                "detailed_results": detailed_results,
                "context": context,
                "session_info": session_summary,
                "timestamp": datetime.now().isoformat()
            }
        
        except Exception as e:
            return {
                "overall_status": "ERROR",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _categorize_test(self, test_id: str) -> str:
        """Categorize a test by its ID"""
        if "eligibility" in test_id:
            return "Eligibility"
        elif "voice_log" in test_id:
            return "Voice Logs"
        elif "authorization" in test_id:
            return "Authorization"
        elif "confirmation" in test_id:
            return "Client Confirmation"
        elif "advice" in test_id:
            return "Advice Validation"
        elif "documentation" in test_id:
            return "Documentation"
        elif "timely" in test_id:
            return "Execution Timing"
        elif "engagement" in test_id:
            return "Engagement Status"
        elif "syndicate" in test_id or "subscription" in test_id:
            return "Allocation & Subscription"
        elif "aces" in test_id:
            return "ACES Completeness"
        else:
            return "Other"
    
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

def create_enhanced_langchain_pipeline(api_key: str, model: str = "gpt-4o") -> EnhancedLangChainPipeline:
    """Factory function to create an enhanced LangChain pipeline"""
    llm = ChatOpenAI(
        model=model,
        temperature=0,
        api_key=api_key
    )
    return EnhancedLangChainPipeline(llm)
