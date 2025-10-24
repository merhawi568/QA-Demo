"""
Test Management Agent for the LangChain-based QA pipeline.
Manages test DAGs, determines test sequences, and handles test dependencies.
"""

from typing import Dict, Any, Optional, List
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.tools import BaseTool
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_config.schemas import (
    TicketType, DEFAULT_TEST_DAGS, TestDAGSchema, TestDAGNode
)
from langchain_config.session_memory import session_manager
import json
from collections import defaultdict, deque

class TestSequenceTool(BaseTool):
    """Tool for determining test execution sequence based on DAG"""
    
    name = "get_test_sequence"
    description = "Get the execution sequence for tests based on ticket type and DAG dependencies"
    
    def _run(self, ticket_type: str, session_id: str) -> str:
        """Get test execution sequence for the given ticket type"""
        try:
            ticket_type_enum = TicketType(ticket_type)
            test_dag = DEFAULT_TEST_DAGS.get(ticket_type_enum)
            
            if not test_dag:
                return json.dumps({
                    "error": f"No test DAG found for ticket type: {ticket_type}",
                    "test_sequence": []
                })
            
            # Calculate execution order based on dependencies
            execution_order = self._calculate_execution_order(test_dag)
            
            # Group tests by execution phase (parallel vs sequential)
            execution_phases = self._group_by_execution_phases(execution_order, test_dag)
            
            return json.dumps({
                "success": True,
                "ticket_type": ticket_type,
                "dag_id": test_dag.dag_id,
                "execution_order": execution_order,
                "execution_phases": execution_phases,
                "total_tests": len(test_dag.nodes),
                "max_parallel": test_dag.max_parallel_tests
            })
        
        except Exception as e:
            return json.dumps({
                "error": str(e),
                "test_sequence": []
            })
    
    def _calculate_execution_order(self, test_dag: TestDAGSchema) -> List[str]:
        """Calculate the execution order based on dependencies using topological sort"""
        # Build dependency graph
        in_degree = defaultdict(int)
        graph = defaultdict(list)
        
        for node in test_dag.nodes:
            in_degree[node.test_id] = 0
            for dep in node.dependencies:
                graph[dep].append(node.test_id)
                in_degree[node.test_id] += 1
        
        # Topological sort
        queue = deque([node for node in in_degree if in_degree[node] == 0])
        execution_order = []
        
        while queue:
            current = queue.popleft()
            execution_order.append(current)
            
            for neighbor in graph[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        # Check for circular dependencies
        if len(execution_order) != len(test_dag.nodes):
            raise ValueError("Circular dependency detected in test DAG")
        
        return execution_order
    
    def _group_by_execution_phases(self, execution_order: List[str], test_dag: TestDAGSchema) -> List[Dict[str, Any]]:
        """Group tests into execution phases based on parallel execution capability"""
        node_map = {node.test_id: node for node in test_dag.nodes}
        phases = []
        current_phase = []
        
        for test_id in execution_order:
            node = node_map[test_id]
            
            if node.parallel_execution:
                current_phase.append({
                    "test_id": test_id,
                    "parallel": True,
                    "dependencies": node.dependencies,
                    "timeout": node.timeout,
                    "retry_count": node.retry_count
                })
            else:
                # If current phase has tests, finalize it
                if current_phase:
                    phases.append({
                        "phase_type": "parallel",
                        "tests": current_phase,
                        "max_parallel": test_dag.max_parallel_tests
                    })
                    current_phase = []
                
                # Add sequential test
                phases.append({
                    "phase_type": "sequential",
                    "tests": [{
                        "test_id": test_id,
                        "parallel": False,
                        "dependencies": node.dependencies,
                        "timeout": node.timeout,
                        "retry_count": node.retry_count
                    }]
                })
        
        # Add remaining parallel tests
        if current_phase:
            phases.append({
                "phase_type": "parallel",
                "tests": current_phase,
                "max_parallel": test_dag.max_parallel_tests
            })
        
        return phases

class TestDependencyTool(BaseTool):
    """Tool for checking test dependencies and readiness"""
    
    name = "check_test_dependencies"
    description = "Check if a test's dependencies are satisfied and it's ready to execute"
    
    def _run(self, test_id: str, session_id: str) -> str:
        """Check if a test is ready to execute based on its dependencies"""
        try:
            # Get test results from session
            test_results = session_manager.get_all_test_results(session_id)
            
            # Get test DAG to find dependencies
            session = session_manager.get_session(session_id)
            if not session or not session.ticket_type:
                return json.dumps({
                    "ready": False,
                    "error": "Session or ticket type not found"
                })
            
            test_dag = DEFAULT_TEST_DAGS.get(session.ticket_type)
            if not test_dag:
                return json.dumps({
                    "ready": False,
                    "error": f"No test DAG found for ticket type: {session.ticket_type}"
                })
            
            # Find the test node
            test_node = None
            for node in test_dag.nodes:
                if node.test_id == test_id:
                    test_node = node
                    break
            
            if not test_node:
                return json.dumps({
                    "ready": False,
                    "error": f"Test {test_id} not found in DAG"
                })
            
            # Check dependencies
            dependency_status = {}
            all_dependencies_met = True
            
            for dep in test_node.dependencies:
                if dep in test_results:
                    dep_result = test_results[dep]
                    dependency_status[dep] = {
                        "completed": True,
                        "passed": dep_result.get("passed", False),
                        "status": "passed" if dep_result.get("passed", False) else "failed"
                    }
                    
                    # If any dependency failed, this test cannot run
                    if not dep_result.get("passed", False):
                        all_dependencies_met = False
                else:
                    dependency_status[dep] = {
                        "completed": False,
                        "passed": False,
                        "status": "pending"
                    }
                    all_dependencies_met = False
            
            return json.dumps({
                "ready": all_dependencies_met,
                "test_id": test_id,
                "dependencies": dependency_status,
                "can_execute": all_dependencies_met
            })
        
        except Exception as e:
            return json.dumps({
                "ready": False,
                "error": str(e)
            })

class TestManagementAgent:
    """Test management agent that handles test DAGs and execution sequencing"""
    
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        self.tools = [TestSequenceTool(), TestDependencyTool()]
        self._setup_agent()
    
    def _setup_agent(self):
        """Setup the LangChain agent with tools and prompt"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a test management agent for a QA pipeline. Your responsibilities are:

1. Determine the correct test sequence based on ticket type and DAG
2. Check test dependencies and readiness
3. Manage test execution phases (parallel vs sequential)
4. Handle test failures and retries

You have access to the following tools:
- get_test_sequence: Get the execution sequence for tests based on ticket type
- check_test_dependencies: Check if a test's dependencies are satisfied

Always use these tools to determine the proper test execution order and check dependencies before execution."""),
            ("human", "Manage tests for ticket type: {ticket_type}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
        
        agent = create_openai_tools_agent(self.llm, self.tools, prompt)
        self.agent_executor = AgentExecutor(agent=agent, tools=self.tools, verbose=True)
    
    def get_test_sequence(self, session_id: str, ticket_type: TicketType) -> List[Dict[str, Any]]:
        """Get the test execution sequence for the given ticket type"""
        try:
            # Use the test sequence tool
            result = self.tools[0]._run(ticket_type.value, session_id)
            sequence_result = json.loads(result)
            
            if "error" in sequence_result:
                return []
            
            # Convert to the format expected by test execution
            test_sequence = []
            node_map = {node.test_id: node for node in DEFAULT_TEST_DAGS[ticket_type].nodes}
            
            for test_id in sequence_result["execution_order"]:
                node = node_map[test_id]
                test_sequence.append({
                    "test_id": test_id,
                    "tool_config": node.tool_config.dict(),
                    "dependencies": node.dependencies,
                    "parallel_execution": node.parallel_execution,
                    "retry_count": node.retry_count,
                    "timeout": node.timeout
                })
            
            return test_sequence
        
        except Exception as e:
            return []
    
    def check_test_readiness(self, session_id: str, test_id: str) -> Dict[str, Any]:
        """Check if a test is ready to execute"""
        try:
            # Use the dependency check tool
            result = self.tools[1]._run(test_id, session_id)
            readiness_result = json.loads(result)
            
            return readiness_result
        
        except Exception as e:
            return {
                "ready": False,
                "error": str(e)
            }
    
    def get_next_executable_tests(self, session_id: str, ticket_type: TicketType) -> List[str]:
        """Get the next tests that can be executed based on current state"""
        try:
            test_sequence = self.get_test_sequence(session_id, ticket_type)
            executable_tests = []
            
            for test_info in test_sequence:
                test_id = test_info["test_id"]
                readiness = self.check_test_readiness(session_id, test_id)
                
                if readiness.get("ready", False):
                    executable_tests.append(test_id)
            
            return executable_tests
        
        except Exception as e:
            return []
    
    def get_execution_phases(self, session_id: str, ticket_type: TicketType) -> List[Dict[str, Any]]:
        """Get the execution phases for the test DAG"""
        try:
            # Use the test sequence tool to get phases
            result = self.tools[0]._run(ticket_type.value, session_id)
            sequence_result = json.loads(result)
            
            if "error" in sequence_result:
                return []
            
            return sequence_result.get("execution_phases", [])
        
        except Exception as e:
            return []
    
    def get_test_summary(self, session_id: str, ticket_type: TicketType) -> Dict[str, Any]:
        """Get a summary of all tests for the ticket type"""
        try:
            test_dag = DEFAULT_TEST_DAGS.get(ticket_type)
            if not test_dag:
                return {"error": f"No test DAG found for ticket type: {ticket_type}"}
            
            test_results = session_manager.get_all_test_results(session_id)
            
            summary = {
                "ticket_type": ticket_type.value,
                "dag_id": test_dag.dag_id,
                "total_tests": len(test_dag.nodes),
                "completed_tests": len(test_results),
                "pending_tests": len(test_dag.nodes) - len(test_results),
                "test_status": {}
            }
            
            # Status of each test
            for node in test_dag.nodes:
                test_id = node.test_id
                if test_id in test_results:
                    result = test_results[test_id]
                    summary["test_status"][test_id] = {
                        "status": "completed",
                        "passed": result.get("passed", False),
                        "message": result.get("message", "")
                    }
                else:
                    readiness = self.check_test_readiness(session_id, test_id)
                    summary["test_status"][test_id] = {
                        "status": "ready" if readiness.get("ready", False) else "pending",
                        "passed": None,
                        "message": "Not yet executed"
                    }
            
            return summary
        
        except Exception as e:
            return {"error": str(e)}
