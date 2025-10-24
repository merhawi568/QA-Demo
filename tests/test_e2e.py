# tests/test_e2e.py
from engines.workflow_engine import WorkflowEngine
from utils.data_loader import load_ticket

def test_happy():
    ticket = load_ticket("TKT67890")
    eng = WorkflowEngine()
    res = eng.run(ticket, scenario="happy")
    assert res["decision"]["decision"] == "PASS"
    assert res["summary"]["failed"] == 0

def test_fail_rate_mismatch():
    ticket = load_ticket("TKT67890")
    eng = WorkflowEngine()
    res = eng.run(ticket, scenario="fail")
    assert res["decision"]["decision"] == "FAIL"
    assert res["summary"]["failed"] >= 1
