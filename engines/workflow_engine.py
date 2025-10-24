# engines/workflow_engine.py (replace your current version with this merged one)
import json
import os
from pathlib import Path
from typing import Dict, Any, List
from agents.data_request_agent import DataRequestAgent
from agents.decision_agent import DecisionAgent
from agents.result_aggregator import ResultAggregator
from agents.exception_agent import ExceptionAgent
from agents.compare import rounded_equality, date_in_range, equals
from utils.logger import info
from agents.document_extraction_agent import DocumentExtractionAgent  # NEW

class WorkflowEngine:
    """
    Minimal, deterministic QA workflow for Fee Modification + optional doc check:
      - Extract datapoints (WorkHub, FeeApp, Email approval)
      - Optional: extract document fields from a PDF (LLM tool if enabled)
      - Run checks: rate match (rounded 2dp), effective date window, approval exists, doc field checks
      - Aggregate -> Decide -> (optional) Exception email payload
    """
    def __init__(self, llm=None):
        self.extractor = DataRequestAgent()
        self.decision = DecisionAgent()
        self.agg = ResultAggregator()
        self.exception = ExceptionAgent()
        self.doc = DocumentExtractionAgent(llm=llm)  # NEW

    def run(self, ticket: Dict[str, Any], scenario: str = "happy", use_llm: bool = False, llm=None,
            pdf_path: str | None = None, expected_doc_fields: Dict[str, Any] | None = None) -> Dict[str, Any]:
        account_id = ticket["account_id"]
        eff_date = ticket["effective_date"]

        info("Fetching WorkHub and FeeApp data")
        wh = self.extractor.fetch_workhub_fee_mod(account_id)
        fa = self.extractor.fetch_feeapp_fees(account_id, scenario=scenario)
        approval_exists = self.extractor.email_approval_exists(account_id)

        checks: List[Dict[str, Any]] = []
        # 1) rate compares
        c1 = rounded_equality(wh["new_rate"], fa["approved_rate"], places=2)
        c1.update({"id": "rate_match"})
        checks.append(c1)
        # 2) approval
        c2 = {"passed": bool(approval_exists), "reason": "approval email present" if approval_exists else "approval email missing", "id": "approval_email_present"}
        checks.append(c2)
        # 3) effective date window
        c3 = date_in_range(wh["modified_timestamp"], eff_date, 7)
        c3.update({"id": "effective_date_window"})
        checks.append(c3)

        # 4) NEW: Document extraction & field comparisons (optional)
        extracted_doc: Dict[str, Any] | None = None
        if pdf_path and expected_doc_fields:
            info(f"Extracting fields from document: {pdf_path}")
            extracted_doc = self.doc.extract_fields(pdf_path, expected_doc_fields)

            # Compare expected vs extracted (only for provided keys)
            for key, expected_value in expected_doc_fields.items():
                got = extracted_doc.get(key)
                # choose comparator based on field type
                if key in ("client_name", "name", "account_name"):
                    # relaxed string equality
                    res = equals(got, expected_value, normalize=True)
                elif "date" in key or key in ("dob",):
                    # compare normalized ISO dates; if not ISO, the reason will still print values
                    res = equals(got, expected_value, normalize=False)
                else:
                    res = equals(got, expected_value, normalize=False)

                res.update({"id": f"doc_field_match::{key}", "left": got, "right": expected_value})
                checks.append(res)

        # aggregate & decide
        summary = self.agg.aggregate(checks)
        decision = self.decision.decide(ticket, summary)

        result: Dict[str, Any] = {
            "ticket": ticket,
            "datapoints": {"workhub": wh, "feeapp": fa, "approval_exists": approval_exists},
            "document": {"path": pdf_path, "extracted": extracted_doc} if extracted_doc is not None else None,
            "checks": checks,
            "summary": summary,
            "decision": decision,
        }

        if decision["decision"] == "FAIL":
            result["exception_email"] = self.exception.build_email(ticket, summary["failed_checks"])

        # Optional LLM narrative
        if use_llm and llm is not None:
            prompt = (
                "Write a concise QA result for a fee modification check.\n"
                f"Ticket: {ticket['ticket_id']}, Account: {account_id}\n"
                f"Checks: {json.dumps(checks)}\n"
                "Summarize in 3 bullets. Keep factual and neutral."
            )
            llm_out = llm.invoke(prompt)
            result["llm_summary"] = str(llm_out.content)

        return result
