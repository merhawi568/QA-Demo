import os
import time
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from utils.data_loader import DataLoader
from utils.logger import log_start, log_complete
from agents.orchestrator import OrchestratorAgent
from agents.data_request_agent import DataRequestAgent
from agents.result_aggregator import ResultAggregator
from agents.decision_agent import DecisionAgent
from agents.exception_agent import ExceptionAgent
from engines.workflow_engine import WorkflowEngine

def main():
    load_dotenv()
    
    # Initialize LLM
    llm = ChatOpenAI(
        model="gpt-4o",
        temperature=0,
        api_key=os.getenv("OPENAI_API_KEY")
    )
    
    # Initialize components
    data_loader = DataLoader("mock_data")
    orchestrator = OrchestratorAgent(llm)
    data_agent = DataRequestAgent(data_loader)
    aggregator = ResultAggregator()
    decision_agent = DecisionAgent(llm)
    exception_agent = ExceptionAgent(llm)
    
    # Build workflow
    engine = WorkflowEngine(
        orchestrator, data_agent, aggregator, 
        decision_agent, exception_agent
    )
    
    # Run demo - PASS scenario
    ticket_id = "TKT67890"
    
    # Load ticket for header
    tt = data_loader.load_trade_ticket(ticket_id)
    log_start(ticket_id, tt["trade_type"], tt["platform"])
    
    start_time = time.time()
    result = engine.run(ticket_id)
    duration = time.time() - start_time
    
    # Print results
    agg = result.get("aggregated_result", {})
    status = agg.get("overall_status", "UNKNOWN")
    total = agg.get("total_checks", 0)
    failed = agg.get("failed", 0)
    
    log_complete(status, duration, total, failed)
    
    # Print exception email if raised
    if result.get("exception_email"):
        email = result["exception_email"]
        print(f"\n📧 Exception Email:")
        print(f"To: {email['to']}")
        print(f"Subject: {email['subject']}")
        print(f"\n{email['body']}")
    
    print("\n" + "="*80)
    print("Demo scenarios available:")
    print("  TKT67890 - PASS scenario (all checks pass)")
    print("  TKT67891 - FAIL scenario (consent timing violation)")
    print("="*80)

if __name__ == "__main__":
    main()
