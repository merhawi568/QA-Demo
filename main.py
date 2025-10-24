import os
import time
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from utils.data_loader import load_ticket
from utils.logger import log_start, log_complete
from engines.workflow_engine import WorkflowEngine
import argparse
def main():
    load_dotenv()
    
    # Initialize LLM
    llm = ChatOpenAI(
        model="gpt-4o",
        temperature=0,
        api_key=os.getenv("OPENAI_API_KEY")
    )
    
    # Initialize components
    parser = argparse.ArgumentParser(description='QA Agent Demo')
    parser.add_argument('--ticket', type=str, default='TKT67890', 
                       help='Ticket ID to validate')
    parser.add_argument('--scenario', choices=['pass', 'fail'], 
                       default='pass', help='Scenario to run')
    parser.add_argument('--verbose', action='store_true', 
                       help='Verbose output')
    
    args = parser.parse_args()
    # Build workflow
    engine = WorkflowEngine(llm=llm)
    
    # Run demo
    ticket_id = args.ticket
    
    # Load ticket for header
    tt = load_ticket(ticket_id)
    log_start(ticket_id, tt["trade_type"], tt["platform"])
    
    # Map scenario names
    scenario_map = {"pass": "happy", "fail": "fail"}
    scenario = scenario_map.get(args.scenario, "happy")
    
    start_time = time.time()
    result = engine.run(tt, scenario=scenario)
    duration = time.time() - start_time
    
    # Print results
    agg = result.get("summary", {})
    status = result.get("decision", {}).get("decision", "UNKNOWN")
    total = agg.get("total", 0)
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
