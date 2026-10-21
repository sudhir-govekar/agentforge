
from langgraph.graph import END, START, MessagesState, StateGraph

from __PACKAGE_NAME__.llm.factory import create_chat_model


def build_graph():
    """Build a minimal LangGraph workflow using the configured model."""

    model = create_chat_model()

    def assistant(state: MessagesState) -> dict:
        response = model.invoke(state["messages"])
        return {"messages": [response]}

    workflow = StateGraph(MessagesState)
    workflow.add_node("assistant", assistant)
    workflow.add_edge(START, "assistant")
    workflow.add_edge("assistant", END)

    return workflow.compile()
