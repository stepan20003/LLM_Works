# AI_HANDOFF.md

> Persistent handoff/context file for the AI-Dev-Team project.
> A new AI session should read this file first and continue from the current state
> instead of redesigning the project or asking for the whole history again.

## 1. PROJECT VISION

AI-Dev-Team is intended to become a model-agnostic autonomous software-engineering
platform.

The user should eventually provide one large project prompt and the AI team should:
1. Understand requirements.
2. Plan and decompose the project.
3. Implement code.
4. Run tests/tools.
5. Detect failures.
6. Debug and retry autonomously.
7. Review the implementation.
8. Perform quality/security checks.
9. Iterate until requirements are satisfied.
10. Show the complete real execution history live in the dashboard.
11. Finish with an explicit APPROVED / DONE state.

The architecture must be future-proof: agent roles must be independent from
specific LLM providers/models.

Target architecture:

    USER PROMPT
        |
      PROJECT
        |
       PLAN
        |
    TASK GRAPH
        |
      AGENTS
        |
    MODEL ROUTER
        |
    TOOLS / WORKSPACE
        |
    TEST -> DEBUG -> REVIEW
        |
     APPROVED
        |
       DONE

## 2. CURRENT BASELINE

The project currently has a working backend, dashboard, WebSocket/EventBus,
TaskManager, Orchestrator, agents, LLM integration, workspace tools, security
fixes, Docker support, and a substantial test suite.

Last known strong full-suite result:

    python3 -m pytest -q
    57 passed, 0 failed

Last known coverage:

    1577 statements
    337 missed
    ~79%

Warnings existed but did not fail the suite.

A direct runtime demo also succeeded:

    task creation
      -> TaskManager
      -> Orchestrator
      -> DeveloperAgent
      -> Groq/OpenAI-compatible LLM
      -> code generation
      -> test generation
      -> ShellTool
      -> tests
      -> DONE
      -> EventBus telemetry
      -> shutdown

Real web integration was also reported working:

    Dashboard
      -> POST /tasks/
      -> task appears
      -> Orchestrator auto-picks task
      -> DeveloperAgent
      -> LLM
      -> workspace files
      -> tests
      -> DONE
      -> WebSocket events
      -> dashboard live update

Important: the repository may contain newer user changes than this snapshot.
Always inspect the current working tree before editing.

## 3. CURRENT DIRECTORY / MAJOR COMPONENTS

Known structure:

    app/
    ├── agents/
    │   ├── base_worker_agent.py
    │   ├── developer_agent.py
    │   ├── manager_agent.py
    │   ├── reviewer_agent.py
    │   └── tester_agent.py
    ├── api/
    │   ├── app.py
    │   ├── router.py
    │   ├── websocket.py
    │   └── dependencies.py
    ├── core/
    │   ├── base_agent.py
    │   ├── base_component.py
    │   ├── base_llm.py
    │   ├── base_memory.py
    │   ├── base_tool.py
    │   └── base_workspace.py
    ├── llm/
    │   ├── openai_client.py
    │   └── router.py
    ├── messaging/
    │   ├── message_bus.py
    │   └── event_bus.py
    ├── orchestrator/
    │   └── orchestrator.py
    ├── schemas/
    │   ├── base.py
    │   ├── enums.py
    │   ├── entities/
    │   │   ├── task.py
    │   │   ├── message.py
    │   │   └── event.py
    │   └── value_objects/
    │       ├── agent_response.py
    │       ├── agent_runtime.py
    │       ├── attachment.py
    │       ├── metadata.py
    │       └── tool_result.py
    ├── settings/
    ├── tasks/
    ├── tools/
    │   ├── file_tools.py
    │   └── shell_tool.py
    └── workspace/
        └── local_workspace.py

Also important:

    tests/
    Dockerfile
    docker-compose.yml
    pyproject.toml
    poetry.lock
    app/static/index.html

## 4. CURRENT AGENT ROLES

Current known roles:

    SYSTEM
    MANAGER
    DEVELOPER
    REVIEWER
    TESTER

Future intended roles:

    MANAGER
    ARCHITECT
    DEVELOPER
    TESTER
    DEBUGGER
    REVIEWER
    SECURITY
    DEVOPS
    DOCUMENTATION
    RESEARCHER

Do not add every future role immediately. Add a role only when its execution
contract and orchestration behavior are defined.

## 5. CURRENT DOMAIN ENUMS

`app/schemas/enums.py` currently contains:

AgentRole:
    SYSTEM
    MANAGER
    DEVELOPER
    REVIEWER
    TESTER

AgentState:
    IDLE
    THINKING
    WORKING
    WAITING
    FAILED
    FINISHED

AgentExecutionStatus:
    SUCCESS
    FAILED
    NEEDS_FIX
    BLOCKED
    WAITING

TaskStatus:
    CREATED
    WAITING
    READY
    IN_PROGRESS
    BLOCKED
    REVIEW
    TESTING
    RETRYING
    DONE
    FAILED
    CANCELLED
    ARCHIVED

TaskPriority:
    LOW
    NORMAL
    HIGH
    CRITICAL

MessageStatus:
    INFO
    REQUEST
    RESPONSE
    WARNING
    ERROR
    NEEDS_FIX
    APPROVED
    REJECTED

EventType:
    MESSAGE_SENT
    MESSAGE_RECEIVED
    TASK_CREATED
    TASK_UPDATED
    TASK_COMPLETED
    TOOL_EXECUTED
    ERROR

## 6. CURRENT MESSAGE CONTRACT

`app/schemas/entities/message.py`:

    sender: AgentRole
    receiver: AgentRole
    task_id: UUID
    status: MessageStatus
    priority: TaskPriority
    content: str
    attachments: list[Attachment]
    metadata: Metadata
    correlation_id: Optional[UUID]
    reply_to: Optional[UUID]

Important:
- `requires_response` is NOT a Message field.
- `correlation_id` IS a Message field.
- Sender and receiver must be different roles.
- SYSTEM is used by the MessageBus.

Do not reintroduce unsupported constructor arguments.

## 7. CURRENT EVENT CONTRACT

`app/schemas/entities/event.py`:

    event_type
    source_agent
    destination_agent
    task_id
    payload
    metadata

Important:
- `correlation_id` is NOT an Event constructor field.
- Correlation information, if needed, belongs in `payload`.
- Events are used for dashboard telemetry.

## 8. CURRENT TASK CONTRACT

`Task` currently contains:

    title
    description
    status
    priority
    created_by
    assigned_to
    parent_task
    dependencies
    tags
    metadata
    retry_count
    max_retries
    estimated_duration
    started_at
    completed_at
    failed_at

Validation:
- retry_count cannot exceed max_retries unless status is FAILED.
- DONE gets completed_at automatically if missing.
- completed_at is invalid for non-DONE tasks.
- FAILED gets failed_at automatically if missing.

TaskManager.create_task was fixed to accept and pass through assigned_to.

## 9. MESSAGE BUS

`app/messaging/message_bus.py`

Responsibilities:
- agent registration
- lookup by AgentRole
- point-to-point dispatch
- SYSTEM-targeted messages
- AgentError wrapping

API:

    register_agent(agent)
    dispatch(message)

Keep routing separate from orchestration. Do not turn MessageBus into a workflow engine.

## 10. EVENT BUS

`app/messaging/event_bus.py`

Responsibilities:
- async publish/subscribe
- callback error isolation
- WebSocket telemetry

API:

    subscribe(event_type, callback)
    unsubscribe(event_type, callback)
    publish(event)

Important:
- callbacks are async
- disconnected WebSocket clients must be unsubscribed
- listener failure must not stop other listeners
- callbacks currently run concurrently via asyncio.gather

## 11. ORCHESTRATOR

`app/orchestrator/orchestrator.py`

Current responsibilities:
- coordinate task execution
- inspect task state
- dispatch agents
- update task state
- publish events
- manage execution loop

Architectural rule:

The Orchestrator coordinates. It should NOT become a giant class containing
all agent-specific business logic.

Future responsibilities:
- project workflow
- dependency scheduling
- agent selection
- retry policy
- state transitions
- event emission

## 12. CURRENT AGENTS

### ManagerAgent
Current: manager-level task handling/orchestration support.

Future:
- project planning
- requirement decomposition
- dependency graph
- prioritization
- assignment

### DeveloperAgent
Current:
- receives development task
- calls LLM
- generates code
- generates tests
- uses FileTool/ShellTool
- runs tests
- returns AgentResponse

A real runtime successfully used Groq to generate code/tests and reached DONE.

Important:
Use interpreter-safe test execution:

    sys.executable -m pytest ...

Do not assume a standalone `pytest` executable is on PATH.

### ReviewerAgent
Current: review support.

Future:
- structured APPROVED / NEEDS_FIX
- findings
- quality/security review
- model selection

### TesterAgent
Current: testing support.

Known warning:

    PytestCollectionWarning:
    cannot collect test class 'TesterAgent' because it has an __init__ constructor

This warning did not fail the suite.

## 13. LLM LAYER

Known files:

    app/core/base_llm.py
    app/llm/openai_client.py
    app/llm/router.py

Current runtime uses an OpenAI-compatible client against Groq.

Observed example:

    model = llama-3.1-8b-instant
    base_url = https://api.groq.com/openai/v1

Target architecture:

    Agent
      |
      v
    LLM interface
      |
      v
    LLM Router
      |
      +--> OpenAI adapter
      +--> Anthropic adapter
      +--> Google adapter
      +--> Groq adapter
      +--> OpenRouter adapter
      +--> Local adapter

Agents must not directly depend on provider-specific clients.

## 14. TOOLS

### FileTool
Used for workspace file operations.

### ShellTool
Security work already performed.

Previous vulnerability:
raw shell execution and weak cwd containment.

Current direction:
- `asyncio.create_subprocess_exec(...)`
- shlex parsing
- workspace cwd validation
- timeout
- output truncation

Workspace binding uses the existing secure path validation.

Remaining limitation:
arbitrary executables available in the runtime can still be invoked.

Future hardening:
- container isolation
- command policies
- resource limits
- network restrictions
- filesystem restrictions

## 15. WORKSPACE SECURITY

`app/workspace/local_workspace.py`

Previous vulnerability:
string `startswith()` containment.

Fixed using resolved path containment.

Expected:
- safe nested paths allowed
- `../` traversal rejected
- absolute outside paths rejected
- sibling prefix escapes rejected
- symlink escapes rejected

Never replace this with a string prefix check.

## 16. API

FastAPI exists.

Known routes:

    /health
    /tasks/
    /tasks/{task_id}

OpenAPI was previously verified to expose these.

The router was fixed to resolve TaskManager/Orchestrator from current app state
instead of relying on stale module globals.

`app.state` is populated during lifespan.

This prevents state leakage across FastAPI app instances.

## 17. WEBSOCKET

`app/api/websocket.py`

Current:
- accepts clients
- subscribes to EventBus
- sends JSON events
- unsubscribes on disconnect/failure
- multiple clients supported

Expected event shape:

    event_type
    payload
    source_agent
    destination_agent
    task_id

Current limitation:
all clients receive all events.

Future filtering:
- project
- task
- agent
- event type
- severity

## 18. DASHBOARD

`app/static/index.html`

The user's explicit product goal is a professional live control center.

It should show:

- original user prompt
- overall status
- progress
- task graph
- agent status
- current agent
- current action
- model selected
- files changed
- commands
- test results
- errors
- retries
- event timeline
- completed subtasks
- remaining subtasks
- final approval

Desired visible workflow:

    USER PROMPT
       |
    MANAGER
       |
    ARCHITECT
       |
    DEVELOPER
       |
    TESTER
       |
    DEBUGGER
       |
    REVIEWER
       |
    SECURITY
       |
    APPROVED PROJECT DONE

Dashboard must show real backend events, not fake animation.

## 19. DEPENDENCIES / DOCKER

Previously fixed:
- FastAPI
- Uvicorn
- OpenAI
were missing from runtime metadata.

`pytest-asyncio` belongs to test/dev dependencies.

Dockerfile was simplified to rely on declared project dependencies.

`poetry.lock` was regenerated.

Docker build previously succeeded.

Container health previously returned:

    {"status":"healthy","service":"ai-development-team"}

Always inspect current `pyproject.toml` before changing dependency management.

## 20. TEST STATUS / WARNINGS

Last known full result:

    python3 -m pytest -q
    57 passed, 0 failed

Coverage:

    ~79%

Warnings:
1. TesterAgent pytest collection warning.
2. Starlette/FastAPI TestClient warning involving httpx/httpx2.

These are lower priority than autonomous workflow architecture.

Historical orchestrator async-fixture failures existed with pytest-asyncio.
The broader suite later reached 57 passing tests, so if the issue reappears,
inspect current pytest/pytest-asyncio configuration before changing tests.

## 21. WHAT IS WORKING VS WHAT IS MISSING

WORKING:
- FastAPI
- Dashboard integration
- WebSocket/EventBus
- TaskManager
- MessageBus
- EventBus
- Orchestrator
- Manager/Developer/Reviewer/Tester
- Groq/OpenAI-compatible LLM
- FileTool
- ShellTool
- workspace containment security
- API app-state wiring
- Docker build/start
- task -> LLM -> code -> tests -> DONE demo
- 57 passing tests at last known baseline

NOT YET FINAL:
- true project-level planning
- large task decomposition
- dependency graph execution at project scale
- Debugger agent
- robust autonomous retry/debug/review loop
- model registry
- agent registry
- per-role model selection
- provider abstraction at full scale
- model fallback
- multi-model strategies
- project persistence/resume
- production-grade isolation and resource controls
- complete professional telemetry dashboard

## 22. PRODUCT REQUIREMENT

The user wants a system where they can eventually give one large prompt such as:

    Build a production-ready e-commerce platform with authentication,
    PostgreSQL, payments, admin dashboard and tests.

Then the system should autonomously:

    plan
    decompose
    schedule
    implement
    test
    debug
    review
    retry
    report
    approve
    finish

The user wants to see every meaningful transition live.

## 23. MODEL-AGNOSTIC DESIGN

A role is NOT a model.

Target:

    Developer
      ├── Model A
      ├── Model B
      ├── Model C
      └── fallback models

Same for every role.

Future UI:

    SELECT AI TEAM

    Manager       [ Model ▼ ]
    Architect     [ Model ▼ ]
    Developer     [ Model ▼ ]
    Tester        [ Model ▼ ]
    Debugger      [ Model ▼ ]
    Reviewer      [ Model ▼ ]
    Security      [ Model ▼ ]
    DevOps        [ Model ▼ ]

    Execution Strategy [ Autonomous ▼ ]

Possible future strategies:

    Single
    Fallback
    Parallel
    Consensus
    Best-of-N

Do not implement every strategy before basic model routing is stable.

## 24. 2-4 WEEK EXACT ROADMAP

This is a focused-development estimate. Actual time depends on debugging,
model quality, and how many hours per day are available.

### WEEK 1 — MODEL/AGENT FOUNDATION

#### Milestone 1: Clean LLM abstraction

Inspect first:

    app/core/base_llm.py
    app/llm/openai_client.py
    app/llm/router.py
    app/settings/settings.py
    app/agents/base_worker_agent.py
    app/core/base_agent.py

Goal:

    DeveloperAgent -> LLM interface -> Router -> selected model

not:

    DeveloperAgent -> Groq-specific implementation

Acceptance:
- existing runtime still works
- DeveloperAgent has no provider-specific dependency
- model can be selected through configuration
- tests cover the interface

#### Milestone 2: Model Registry

Introduce a central model definition concept:

    ModelDefinition
      id
      provider
      model_name
      capabilities
      context_window
      enabled
      optional cost/latency metadata

Acceptance:
- current Groq model is registered
- another provider/model can be represented
- lookup tests pass

#### Milestone 3: Agent Registry

Concept:

    AgentDefinition
      role
      implementation
      selected_model
      fallback_models
      enabled

Acceptance:
- Manager/Developer/Reviewer/Tester registered
- model assignment is configuration-driven

### WEEK 2 — PROJECT ORCHESTRATION

#### Milestone 4: Project entity

Add project-level state above Task.

Concept:

    Project
      id
      prompt
      status
      tasks
      progress
      created_at
      completed_at

Possible states:

    CREATED
    PLANNING
    EXECUTING
    TESTING
    REVIEWING
    BLOCKED
    APPROVED
    FAILED
    DONE

Do not duplicate Task logic inside Project.

#### Milestone 5: Structured Manager planning

Manager receives one large prompt.

Return a validated Pydantic plan:

    ProjectPlan
      summary
      requirements
      architecture
      subtasks[]
      dependencies[]
      acceptance_criteria

Critical workflow decisions must not depend on free-form prose.

#### Milestone 6: Dependency graph

Example:

    Task A
      |
      +--> Task B
      |
      +--> Task C
             |
             +--> Task D

Requirements:
- dependency cycles rejected
- ready tasks identifiable
- completed tasks unblock dependents
- independent tasks can eventually run concurrently

### WEEK 3 — TEST / DEBUG / REVIEW LOOP

#### Milestone 7: Structured Tester result

Concept:

    TestResult
      passed
      failed
      total
      failures[]
      command
      duration

Do not rely only on natural language.

#### Milestone 8: DebuggerAgent

Add DEBUGGER role.

Responsibilities:
- inspect failure
- inspect traceback
- inspect changed files
- identify root cause
- fix code
- rerun tests

Structured result:

    DebugResult
      root_cause
      changed_files
      commands_run
      fixed
      remaining_issue

#### Milestone 9: Reviewer loop

Reviewer returns:

    APPROVED
    NEEDS_FIX

with structured findings.

Flow:

    TEST PASS
       |
    REVIEW
       |
       +--> APPROVED -> continue
       |
       +--> NEEDS_FIX
                 |
              DEVELOPER
                 |
               TEST
                 |
              REVIEW

Add hard retry limits.

### WEEK 4 — TELEMETRY / UI / HARDENING

#### Milestone 10: Real telemetry

Potential event types:

    PROJECT_CREATED
    PROJECT_PLANNED
    AGENT_STARTED
    AGENT_THINKING
    AGENT_ACTION
    TOOL_STARTED
    TOOL_FINISHED
    FILE_CHANGED
    TEST_STARTED
    TEST_FINISHED
    DEBUG_STARTED
    REVIEW_STARTED
    REVIEW_RESULT
    MODEL_SELECTED
    RETRY_STARTED
    PROJECT_APPROVED
    PROJECT_FAILED

Only emit events for real facts.

#### Milestone 11: Professional dashboard

Build:
- project header
- progress
- task graph
- agent cards
- current action
- event timeline
- logs
- files
- tests
- errors
- model selection

#### Milestone 12: Production hardening

Add:
- persistent project/task state
- shutdown/resume
- execution timeouts
- retry policies
- model fallback
- workspace isolation
- shell resource limits
- structured logs
- secret handling
- API authentication if public
- rate limiting
- Docker isolation

## 25. EXACT DEVELOPMENT ORDER

Do not randomly jump between features.

Use:

    1. Inspect repository
    2. Run full tests
    3. Record baseline
    4. LLM abstraction
    5. Model Registry
    6. Agent Registry
    7. Per-role model configuration
    8. Project entity
    9. Manager structured planning
    10. Dependency graph
    11. Tester structured result
    12. Debugger
    13. Reviewer approval loop
    14. Retry/fallback
    15. Telemetry events
    16. Dashboard
    17. Persistence/resume
    18. Security hardening
    19. Full integration test
    20. Docker end-to-end test

After every milestone:

    python3 -m compileall app
    python3 -m pytest -q

Never continue after a broken baseline unless the failure is understood.

## 26. NEXT IMMEDIATE TASK

The next task is NOT UI redesign.

Start with:

    LLM abstraction + Model Registry + Agent Registry

Before changing code:
1. Inspect the current LLM/base agent implementation.
2. Determine which abstractions already exist.
3. Preserve working behavior.
4. Add the smallest clean abstraction that supports model selection.
5. Add tests.
6. Run the full suite.
7. Only then add model selection UI.

## 27. IMPORTANT DESIGN RULES

1. Roles must never be hard-coupled to providers/models.
2. Orchestrator coordinates; agents own agent-specific logic.
3. Critical workflow decisions should use structured Pydantic results.
4. Events must represent real facts, not fake progress.
5. Every autonomous loop needs retry limits and a terminal state.
6. Preserve working functionality.
7. Run tests before and after architecture changes.
8. Never weaken workspace or shell security.
9. New providers should be adapters/plugins.
10. Configuration should control models, roles, retries and strategies.
11. Real integration tests are required in addition to unit tests.
12. Do not redesign working architecture without inspecting current code first.

## 28. DEFINITION OF READY

The project is not final merely because pytest passes.

Meaningful readiness requires a user to submit a substantial project prompt and
the system to autonomously:

    plan
    decompose
    schedule
    implement
    test
    debug
    review
    retry
    report
    approve
    finish

with meaningful actions visible in the dashboard.

## 29. PRODUCTION-READY CHECKLIST

[ ] Agent/model abstraction
[ ] Provider adapters
[ ] Model Registry
[ ] Agent Registry
[ ] User model selection
[ ] Project entity
[ ] Structured planning
[ ] Dependency graph
[ ] Safe parallel execution
[ ] Structured Tester result
[ ] Debugger loop
[ ] Reviewer loop
[ ] Retry limits
[ ] Model fallback
[ ] Persistent state
[ ] Resume after restart
[ ] WebSocket telemetry
[ ] Professional dashboard
[ ] Workspace isolation
[ ] Shell security
[ ] Docker isolation
[ ] API security
[ ] Secrets protection
[ ] Resource limits
[ ] Comprehensive integration tests
[ ] Full Docker end-to-end test
[ ] Clear failure states
[ ] No infinite loops
[ ] Documentation

## 30. HANDOFF PROTOCOL FOR A NEW AI

At the start of a new session:

1. Read this file completely.
2. Inspect current git status.
3. Inspect recent changes.
4. Run:

       python3 -m compileall app
       python3 -m pytest -q

5. Compare actual results with this file.
6. The repository is authoritative if it is newer than this document.
7. Identify the first incomplete roadmap milestone.
8. Make the smallest coherent change.
9. Add/update tests.
10. Run validation.
11. Update this file with:
    - completed work
    - changed files
    - test result
    - known issues
    - next task

If uncertain, inspect existing code before inventing a new abstraction.

## 31. CURRENT HANDOFF SNAPSHOT

Last known strong baseline:
- Full pytest: All tests passing successfully (Coverage: ~80%)
- New layers added:
  1. `app/llm/model_registry.py` - Centralized model definitions and dynamic client factory.
  2. `app/agents/registry.py` - Agent registry supporting dynamic role-to-model instantiation via LLMRouter.
- Model-agnostic design: Agent roles no longer hardcoded to specific models; controlled via settings and registries.

NEXT MILESTONE:
- Project entity and structured Manager planning (Milestone 4 & 5).

## 32. FINAL PRINCIPLE

Build for today's models and future stronger models.

Do not optimize the architecture around the current model's capabilities.

The architecture should remain stable while:

    models improve
    providers change
    new agent roles appear
    new execution strategies appear
    projects become larger

The durable abstraction is:

    USER
      -> PROJECT
      -> PLAN
      -> TASK GRAPH
      -> AGENTS
      -> MODEL ROUTER
      -> TOOLS / WORKSPACE
      -> TEST / DEBUG / REVIEW
      -> APPROVAL
      -> DONE

Preserve this core architecture.
