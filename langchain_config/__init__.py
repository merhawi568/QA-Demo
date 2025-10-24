"""
LangChain-based QA Pipeline Package

This package provides a complete LangChain-based implementation of the QA pipeline
that can work alongside the existing deterministic pipeline.

Components:
- schemas: Data schemas and configurations
- session_memory: Session state management
- generic_tools: Configurable test tools
- agents: LangChain agents for orchestration, data extraction, test management, and execution
- langchain_pipeline: Main pipeline coordinator
"""

from .schemas import (
    TicketType, DataSource, TestType, OperationType,
    TicketTypeSchema, DataExtractionSchema, APIConfigSchema,
    TestToolConfig, TestDAGNode, TestDAGSchema, SessionMemorySchema,
    DEFAULT_TICKET_TYPE_SCHEMAS, DEFAULT_DATA_EXTRACTION_SCHEMAS,
    DEFAULT_API_CONFIGS, DEFAULT_TEST_DAGS
)

from .session_memory import SessionMemoryManager, session_manager

from .generic_tools import (
    ToolResult, CompareTool, DateRangeTool, ValidationTool, GenericToolFactory
)

from .agents.orchestration_agent import OrchestrationAgent
from .agents.data_agent import DataAgent
from .agents.test_management_agent import TestManagementAgent
from .agents.test_execution_agent import TestExecutionAgent

from .langchain_pipeline import LangChainPipeline, create_langchain_pipeline

__version__ = "1.0.0"
__author__ = "QA Demo Team"

__all__ = [
    # Schemas
    "TicketType", "DataSource", "TestType", "OperationType",
    "TicketTypeSchema", "DataExtractionSchema", "APIConfigSchema",
    "TestToolConfig", "TestDAGNode", "TestDAGSchema", "SessionMemorySchema",
    "DEFAULT_TICKET_TYPE_SCHEMAS", "DEFAULT_DATA_EXTRACTION_SCHEMAS",
    "DEFAULT_API_CONFIGS", "DEFAULT_TEST_DAGS",
    
    # Session Management
    "SessionMemoryManager", "session_manager",
    
    # Generic Tools
    "ToolResult", "CompareTool", "DateRangeTool", "ValidationTool", "GenericToolFactory",
    
    # Agents
    "OrchestrationAgent", "DataAgent", "TestManagementAgent", "TestExecutionAgent",
    
    # Main Pipeline
    "LangChainPipeline", "create_langchain_pipeline"
]
