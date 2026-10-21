
import sys

from pydantic import ValidationError

from __PACKAGE_NAME__.core.config import get_settings
from __PACKAGE_NAME__.llm.factory import create_chat_model


def main() -> int:
    try:
        settings = get_settings()
        model = create_chat_model(settings)

        print(
            f"Testing provider={settings.llm_provider}, "
            f"model={settings.llm_model}..."
        )

        response = model.invoke("Reply with exactly: OK")
        print("LLM connection successful.")
        print(f"Response: {response.content}")
        return 0

    except ValidationError as exc:
        print("Configuration validation failed.")
        for error in exc.errors(include_input=False):
            location = ".".join(str(part) for part in error["loc"])
            print(f"- {location}: {error['msg']}")
        return 2

    except Exception as exc:
        # Avoid printing raw SDK errors that could expose request details.
        print("LLM connection test failed.")
        print(f"Error type: {type(exc).__name__}")
        print(
            "Check credentials, model availability, network access, "
            "and the provider service."
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
