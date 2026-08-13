import pytest
from uuid import uuid4
from app.agents.debugger_agent import DebuggerAgent
from app.schemas.enums import AgentRole, AgentExecutionStatus
from app.core.base_llm import BaseLLM

class MockLLM(BaseLLM):
    model_name: str = "mock"
    api_key: str = "test"
    
    async def initialize(self): pass
    async def shutdown(self): pass
    async def health_check(self) -> bool: return True
    
    async def generate_completion(self, prompt, system_prompt=None):
        if "force_fail" in prompt.lower():
            raise Exception("LLM failure")
        return "Fix plan: do X and Y."
        
    async def generate_structured(self, prompt, response_schema, system_prompt=None):
        pass

@pytest.mark.asyncio
async def test_debugger_agent_success():
    agent = DebuggerAgent(component_id="debugger-1")
    await agent.initialize()
    agent.llm = MockLLM(component_id="mock")
    task_id = uuid4()

    resp = await agent.process_task(
        task_id, 
        {"test_result": {"error_summary": "Test failed due to X", "stdout": "", "stderr": ""}}
    )
    assert resp.status == AgentExecutionStatus.SUCCESS
    assert resp.next_agent in {AgentRole.TESTER, AgentRole.DEVELOPER}
    assert "Fix plan:" in resp.metadata.extra["rca_plan"] or "Performed root cause analysis" in resp.metadata.extra["rca_plan"]
    await agent.shutdown()

@pytest.mark.asyncio
async def test_debugger_agent_llm_failure():
    agent = DebuggerAgent(component_id="debugger-1")
    await agent.initialize()
    agent.llm = MockLLM(component_id="mock")
    task_id = uuid4()

    resp = await agent.process_task(
        task_id, 
        {"test_result": {"error_summary": "force_fail", "stdout": "", "stderr": ""}}
    )
    assert resp.status == AgentExecutionStatus.FAILED
    assert resp.next_agent in {AgentRole.MANAGER, AgentRole.TESTER, AgentRole.DEVELOPER}
    await agent.shutdown()

@pytest.mark.asyncio
async def test_debugger_agent_no_structured_test_result():
    agent = DebuggerAgent(component_id="debugger-1")
    await agent.initialize()
    agent.llm = MockLLM(component_id="mock")
    task_id = uuid4()

    resp = await agent.process_task(
        task_id, 
        {"content": "some raw output"}
    )
    assert resp.status == AgentExecutionStatus.SUCCESS
    assert resp.next_agent in {AgentRole.TESTER, AgentRole.DEVELOPER}
    await agent.shutdown()
