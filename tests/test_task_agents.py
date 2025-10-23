import pytest
from agents.task_agents import TaskAgents

def test_compare_equals():
    result = TaskAgents.compare("ACC12345", "ACC-12345", "equals", normalize=True)
    assert result.passed == True

def test_compare_not_equals():
    result = TaskAgents.compare("ACC111", "ACC222", "equals")
    assert result.passed == False

def test_validate_email():
    result = TaskAgents.validate("test@example.com", ["not_null", "is_email"])
    assert result.passed == True

def test_validate_email_fail():
    result = TaskAgents.validate("invalid-email", ["is_email"])
    assert result.passed == False

def test_date_compare():
    result = TaskAgents.date_compare(
        "2025-10-23T14:00:00Z",
        "2025-10-23T14:30:00Z",
        "before"
    )
    assert result.passed == True
