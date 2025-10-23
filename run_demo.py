import os
import time
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from utils.data_loader import DataLoader
from utils.logger import log_start, log_complete, console
from agents.orchestrator import OrchestratorAgent
from agents.data_request_agent import DataRequestAgent
from agents.result_aggregator import ResultAggregator
from agents.decision_agent import DecisionAgent
from agents.exception_agent import ExceptionAgent
from engines.workflow_engine import WorkflowEngine
from rich.panel import Panel

def run_scenario(engine, data_loader, ticket_id, scenario_name):
    console.print(Panel(f"[bold cyan]Scenario: {scenario_name}[/bold cyan]", border_style="cyan"))
    
    tt = data_loader.load_trade_ticket(ticket_id)
    log_start(ticket_id, tt["trade_type"], tt["platform"])
    
    start_time = time.time()
    result = engine.run(ticket_id)
    duration = time.time() - start_time
    
    agg = result.get("aggregated_result", {})
    status = agg.get("overall_status", "UNKNOWN")
    total = agg.get("total_checks", 0)
    failed = agg.get("failed", 0)
    
    log_complete(status, duration, total, failed)
    
    if result.get("exception_email"):
        email = result["exception_email"]
        console.print("\n[bold yellow]📧 Exception Email Drafted:[/bold yellow]")
        console.print(Panel(
            f"[cyan]To:[/cyan] {email['to']}\n"
            f"[cyan]Subject:[/cyan] {email['subject']}\n\n"
            f"{email['body']}",
            border_style="yellow"
        ))
    
    console.print("\n" + "="*80 + "\n")
    input("Press Enter to continue to next scenario...")

def main():
    load_dotenv()
    
    llm = ChatOpenAI(model="gpt-4o", temperature=0, api_key=os.getenv("OPENAI_API_KEY"))
    
    data_loader = DataLoader("mock_data")
    orchestrator = OrchestratorAgent(llm)
    data_agent = DataRequestAgent(data_loader)
    aggregator = ResultAggregator()
    decision_agent = DecisionAgent(llm)
    exception_agent = ExceptionAgent(llm)
    
    engine = WorkflowEngine(orchestrator, data_agent, aggregator, decision_agent, exception_agent)
    
    console.print(Panel(
        "[bold green]QA Agent Multi-Agent Demo[/bold green]\n\n"
        "This demo shows:\n"
        "• Orchestrator determining required checks\n"
        "• Data agents fetching from mock APIs\n"
        "• Task agents running validations\n"
        "• Decision agent evaluating results\n"
        "• Exception agent drafting emails\n\n"
        "[yellow]Press Ctrl+C to exit anytime[/yellow]",
        border_style="green"
    ))
    input("\nPress Enter to start...")
    
    # Scenario 1: PASS
    run_scenario(engine, data_loader, "TKT67890", "✅ All Checks Pass")
    
    # Scenario 2: FAIL - Update to use CALL-002
    console.print("[yellow]Note: Scenario 2 will use CALL-002 (consent after trade)[/yellow]\n")
    
    # Temporarily modify workflow to use CALL-002
    original_fetch = engine.fetch_data
    def fetch_data_fail(state):
        state = original_fetch(state)
        state["voice_data"] = data_loader.load_voice_recording("CALL-002")
        return state
    engine.fetch_data = fetch_data_fail
    
    run_scenario(engine, data_loader, "TKT67891", "❌ Consent Timing Violation")
    
    console.print(Panel(
        "[bold green]Demo Complete![/bold green]\n\n"
        "Ready for POC:\n"
        "1. Uncomment real API code in data_loader.py\n"
        "2. Add API credentials\n"
        "3. Connect to real systems\n"
        "4. Add more validation checks\n"
        "5. Deploy!",
        border_style="green"
    ))

if __name__ == "__main__":
    main()
