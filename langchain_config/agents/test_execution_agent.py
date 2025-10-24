"""
Test Execution Agent for the LangChain-based QA pipeline.
Executes individual tests using generic tools and manages test results.
"""

from typing import Dict, Any, Optional, List
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.tools import BaseTool
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_config.generic_tools import GenericToolFactory, ToolResult
from langchain_config.schemas import TestType, OperationType
from langchain_config.session_memory import session_manager
import json
import time
from datetime import datetime

class TestExecutionTool(BaseTool):
    """Tool for executing individual tests"""
    
    name = "execute_test"
    description = "Execute a specific test using the appropriate generic tool"
    
    def _run(self, test_id: str, tool_config: Dict[str, Any], session_id: str) -> str:
        """Execute a test with the given configuration"""
        try:
            # Get extracted data from session
            extracted_data = session_manager.get_extracted_data(session_id)
            
            # Extract test parameters
            tool_type = TestType(tool_config["tool_type"])
            operation = OperationType(tool_config["operation"])
            parameters = tool_config.get("parameters", {})
            
            # Get data for the test based on tool type
            test_data = self._prepare_test_data(tool_type, extracted_data, parameters)
            
            # Execute the test
            if tool_type in [TestType.COMPARE, TestType.EQUALITY_CHECK, TestType.ROUNDED_EQUALITY]:
                # These tools require two data values
                data_a = test_data.get("data_a")
                data_b = test_data.get("data_b")
                result = GenericToolFactory.execute_tool(
                    tool_type, test_id, data_a, operation, parameters, data_b
                )
            else:
                # Single data value tools
                data = test_data.get("data")
                result = GenericToolFactory.execute_tool(
                    tool_type, test_id, data, operation, parameters
                )
            
            # Store result in session
            session_manager.store_test_result(session_id, test_id, result.to_dict())
            
            return json.dumps({
                "success": True,
                "test_id": test_id,
                "result": result.to_dict()
            })
        
        except Exception as e:
            error_result = ToolResult(
                test_id=test_id,
                passed=False,
                message=f"Test execution failed: {str(e)}"
            )
            
            # Store error result
            session_manager.store_test_result(session_id, test_id, error_result.to_dict())
            
            return json.dumps({
                "success": False,
                "test_id": test_id,
                "error": str(e),
                "result": error_result.to_dict()
            })
    
    def _prepare_test_data(self, tool_type: TestType, extracted_data: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare test data based on tool type and parameters"""
        try:
            if tool_type == TestType.COMPARE:
                # For comparison tests, we need two data values
                data_a_source = parameters.get("data_source_a", "connect_data")
                data_b_source = parameters.get("data_source_b", "doc_manager_data")
                fields_a = parameters.get("fields_a", ["global_fee_transparency"])
                fields_b = parameters.get("fields_b", ["engagement_status"])
                
                # Extract first field from each source for comparison
                data_a = self._extract_field_value(extracted_data, data_a_source, fields_a[0])
                data_b = self._extract_field_value(extracted_data, data_b_source, fields_b[0])
                
                return {"data_a": data_a, "data_b": data_b}
            
            elif tool_type == TestType.DATE_RANGE_CHECK:
                # For date range tests, we need a date value
                data_source = parameters.get("data_source", "connect_data")
                fields = parameters.get("fields", ["execution_timestamps"])
                date_value = self._extract_field_value(extracted_data, data_source, fields[0])
                
                return {"data": date_value}
            
            elif tool_type == TestType.VALIDATE_PRESENCE:
                # For presence validation, we need to check specific fields
                data_source = parameters.get("data_source", "connect_data")
                fields = parameters.get("fields", ["order_id"])
                
                # Check if any of the required fields exist
                field_values = []
                for field in fields:
                    try:
                        value = self._extract_field_value(extracted_data, data_source, field)
                        field_values.append(value)
                    except:
                        field_values.append(None)
                
                # Return the first non-null field value or None
                for value in field_values:
                    if value is not None:
                        return {"data": value}
                
                return {"data": None}
            
            else:
                # Default case - try to extract a single value
                data_source = parameters.get("data_source", "connect_data")
                fields = parameters.get("fields", ["order_id"])
                field_value = self._extract_field_value(extracted_data, data_source, fields[0])
                
                return {"data": field_value}
        
        except Exception as e:
            raise Exception(f"Failed to prepare test data: {str(e)}")
    
    def _extract_field_value(self, extracted_data: Dict[str, Any], source: str, field: str) -> Any:
        """Extract a field value from extracted data"""
        try:
            if source not in extracted_data:
                raise ValueError(f"Data source {source} not found in extracted data")
            
            source_data = extracted_data[source]
            if not isinstance(source_data, dict) or "data" not in source_data:
                raise ValueError(f"Invalid data structure for source {source}")
            
            data = source_data["data"]
            if field not in data:
                raise ValueError(f"Field {field} not found in source {source}")
            
            return data[field]
        
        except Exception as e:
            raise Exception(f"Failed to extract field {field} from {source}: {str(e)}")

class TestExecutionAgent:
    """Test execution agent that runs individual tests using generic tools"""
    
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        self.tools = [TestExecutionTool()]
        self._setup_agent()
    
    def _setup_agent(self):
        """Setup the LangChain agent with tools and prompt"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a test execution agent for a QA pipeline. Your responsibilities are:

1. Execute individual tests using the appropriate generic tools
2. Handle test timeouts and retries
3. Manage test data preparation and validation
4. Store test results in session memory

You have access to the following tools:
- execute_test: Execute a specific test with given configuration

Always use the execute_test tool to run tests and ensure results are properly stored."""),
            ("human", "Execute test: {test_info}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
        
        agent = create_openai_tools_agent(self.llm, self.tools, prompt)
        self.agent_executor = AgentExecutor(agent=agent, tools=self.tools, verbose=True)
    
    def execute_test(self, session_id: str, test_info: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single test"""
        try:
            test_id = test_info["test_id"]
            tool_config = test_info["tool_config"]
            timeout = test_info.get("timeout", 60)
            retry_count = test_info.get("retry_count", 0)
            
            # Execute with timeout and retry logic
            result = self._execute_with_retry(session_id, test_id, tool_config, timeout, retry_count)
            
            return result
        
        except Exception as e:
            error_result = {
                "test_id": test_info["test_id"],
                "passed": False,
                "message": f"Test execution failed: {str(e)}",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            
            # Store error result
            session_manager.store_test_result(session_id, test_info["test_id"], error_result)
            
            return error_result
    
    def _execute_with_retry(self, session_id: str, test_id: str, tool_config: Dict[str, Any], 
                           timeout: int, retry_count: int) -> Dict[str, Any]:
        """Execute test with retry logic"""
        last_error = None
        
        for attempt in range(retry_count + 1):
            try:
                # Use the test execution tool
                result = self.tools[0]._run(test_id, tool_config, session_id)
                execution_result = json.loads(result)
                
                if execution_result.get("success", False):
                    return execution_result["result"]
                else:
                    last_error = execution_result.get("error", "Unknown error")
            
            except Exception as e:
                last_error = str(e)
            
            # If not the last attempt, wait before retry
            if attempt < retry_count:
                time.sleep(1)  # Simple retry delay
        
        # All retries failed
        error_result = {
            "test_id": test_id,
            "passed": False,
            "message": f"Test failed after {retry_count + 1} attempts: {last_error}",
            "error": last_error,
            "attempts": retry_count + 1,
            "timestamp": datetime.now().isoformat()
        }
        
        # Store error result
        session_manager.store_test_result(session_id, test_id, error_result)
        
        return error_result
    
    def execute_test_batch(self, session_id: str, test_batch: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Execute a batch of tests (for parallel execution)"""
        results = []
        
        for test_info in test_batch:
            try:
                result = self.execute_test(session_id, test_info)
                results.append(result)
            except Exception as e:
                error_result = {
                    "test_id": test_info["test_id"],
                    "passed": False,
                    "message": f"Batch execution failed: {str(e)}",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
                results.append(error_result)
        
        return results
    
    def get_test_result(self, session_id: str, test_id: str) -> Optional[Dict[str, Any]]:
        """Get the result of a specific test"""
        return session_manager.get_test_result(session_id, test_id)
    
    def get_all_test_results(self, session_id: str) -> Dict[str, Any]:
        """Get all test results for a session"""
        return session_manager.get_all_test_results(session_id)
    
    def get_test_summary(self, session_id: str) -> Dict[str, Any]:
        """Get a summary of test execution results"""
        test_results = self.get_all_test_results(session_id)
        
        if not test_results:
            return {
                "total_tests": 0,
                "passed_tests": 0,
                "failed_tests": 0,
                "success_rate": 0.0,
                "overall_status": "NO_TESTS"
            }
        
        total_tests = len(test_results)
        passed_tests = sum(1 for result in test_results.values() if result.get("passed", False))
        failed_tests = total_tests - passed_tests
        success_rate = passed_tests / total_tests if total_tests > 0 else 0.0
        
        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "success_rate": success_rate,
            "overall_status": "PASS" if failed_tests == 0 else "FAIL",
            "test_details": test_results
        }
