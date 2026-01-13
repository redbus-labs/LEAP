import pytest

from core_agentic import agentic_base
from core_agentic.agentic import orchestrator, beforeExecution

@pytest.fixture(scope="function", autouse=True)
def setup_and_teardown():
    beforeExecution()
    print("Fresh browser started")
    yield
    agentic_base.afterExecutionCleanup()
    print("Cleanup done, browser closed")

def test_demo():
        orchestrator("""I want to reach Sihanoukville. I am currently in Koh Touch Beach.
        "I want to travel 15 days from today. Verify if there are any ferries available """)

