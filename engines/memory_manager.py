import sqlite3
import json
from datetime import datetime

class MemoryManager:
    def __init__(self, db_path: str = "workflow_memory.db"):
        self.conn = sqlite3.connect(db_path)
        self._create_tables()
    
    def _create_tables(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS workflow_runs (
                id INTEGER PRIMARY KEY,
                ticket_id TEXT,
                status TEXT,
                started_at TEXT,
                completed_at TEXT,
                duration REAL
            )
        """)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS agent_outputs (
                id INTEGER PRIMARY KEY,
                run_id INTEGER,
                agent_name TEXT,
                input_data TEXT,
                output_data TEXT,
                timestamp TEXT,
                FOREIGN KEY(run_id) REFERENCES workflow_runs(id)
            )
        """)
        self.conn.commit()
    
    def save_run(self, ticket_id: str, status: str, duration: float) -> int:
        cursor = self.conn.execute("""
            INSERT INTO workflow_runs (ticket_id, status, started_at, completed_at, duration)
            VALUES (?, ?, ?, ?, ?)
        """, (ticket_id, status, datetime.now().isoformat(), 
              datetime.now().isoformat(), duration))
        self.conn.commit()
        return cursor.lastrowid
    
    def save_agent_output(self, run_id: int, agent_name: str, 
                         input_data: dict, output_data: dict):
        self.conn.execute("""
            INSERT INTO agent_outputs (run_id, agent_name, input_data, output_data, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, (run_id, agent_name, json.dumps(input_data), 
              json.dumps(output_data), datetime.now().isoformat()))
        self.conn.commit()
    
    def get_run_history(self, ticket_id: str = None):
        if ticket_id:
            cursor = self.conn.execute(
                "SELECT * FROM workflow_runs WHERE ticket_id = ?", (ticket_id,))
        else:
            cursor = self.conn.execute("SELECT * FROM workflow_runs ORDER BY id DESC LIMIT 10")
        return cursor.fetchall()
