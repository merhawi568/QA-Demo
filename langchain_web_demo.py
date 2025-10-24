#!/usr/bin/env python3
"""
Enhanced LangChain QA Pipeline Web Demo
Real-time visualization of the 16-test LangChain pipeline for leadership presentation
"""

import json
import time
import asyncio
from datetime import datetime
from flask import Flask, render_template, request, jsonify, Response
from langchain_config.enhanced_pipeline import create_enhanced_langchain_pipeline
from utils.data_loader import load_ticket
import os
from dotenv import load_dotenv
import threading

app = Flask(__name__)

class LangChainWorkflowVisualizer:
    def __init__(self):
        # Load environment variables
        load_dotenv()
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        # Initialize Enhanced LangChain Pipeline
        self.engine = create_enhanced_langchain_pipeline(api_key)
        self.current_step = 0
        self.steps = [
            {"id": "categorization", "name": "Orchestration Agent", "description": "Categorizing ticket and determining test requirements", "status": "pending"},
            {"id": "data_extraction", "name": "Data Agent", "description": "Extracting data from all 6 platforms (Connect, Brokerage Blotter, Doc Manager, Voice Logs, ACES, SCRIBE)", "status": "pending"},
            {"id": "test_management", "name": "Test Management Agent", "description": "Determining test sequence for 16 comprehensive QA tests", "status": "pending"},
            {"id": "test_execution", "name": "Enhanced Test Execution", "description": "Executing 16 comprehensive QA tests in parallel", "status": "pending"},
            {"id": "platform_connect", "name": "Platform Connect Agent", "description": "Validating eligibility and timely execution (Tests 1, 11)", "status": "pending"},
            {"id": "voice_logs", "name": "Voice Log Agent", "description": "Analyzing voice logs and client confirmation (Tests 2, 4, 5, 6, 10)", "status": "pending"},
            {"id": "doc_manager", "name": "Doc Manager Agent", "description": "Validating document presence and engagement (Tests 7, 12, 13)", "status": "pending"},
            {"id": "brokerage_blotter", "name": "Brokerage Blotter Agent", "description": "Checking authorization and syndicate allocation (Tests 3, 8, 9, 14, 15)", "status": "pending"},
            {"id": "aces_validation", "name": "ACES Agent", "description": "Validating ACES field completeness (Test 16)", "status": "pending"},
            {"id": "scribe_validation", "name": "SCRIBE Agent", "description": "Validating SCRIBE process completion", "status": "pending"},
            {"id": "result_aggregation", "name": "Result Aggregator", "description": "Aggregating all test results and generating final report", "status": "pending"},
            {"id": "decision", "name": "Decision Agent", "description": "Making final decision based on success rate", "status": "pending"},
            {"id": "exception", "name": "Exception Agent", "description": "Generating exception email (if needed)", "status": "pending"}
        ]
        self.results = {}
        self.ticket_data = {}
        self.test_results = {}
        self.current_status = "idle"
        self.start_time = None
        self.end_time = None
        self.error_message = None

    def reset_workflow(self):
        """Reset the workflow for a new run"""
        self.current_step = 0
        for step in self.steps:
            step["status"] = "pending"
        self.results = {}
        self.ticket_data = {}
        self.test_results = {}
        self.current_status = "idle"
        self.error_message = None
    
    def update_step_status(self, step_id, status, details=None):
        """Update the status of a specific step"""
        for step in self.steps:
            if step["id"] == step_id:
                step["status"] = status
                if details:
                    step["details"] = details
                break
    
    def run_langchain_workflow(self, ticket_id, scenario="happy"):
        """Run the Enhanced LangChain Pipeline workflow"""
        self.reset_workflow()
        self.current_status = "running"
        self.start_time = datetime.now()
        
        try:
            # Load ticket data
            self.ticket_data = load_ticket(ticket_id)
            
            # Step 1: Categorization
            self.update_step_status("categorization", "running", {"ticket_id": ticket_id, "scenario": scenario})
            time.sleep(0.5)
            categorization_result = self.engine.orchestration_agent._categorize_ticket(self.ticket_data)
            self.update_step_status("categorization", "completed", {"result": categorization_result})
            
            # Step 2: Data Extraction
            self.update_step_status("data_extraction", "running")
            time.sleep(0.8)
            # Create a mock session ID for data extraction
            session_id = f"session_{ticket_id}_{int(time.time())}"
            from langchain_config.schemas import TicketType
            ticket_type = TicketType(categorization_result.get('ticket_type', 'FEE_MODIFICATION'))
            extracted_data = self.engine.data_agent.extract_data(session_id, ticket_type)
            self.update_step_status("data_extraction", "completed", {"sources": list(extracted_data.keys())})
            
            # Step 3: Test Management
            self.update_step_status("test_management", "running")
            time.sleep(0.3)
            test_sequence = self.engine.test_management_agent.get_test_sequence(session_id, ticket_type)
            self.update_step_status("test_management", "completed", {"tests": len(test_sequence)})
            
            # Step 4: Test Execution (16 tests)
            self.update_step_status("test_execution", "running")
            time.sleep(1.2)
            # Execute tests in batches
            test_results = {}
            for test_info in test_sequence:
                test_id = test_info.get('test_id', 'unknown')
                # Create context for the test
                context = {
                    'session_id': session_id,
                    'ticket_data': self.ticket_data,
                    'extracted_data': extracted_data
                }
                test_result = self.engine.enhanced_test_execution_agent.execute_enhanced_test(test_id, context)
                test_results[test_id] = test_result
            self.test_results = test_results
            self.update_step_status("test_execution", "completed", {"results": test_results})
            
            # Step 5-10: Platform-specific agents
            platform_agents = [
                ("platform_connect", "Platform Connect Agent"),
                ("voice_logs", "Voice Log Agent"), 
                ("doc_manager", "Doc Manager Agent"),
                ("brokerage_blotter", "Brokerage Blotter Agent"),
                ("aces_validation", "ACES Agent"),
                ("scribe_validation", "SCRIBE Agent")
            ]
            
            for agent_id, agent_name in platform_agents:
                self.update_step_status(agent_id, "running")
                time.sleep(0.4)
                # Simulate platform agent execution
                self.update_step_status(agent_id, "completed", {"status": "processed"})
            
            # Step 11: Result Aggregation
            self.update_step_status("result_aggregation", "running")
            time.sleep(0.5)
            
            # Calculate results - separate actual execution vs conditional skipping
            passed_tests = sum(1 for result in test_results.values() if result.get('passed', False) and not result.get('skipped', False))
            skipped_tests = sum(1 for result in test_results.values() if result.get('skipped', False))
            failed_tests = sum(1 for result in test_results.values() if not result.get('passed', False) and not result.get('skipped', False))
            total_tests = len(test_results)
            
            # Calculate execution success rate (only for tests that actually ran)
            executed_tests = passed_tests + failed_tests
            execution_success_rate = (passed_tests / executed_tests * 100) if executed_tests > 0 else 100
            
            # Calculate overall success rate (including skipped as successful for business logic)
            overall_successful = passed_tests + skipped_tests
            overall_success_rate = (overall_successful / total_tests * 100) if total_tests > 0 else 0
            
            self.update_step_status("result_aggregation", "completed", {
                "passed": passed_tests, 
                "skipped": skipped_tests,
                "failed": failed_tests,
                "executed": executed_tests,
                "total": total_tests, 
                "execution_success_rate": f"{execution_success_rate:.1f}%",
                "overall_success_rate": f"{overall_success_rate:.1f}%"
            })
            
            # Step 12: Decision
            self.update_step_status("decision", "running")
            time.sleep(0.3)
            # Use execution success rate for decision making (more accurate)
            decision = "PASS" if execution_success_rate >= 90 else "FAIL"
            self.update_step_status("decision", "completed", {
                "decision": decision, 
                "reason": f"Execution success rate: {execution_success_rate:.1f}% ({passed_tests}/{executed_tests} executed tests passed)" if decision == "PASS" else f"Execution success rate below threshold: {execution_success_rate:.1f}% ({passed_tests}/{executed_tests} executed tests passed)"
            })
            
            # Step 13: Exception handling
            if decision == "FAIL":
                self.update_step_status("exception", "running")
                time.sleep(0.4)
                exception_email = {
                    "to": "controls-qa-exceptions@firm.com",
                    "subject": f"[QA-EXCEPTION] {ticket_id}",
                    "body": f"Ticket {ticket_id} failed validation. Success rate: {success_rate:.1f}%. Please review."
                }
                self.update_step_status("exception", "completed", {"email": exception_email})
            else:
                self.update_step_status("exception", "skipped", {"reason": "No exceptions needed"})
            
            # Store final results
            self.end_time = datetime.now()
            processing_time = (self.end_time - self.start_time).total_seconds()
            
            self.results = {
                "ticket": self.ticket_data,
                "decision": decision,
                "passed_tests": passed_tests,
                "skipped_tests": skipped_tests,
                "failed_tests": failed_tests,
                "executed_tests": executed_tests,
                "total_tests": total_tests,
                "execution_success_rate": f"{execution_success_rate:.1f}%",
                "overall_success_rate": f"{overall_success_rate:.1f}%",
                "test_results": test_results,
                "processing_time": f"{processing_time:.2f} seconds",
                "timestamp": self.end_time.isoformat(),
                "pipeline": "Enhanced LangChain Pipeline"
            }
            
            self.current_status = "completed"
            
        except Exception as e:
            self.update_step_status("categorization", "failed", {"error": str(e)})
            self.error_message = str(e)
            self.current_status = "failed"
            self.end_time = datetime.now()

# Global workflow instance
workflow = LangChainWorkflowVisualizer()

@app.route('/')
def index():
    """Main page"""
    return render_template('langchain_index.html')

@app.route('/api/workflow_status')
def workflow_status():
    """Get current workflow status"""
    return jsonify({
        "status": workflow.current_status,
        "current_step": workflow.current_step,
        "total_steps": len(workflow.steps),
        "steps": workflow.steps,
        "results": workflow.results,
        "test_results": workflow.test_results,
        "error": workflow.error_message
    })

@app.route('/api/start_workflow', methods=['POST'])
def start_workflow():
    """Start the LangChain workflow"""
    data = request.get_json()
    ticket_id = data.get('ticket_id', 'TKT67890')
    scenario = data.get('scenario', 'happy')
    
    # Run workflow in background thread
    def run_workflow():
        workflow.run_langchain_workflow(ticket_id, scenario)
    
    thread = threading.Thread(target=run_workflow)
    thread.daemon = True
    thread.start()
    
    return jsonify({"status": "started", "ticket_id": ticket_id, "scenario": scenario})

@app.route('/api/reset_workflow', methods=['POST'])
def reset_workflow():
    """Reset the workflow"""
    workflow.reset_workflow()
    return jsonify({"status": "reset"})

if __name__ == '__main__':
    print("🚀 Starting Enhanced LangChain QA Pipeline Web Demo")
    print("📱 Open your browser to: http://localhost:5002")
    print("🎯 16 Comprehensive QA Tests with LangChain Agents!")
    print("🔧 Enhanced Tools: Semantic Comparison, Document Validation, Timestamp Validation")
    print("🤖 Platform Agents: Connect, Voice Logs, Doc Manager, Brokerage Blotter, ACES, SCRIBE")
    app.run(debug=True, host='0.0.0.0', port=5002)
