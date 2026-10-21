
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import ValidationError

from __PACKAGE_NAME__.agents.contracts import AgentRequest, AgentResponse
from __PACKAGE_NAME__.agents.exceptions import AgentExecutionError
from __PACKAGE_NAME__.core.logging import get_logger


logger = get_logger(__name__)


class AgentService:
    """Execute a task using an injected LangChain chat model."""

    def __init__(
        self,
        model: BaseChatModel,
        *,
        agent_name: str = "general-agent",
        system_prompt: str = (
            "You are a helpful assistant. "
            "Answer accurately and clearly. "
            "If you do not know something, say so."
        ),
    ) -> None:
        self._model = model
        self._agent_name = agent_name
        self._system_prompt = system_prompt

    def run(self, request: AgentRequest) -> AgentResponse:
        """Validate input, invoke the model, and return a typed response."""
        try:
            logger.info(
                "agent_execution_started",
                agent_name=self._agent_name,
                conversation_id=request.conversation_id,
            )

            result = self._model.invoke(
                [
                    SystemMessage(content=self._system_prompt),
                    HumanMessage(content=request.task),
                ]
            )

            # The standard chat model returns an AI message.
            content = result.content
            if not isinstance(content, str) or not content.strip():
                raise AgentExecutionError(
                    "The model returned an empty or non-text response."
                )

            response = AgentResponse(
                answer=content,
                agent_name=self._agent_name,
                model_name=str(
                    getattr(self._model, "model_name", None)
                    or getattr(self._model, "model", None)
                    or "configured-model"
                ),
                conversation_id=request.conversation_id,
            )

            logger.info(
                "agent_execution_completed",
                agent_name=self._agent_name,
                conversation_id=request.conversation_id,
            )
            return response

        except AgentExecutionError:
            raise
        except Exception as exc:
            logger.exception(
                "agent_execution_failed",
                agent_name=self._agent_name,
                conversation_id=request.conversation_id,
                error_type=type(exc).__name__,
            )
            raise AgentExecutionError(
                "The agent could not complete the requested task."
            ) from exc
