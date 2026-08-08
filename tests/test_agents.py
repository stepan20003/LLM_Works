import pytest
import pytest_asyncio
from uuid import uuid4

from app.agents.manager_agent import ManagerAgent
from app.agents.reviewer_agent import ReviewerAgent
from app.agents.tester_agent import TesterAgent
from app.agents.developer_agent import DeveloperAgent
from app.schemas.enums import AgentExecutionStatus, AgentRole
from app.core.base_tool import BaseTool
from app.schemas.value_objects.tool_result import ToolResult
from app.schemas.value_objects.metadata import Metadata


class MockShellTool(BaseTool):
    """Mock tool to simulate shell command executions for agents."""
    component_id: str = "mock-shell"
    description: str = "Mock shell tool for tests"
    should_succeed: bool = True
    
    async def initialize(self):
        self.is_initialized = True
        
    async def shutdown(self):
        self.is_initialized = False
        
    async def health_check(self):
        return self.is_initialized
        
    async def execute(self, **kwargs):
        self.validate_state()
        if self.should_succeed:
            return ToolResult(
                success=True, 
                stdout="Mock command executed successfully.", 
                execution_time=0.1, 
                metadata=Metadata(source_component="mock-shell")
            )
        else:
            return ToolResult(
                success=False, 
                stderr="Mock command failed.", 
                exit_code=1, 
                execution_time=0.1, 
                metadata=Metadata(source_component="mock-shell")
            )


@pytest.mark.asyncio
async def test_manager_agent():
    """Verify ManagerAgent routing logic."""
    agent = ManagerAgent(component_id="manager-1")
    await agent.initialize()
    
    task_id = uuid4()
    response = await agent.process_task(task_id, {"content": "Build a new module"})
    
    assert response.status == AgentExecutionStatus.SUCCESS
    assert response.next_agent == AgentRole.DEVELOPER
    await agent.shutdown()


@pytest.mark.asyncio
async def test_reviewer_agent():
    """Verify ReviewerAgent code evaluation logic."""
    agent = ReviewerAgent(component_id="reviewer-1")
    await agent.initialize()
    
    task_id = uuid4()
    
    # Դեպք 1: Բարեհաջող ստուգում
    resp_pass = await agent.process_task(task_id, {"content": "All tests passed cleanly."})
    assert resp_pass.status == AgentExecutionStatus.SUCCESS
    assert resp_pass.next_agent == AgentRole.MANAGER
    
    # Դեպք 2: Սխալի հայտնաբերում
    resp_fail = await agent.process_task(task_id, {"content": "There is a syntax error in the file."})
    assert resp_fail.status == AgentExecutionStatus.NEEDS_FIX
    assert resp_fail.next_agent == AgentRole.DEVELOPER
    
    await agent.shutdown()


@pytest.mark.asyncio
async def test_tester_agent():
    """Verify TesterAgent test execution and reporting logic."""
    agent = TesterAgent(component_id="tester-1")
    await agent.initialize()
    task_id = uuid4()
    
    # Դեպք 1: Գործիքը գրանցված չէ (պետք է ձախողվի)
    resp_no_tool = await agent.process_task(task_id, {"content": "Run tests"})
    assert resp_no_tool.status == AgentExecutionStatus.FAILED
    assert "is not registered" in resp_no_tool.message
    
    # Գրանցում ենք կեղծ գործիքը
    mock_tool = MockShellTool()
    await mock_tool.initialize()
    agent.register_tool("shell_tool", mock_tool)
    
    # Դեպք 2: Թեստերը բարեհաջող անցնում են
    resp_success = await agent.process_task(task_id, {"content": "Run tests"})
    assert resp_success.status == AgentExecutionStatus.SUCCESS
    assert resp_success.next_agent == AgentRole.REVIEWER
    
    # Դեպք 3: Թեստերը ձախողվում են
    mock_tool.should_succeed = False
    resp_needs_fix = await agent.process_task(task_id, {"content": "Run tests"})
    assert resp_needs_fix.status == AgentExecutionStatus.NEEDS_FIX
    assert resp_needs_fix.next_agent == AgentRole.DEVELOPER
    
    await mock_tool.shutdown()
    await agent.shutdown()


@pytest.mark.asyncio
async def test_developer_agent():
    """Verify DeveloperAgent coding and shell execution logic."""
    agent = DeveloperAgent(component_id="dev-1")
    await agent.initialize()
    task_id = uuid4()
    
    # Դեպք 1: Սովորական ծածկագիր (առանց թեստի պահանջի)
    resp_simple = await agent.process_task(task_id, {"content": "Write standard code"})
    assert resp_simple.status == AgentExecutionStatus.SUCCESS
    assert resp_simple.next_agent == AgentRole.REVIEWER
    
    # Դեպք 2: "Test" բառը կա, բայց գործիք չկա (պարզապես բաց է թողնում)
    resp_no_tool = await agent.process_task(task_id, {"content": "Write code and test it"})
    assert resp_no_tool.status == AgentExecutionStatus.SUCCESS
    
    # Դեպք 3: "Test" պահանջը կա և գործիքը ձախողվում է
    mock_tool = MockShellTool()
    mock_tool.should_succeed = False
    await mock_tool.initialize()
    agent.register_tool("shell_tool", mock_tool)
    
    resp_fail = await agent.process_task(task_id, {"content": "Write code and test it"})
    assert resp_fail.status == AgentExecutionStatus.FAILED
    assert resp_fail.next_agent == AgentRole.REVIEWER
    
    await mock_tool.shutdown()
    await agent.shutdown()