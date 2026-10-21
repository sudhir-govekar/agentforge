
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from __PACKAGE_NAME__.agents.contracts import AgentRequest
from __PACKAGE_NAME__.agents.service import AgentService


class AgentGraphState(TypedDict, total=False):
    """Typed state passed between graph nodes."""

    task: str
    conversation_id: str | None
    answer: str
    agent_name: str
    model_name: str


def build_agent_graph(service: AgentService):
    """Build a compiled graph with the agent service injected."""

    def execute_agent(state: AgentGraphState) -> dict:
        request = AgentRequest(
            task=state["task"],
            conversation_id=state.get("conversation_id"),
        )
        response = service.run(request)

        return {
            "answer": response.answer,
            "agent_name": response.agent_name,
            "model_name": response.model_name,
        }

    builder = StateGraph(AgentGraphState)
    builder.add_node("execute_agent", execute_agent)
    builder.add_edge(START, "execute_agent")
    builder.add_edge("execute_agent", END)

    return builder.compile()
