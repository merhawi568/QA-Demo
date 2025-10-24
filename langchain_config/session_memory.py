"""
Session Memory Manager for the LangChain-based QA pipeline.
Manages state, extracted data, and test results throughout the workflow.
"""

import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from langchain_config.schemas import SessionMemorySchema, TicketType

@dataclass
class SessionMemory:
    """In-memory session storage for workflow state"""
    session_id: str
    ticket_id: str
    ticket_type: Optional[TicketType] = None
    extracted_data: Dict[str, Any] = None
    test_results: Dict[str, Any] = None
    execution_status: str = "pending"
    created_at: str = None
    updated_at: str = None
    
    def __post_init__(self):
        if self.extracted_data is None:
            self.extracted_data = {}
        if self.test_results is None:
            self.test_results = {}
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        if self.updated_at is None:
            self.updated_at = datetime.now().isoformat()

class SessionMemoryManager:
    """Manages session memory for the QA pipeline"""
    
    def __init__(self):
        self.sessions: Dict[str, SessionMemory] = {}
    
    def create_session(self, ticket_id: str, ticket_type: Optional[TicketType] = None) -> str:
        """Create a new session for a ticket"""
        session_id = str(uuid.uuid4())
        session = SessionMemory(
            session_id=session_id,
            ticket_id=ticket_id,
            ticket_type=ticket_type
        )
        self.sessions[session_id] = session
        return session_id
    
    def get_session(self, session_id: str) -> Optional[SessionMemory]:
        """Get session by ID"""
        return self.sessions.get(session_id)
    
    def update_ticket_type(self, session_id: str, ticket_type: TicketType) -> bool:
        """Update the ticket type for a session"""
        session = self.get_session(session_id)
        if session:
            session.ticket_type = ticket_type
            session.updated_at = datetime.now().isoformat()
            return True
        return False
    
    def store_extracted_data(self, session_id: str, data_source: str, data: Dict[str, Any]) -> bool:
        """Store extracted data from a specific source"""
        session = self.get_session(session_id)
        if session:
            if data_source not in session.extracted_data:
                session.extracted_data[data_source] = {}
            session.extracted_data[data_source].update(data)
            session.updated_at = datetime.now().isoformat()
            return True
        return False
    
    def get_extracted_data(self, session_id: str, data_source: Optional[str] = None) -> Dict[str, Any]:
        """Get extracted data, optionally filtered by source"""
        session = self.get_session(session_id)
        if not session:
            return {}
        
        if data_source:
            return session.extracted_data.get(data_source, {})
        return session.extracted_data
    
    def store_test_result(self, session_id: str, test_id: str, result: Dict[str, Any]) -> bool:
        """Store test execution result"""
        session = self.get_session(session_id)
        if session:
            session.test_results[test_id] = {
                **result,
                "timestamp": datetime.now().isoformat()
            }
            session.updated_at = datetime.now().isoformat()
            return True
        return False
    
    def get_test_result(self, session_id: str, test_id: str) -> Optional[Dict[str, Any]]:
        """Get specific test result"""
        session = self.get_session(session_id)
        if session:
            return session.test_results.get(test_id)
        return None
    
    def get_all_test_results(self, session_id: str) -> Dict[str, Any]:
        """Get all test results for a session"""
        session = self.get_session(session_id)
        if session:
            return session.test_results
        return {}
    
    def update_execution_status(self, session_id: str, status: str) -> bool:
        """Update the execution status of a session"""
        session = self.get_session(session_id)
        if session:
            session.execution_status = status
            session.updated_at = datetime.now().isoformat()
            return True
        return False
    
    def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """Get a summary of the session state"""
        session = self.get_session(session_id)
        if not session:
            return {}
        
        return {
            "session_id": session.session_id,
            "ticket_id": session.ticket_id,
            "ticket_type": session.ticket_type,
            "execution_status": session.execution_status,
            "data_sources": list(session.extracted_data.keys()),
            "completed_tests": list(session.test_results.keys()),
            "created_at": session.created_at,
            "updated_at": session.updated_at
        }
    
    def clear_session(self, session_id: str) -> bool:
        """Clear a session from memory"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False
    
    def list_sessions(self) -> List[Dict[str, Any]]:
        """List all active sessions"""
        return [self.get_session_summary(session_id) for session_id in self.sessions.keys()]
    
    def export_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Export session data as dictionary"""
        session = self.get_session(session_id)
        if session:
            return asdict(session)
        return None
    
    def import_session(self, session_data: Dict[str, Any]) -> bool:
        """Import session data from dictionary"""
        try:
            session = SessionMemory(**session_data)
            self.sessions[session.session_id] = session
            return True
        except Exception:
            return False

# Global session memory manager instance
session_manager = SessionMemoryManager()
