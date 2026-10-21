from __PACKAGE_NAME__.agents.graph import build_agent_graph
from __PACKAGE_NAME__.agents.service import AgentService
from __PACKAGE_NAME__.llm.factory import create_chat_model


def create_agent_graph():
    """Construct the model, service, and compiled graph."""
    model = create_chat_model()

    service = AgentService(
        model,
        agent_name="claims-agent",
        system_prompt=(
            "You are a claims-domain assistant. "
            "Provide clear, accurate responses. "
            "Do not invent policy terms or claim facts."
        ),
    )

    return build_agent_graph(service)