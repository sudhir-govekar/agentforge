import argparse

from __PACKAGE_NAME__.agents.bootstrap import create_agent_graph
from __PACKAGE_NAME__.agents.contracts import AgentRequest
from __PACKAGE_NAME__.bootstrap import configure_application


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the generated agent.")
    parser.add_argument("--task", required=True, help="Task for the agent.")
    parser.add_argument("--conversation-id", default=None)
    args = parser.parse_args()

    configure_application()

    request = AgentRequest(
        task=args.task,
        conversation_id=args.conversation_id,
    )

    graph = create_agent_graph()
    result = graph.invoke(request.model_dump())

    print(result["answer"])


if __name__ == "__main__":
    main()