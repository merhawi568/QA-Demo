# run_demo.py (only diffs shown vs the version I gave you)
import json
import os
import argparse
from dotenv import load_dotenv
from rich.panel import Panel
from langchain_openai import ChatOpenAI
from utils.logger import console, section, success, failure, info
from utils.data_loader import load_ticket
from engines.workflow_engine import WorkflowEngine

def run_case(ticket_id: str, scenario: str, use_llm: bool, pdf_path: str | None):
    section(f"Scenario: {scenario.upper()} — Ticket {ticket_id}")
    ticket = load_ticket(ticket_id)

    llm = None
    if use_llm and os.getenv("OPENAI_API_KEY"):
        llm = ChatOpenAI(model="gpt-4o", temperature=0)

    # expected fields for doc extraction (for demo)
    expected_doc_fields = None
    if pdf_path:
        # In a real run, you’d pull these from ticket metadata or template.
        expected_doc_fields = {
            "client_name": "JANE DOE",
            "dob": "2015-06-12",
            "effective_date": ticket["effective_date"],
        }

    engine = WorkflowEngine(llm=llm if use_llm else None)
    result = engine.run(
        ticket,
        scenario=scenario,
        use_llm=use_llm,
        llm=llm,
        pdf_path=pdf_path,
        expected_doc_fields=expected_doc_fields
    )

    console.print(Panel("[bold]Checks[/bold]", border_style="cyan"))
    for c in result["checks"]:
        (success if c["passed"] else failure)(f"{c['id']}: {c['reason']}")

    console.print(Panel("[bold]Decision[/bold]", border_style="cyan"))
    if result["decision"]["decision"] == "PASS":
        success("Overall: PASS")
    else:
        failure("Overall: FAIL")
        ex = result.get("exception_email")
        if ex:
            info(f"Exception Email To: {ex['to']}")
            info(f"Subject: {ex['subject']}")
            console.print("\n" + ex["body"])

    if use_llm and "llm_summary" in result:
        console.print(Panel("[bold]LLM Summary[/bold]\n\n" + result["llm_summary"], border_style="magenta"))

    out_dir = "outputs"; os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"RUN_{ticket_id}_{scenario}.json")
    open(path, "w").write(json.dumps(result, indent=2))
    info(f"Ledger written to {path}")

def main():
    load_dotenv()
    parser = argparse.ArgumentParser(description="QA Demo Runner")
    parser.add_argument("--ticket", default="TKT67890")
    parser.add_argument("--scenario", choices=["happy", "fail"], default="happy")
    parser.add_argument("--llm", action="store_true", help="Use OpenAI for narrative + PDF structuring")
    parser.add_argument("--pdf", default=None, help="Path to a PDF to parse (enables document checks)")
    args = parser.parse_args()
    run_case(args.ticket, args.scenario, use_llm=args.llm, pdf_path=args.pdf)

if __name__ == "__main__":
    main()
