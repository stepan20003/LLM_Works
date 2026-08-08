import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch
from pydantic import BaseModel, SecretStr

from app.llm.openai_client import OpenAIClient
from app.llm.router import LLMRouter
from app.schemas.enums import AgentRole
from app.exceptions.base import ConfigurationError


class MockResponseSchema(BaseModel):
    summary: str
    confidence: float


@pytest_asyncio.fixture
async def llm_router():
    default_client = OpenAIClient(
        component_id="default-llm",
        model_name="gpt-4o-mini",
        api_key=SecretStr("fake-key-1")
    )
    special_client = OpenAIClient(
        component_id="special-llm",
        model_name="gpt-4o",
        api_key=SecretStr("fake-key-2")
    )
    
    router = LLMRouter(default_client=default_client)
    await router.initialize()
    
    # Պարտադիր ինիցիալիզացնում ենք հատուկ client-ը մինչև գրանցելը
    await special_client.initialize()
    router.register_role_client(AgentRole.REVIEWER, special_client)
    
    yield router
    await router.shutdown()


@pytest.mark.asyncio
async def test_llm_router_initialization_and_routing(llm_router: LLMRouter):
    assert llm_router.is_initialized is True
    assert await llm_router.health_check() is True

    reviewer_client = llm_router.get_client_for_role(AgentRole.REVIEWER)
    assert reviewer_client.model_name == "gpt-4o"
    
    developer_client = llm_router.get_client_for_role(AgentRole.DEVELOPER)
    assert developer_client.model_name == "gpt-4o-mini"


@pytest.mark.asyncio
async def test_openai_client_generate_completion():
    # Ստեղծում ենք իրական client (առանց ցանցային զանգերի)
    client = OpenAIClient(
        component_id="test-client",
        model_name="gpt-4o",
        api_key=SecretStr("fake-key")
    )
    await client.initialize()

    # Մոք ենք անում միայն ցանցային զանգ կատարող մեթոդը
    with patch.object(client.client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
        mock_msg = AsyncMock()
        mock_msg.content = "Hello from Mock LLM!"
        mock_choice = AsyncMock()
        mock_choice.message = mock_msg
        mock_create.return_value.choices = [mock_choice]

        response = await client.generate_completion(
            prompt="Say hello", 
            system_prompt="You are a helpful bot."
        )

        assert response == "Hello from Mock LLM!"
        mock_create.assert_called_once()
        
        call_kwargs = mock_create.call_args.kwargs
        assert call_kwargs["model"] == "gpt-4o"
        assert len(call_kwargs["messages"]) == 2
        assert call_kwargs["messages"][0]["role"] == "system"

    await client.shutdown()


@pytest.mark.asyncio
async def test_openai_client_generate_structured():
    client = OpenAIClient(
        component_id="test-structured",
        model_name="gpt-4o",
        api_key=SecretStr("fake-key")
    )
    await client.initialize()

    # Մոք ենք անում parsed completions մեթոդը
    with patch.object(client.client.beta.chat.completions, 'parse', new_callable=AsyncMock) as mock_parse:
        mock_parsed_response = MockResponseSchema(summary="All good", confidence=0.99)
        mock_msg = AsyncMock()
        mock_msg.parsed = mock_parsed_response
        mock_choice = AsyncMock()
        mock_choice.message = mock_msg
        mock_parse.return_value.choices = [mock_choice]

        response = await client.generate_structured(
            prompt="Analyze this code", 
            response_schema=MockResponseSchema
        )

        assert isinstance(response, MockResponseSchema)
        assert response.summary == "All good"
        assert response.confidence == 0.99

    await client.shutdown()


@pytest.mark.asyncio
async def test_openai_client_missing_api_key_initialization_fails():
    client = OpenAIClient(
        component_id="bad-client",
        model_name="gpt-4o",
        api_key=SecretStr("")
    )
    
    # Դիտավորյալ exception ենք նետում AsyncOpenAI ստեղծելիս
    with patch("app.llm.openai_client.AsyncOpenAI", side_effect=Exception("Bad config")):
        with pytest.raises(ConfigurationError):
            await client.initialize()