
from pathlib import Path
import re
import json

import typer

from agentforge import __version__
from agentforge.generator import generate_project
from agentforge.generator import generate_agent

app = typer.Typer(
    name="agentforge",
    help="Generate production-minded Python applications.",
    no_args_is_help=True,
)


@app.command()
def version() -> None:
    """Display the AgentForge version."""
    typer.echo(f"AgentForge {__version__}")


@app.command()
def init(
    project_name: str = typer.Argument(
        ...,
        help="Name of the project to generate, e.g. claims-assistant.",
    ),
    path: Path | None = typer.Option(
        None,
        "--path",
        "-p",
        help="Parent directory where the project will be created.",
    ),
) -> None:
    """Generate a new AgentForge application."""
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", project_name):
        raise typer.BadParameter(
            "Use letters, numbers, hyphens, and underscores in the project name."
        )

    parent_dir = (path or Path.cwd()).expanduser().resolve()

    try:
        project_dir = generate_project(project_name, parent_dir)
    except FileExistsError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    except OSError as exc:
        typer.echo(f"Could not generate project: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    except ValueError as exc:
        typer.echo(f"Invalid project: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    typer.echo(f"Project created successfully: {project_dir}")
    typer.echo("")
    typer.echo("Next steps:")
    typer.echo(f"  cd {project_name}")
    typer.echo('  python -m pip install -e ".[dev]"')
    typer.echo(f"  python -m {project_name.replace('-', '_')}")

agent_app = typer.Typer(
    name="agent",
    help="Generate and manage application agents.",
    no_args_is_help=True,
)

app.add_typer(agent_app, name="agent")


@agent_app.command("create")
def create_agent(
    agent_name: str = typer.Argument(
        ...,
        help="Name of the agent to generate.",
    ),
    path: Path = typer.Option(
        Path.cwd(),
        "--path",
        "-p",
        help="Existing generated project directory.",
    ),
) -> None:
    """Generate a production-style agent scaffold."""
    try:
        created_files = generate_agent(agent_name, path)
    except (ValueError, FileExistsError, OSError) as exc:
        typer.echo(f"Agent generation failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    typer.echo(f"Agent '{agent_name}' generated successfully.")
    typer.echo("Created files:")
    for file_path in created_files:
        typer.echo(f"  {file_path}")



guardrail_app = typer.Typer(
    help="Configure guardrails for individual agents."
)



def generate_guardrails_module() -> str:
    """Return the source code for the generated guardrail engine."""

    return r'''import json
import re
from pathlib import Path
from typing import Any


class GuardrailViolationError(ValueError):
    """Raised when a guardrail blocks input or output."""


class GuardrailEngine:
    """Validate agent input and output using guardrails.json."""

    PATTERNS = {
        "email": (
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
        ),
        "credit_card": r"\b(?:\d[ -]*?){13,19}\b",
        "password": r"(?i)\bpassword\s*[:=]\s*\S+",
        "api_key": (
            r"\b(?:sk-[A-Za-z0-9_-]{10,}|"
            r"(?:api[_-]?key)\s*[:=]\s*\S+)\b"
        ),
    }

    def __init__(self, config_path: Path) -> None:
        self.config_path = Path(config_path)

        with self.config_path.open("r", encoding="utf-8") as file:
            self.config: dict[str, Any] = json.load(file)

    def _should_apply(self, stage: str) -> bool:
        if not self.config.get("enabled", False):
            return False

        scope = self.config.get("apply_to", "both")

        if isinstance(scope, str):
            scope = [scope]

        return "both" in scope or stage in scope

    def validate_input(self, text: str) -> str:
        if not self._should_apply("input"):
            return text

        return self._validate(text)

    def validate_output(self, text: str) -> str:
        if not self._should_apply("output"):
            return text

        return self._validate(text)

    def _validate(self, text: str) -> str:
        if not isinstance(text, str):
            raise TypeError("Guardrails require text content.")

        result = text
        pii_rules = self.config.get("pii", {})

        for name, pattern in self.PATTERNS.items():
            rule = pii_rules.get(name, {})

            if not rule.get("enabled", False):
                continue

            action = rule.get("action", "redact")

            if action not in {"block", "redact"}:
                raise ValueError(
                    f"Unsupported action for guardrail '{name}'."
                )

            if action == "block" and re.search(pattern, result):
                raise GuardrailViolationError(
                    f"Content blocked by the '{name}' guardrail."
                )

            if action == "redact":
                result = re.sub(
                    pattern,
                    f"[REDACTED_{name.upper()}]",
                    result,
                )

        for rule in self.config.get("custom_rules", []):
            if not rule.get("enabled", True):
                continue

            pattern = rule.get("pattern")
            if not pattern:
                continue

            try:
                matched = re.search(pattern, result)
            except re.error as exc:
                raise ValueError(
                    f"Invalid custom guardrail regex: "
                    f"{rule.get('name', 'unnamed')}"
                ) from exc

            if not matched:
                continue

            action = rule.get("action", "block")

            if action == "block":
                raise GuardrailViolationError(
                    "Content blocked by custom guardrail "
                    f"'{rule.get('name', 'unnamed')}'."
                )

            if action == "redact":
                result = re.sub(pattern, "[REDACTED]", result)
            else:
                raise ValueError(
                    f"Unsupported custom guardrail action: {action}"
                )

        return result
'''



def integrate_guardrails_into_service(service_path: Path) -> str:
    """Integrate guardrail validation into an AgentForge AgentService."""

    source = service_path.read_text(encoding="utf-8")

    guardrail_import = "from .guardrails import GuardrailEngine"

    # Prevent duplicate integration.
    if guardrail_import in source:
        required = (
            "self.guardrails = GuardrailEngine(",
            "self.guardrails.validate_input(",
            "self.guardrails.validate_output(",
        )

        missing = [item for item in required if item not in source]
        if missing:
            raise ValueError(
                "service.py contains an incomplete guardrail integration. "
                f"Missing: {', '.join(missing)}"
            )

        return source

    # Insert imports after the existing imports and before the logger.
    logger_anchor = "logger = get_logger(__name__)"

    if source.count(logger_anchor) != 1:
        raise ValueError(
            "Could not uniquely locate logger initialization in service.py."
        )

    source = source.replace(
        logger_anchor,
        "from pathlib import Path\n"
        f"{guardrail_import}\n\n"
        f"{logger_anchor}",
        1,
    )

    # Initialize the engine in AgentService.__init__.
    init_anchor = "        self._system_prompt = system_prompt"

    if source.count(init_anchor) != 1:
        raise ValueError(
            "Could not locate self._system_prompt = system_prompt."
        )

    source = source.replace(
        init_anchor,
        init_anchor
        + '\n        self.guardrails = GuardrailEngine('
        'config_path=Path(__file__).with_name("guardrails.json"))',
        1,
    )

    # Validate user input before it reaches the model.
    input_anchor = "                    HumanMessage(content=request.task),"

    if source.count(input_anchor) != 1:
        raise ValueError(
            "Could not locate HumanMessage(content=request.task)."
        )

    source = source.replace(
        "            result = self._model.invoke(\n",
        "            validated_task = self.guardrails.validate_input(\n"
        "                request.task\n"
        "            )\n\n"
        "            result = self._model.invoke(\n",
        1,
    )

    source = source.replace(
        input_anchor,
        "                    HumanMessage(content=validated_task),",
        1,
    )

    # Validate model output before creating AgentResponse.
    output_anchor = "            content = result.content"

    if source.count(output_anchor) != 1:
        raise ValueError(
            "Could not locate content = result.content."
        )

    source = source.replace(
        output_anchor,
        "            content = self.guardrails.validate_output(\n"
        "                result.content\n"
        "            )",
        1,
    )

    return source


def add_guardrail(
    project_path: Path | None = typer.Option(
        None,
        "--project-path",
        "-p",
        help="Path to the generated application.",
    ),
    agent: str | None = typer.Option(
        None,
        "--agent",
        "-a",
        help="Agent to configure.",
    ),
) -> None:
    """Configure and integrate guardrails for a selected agent."""

    root = (project_path or Path.cwd()).expanduser().resolve()

    if not (root / "pyproject.toml").is_file():
        typer.echo(f"Not an application project: {root}", err=True)
        raise typer.Exit(code=1)

    src_dir = root / "src"
    packages = (
        [
            item
            for item in src_dir.iterdir()
            if item.is_dir() and (item / "__init__.py").is_file()
        ]
        if src_dir.is_dir()
        else []
    )

    if len(packages) != 1:
        typer.echo(
            "Expected exactly one Python package under src/.",
            err=True,
        )
        raise typer.Exit(code=1)

    agents_dir = packages[0] / "agents"
    agents = (
        [
            item
            for item in agents_dir.iterdir()
            if item.is_dir() and (item / "service.py").is_file()
        ]
        if agents_dir.is_dir()
        else []
    )

    if not agents:
        typer.echo("No named agents found.", err=True)
        raise typer.Exit(code=1)

    # Select the target agent.
    agent_names = {item.name for item in agents}

    if agent is None:
        typer.echo("\nAvailable agents:")
        for index, item in enumerate(agents, start=1):
            typer.echo(f"{index}. {item.name}")

        selected = typer.prompt("Enter the agent name").strip()
    else:
        selected = agent.strip()

    if selected not in agent_names:
        typer.echo(f"Agent '{selected}' was not found.", err=True)
        raise typer.Exit(code=1)

    agent_dir = agents_dir / selected
    service_path = agent_dir / "service.py"
    config_path = agent_dir / "guardrails.json"
    guardrails_path = agent_dir / "guardrails.py"

    # Choose validation scope.
    typer.echo("\nChoose guardrail scope:")
    typer.echo("1. Input only")
    typer.echo("2. Output only")
    typer.echo("3. Both input and output")

    scope_choice = typer.prompt("Select scope (1/2/3)", default="3")

    scope_options = {
        "1": ["input"],
        "2": ["output"],
        "3": ["input", "output"],
    }

    if scope_choice not in scope_options:
        typer.echo("Invalid scope selection.", err=True)
        raise typer.Exit(code=1)

    # Choose the rule set.
    typer.echo("\nChoose guardrail type:")
    typer.echo("1. Default guardrails")
    typer.echo("2. Default + custom guardrails")

    guardrail_choice = typer.prompt(
        "Select type (1/2)",
        default="1",
    )

    if guardrail_choice not in {"1", "2"}:
        typer.echo("Invalid guardrail selection.", err=True)
        raise typer.Exit(code=1)

    config = {
        "enabled": True,
        "apply_to": scope_options[scope_choice],
        "pii": {
            "email": {"enabled": True, "action": "redact"},
            "credit_card": {"enabled": True, "action": "redact"},
            "password": {"enabled": True, "action": "block"},
            "api_key": {"enabled": True, "action": "block"},
        },
        "custom_rules": [],
    }

    # Collect custom rules.
    if guardrail_choice == "2":
        while typer.confirm("Add a custom rule?", default=False):
            name = typer.prompt("Rule name").strip()

            if not name:
                typer.echo("Rule name cannot be empty.", err=True)
                raise typer.Exit(code=1)

            pattern = typer.prompt("Python regex pattern")

            try:
                re.compile(pattern)
            except re.error as exc:
                typer.echo(f"Invalid regex: {exc}", err=True)
                raise typer.Exit(code=1) from exc

            action = typer.prompt(
                "Action: block or redact",
                default="block",
            ).strip().lower()

            if action not in {"block", "redact"}:
                typer.echo("Action must be block or redact.", err=True)
                raise typer.Exit(code=1)

            config["custom_rules"].append(
                {
                    "name": name,
                    "pattern": pattern,
                    "action": action,
                    "enabled": True,
                }
            )

    # Confirm replacement of existing configuration.
    if config_path.exists():
        if not typer.confirm(
            "Existing guardrail configuration will be replaced. Continue?",
            default=False,
        ):
            typer.echo("Cancelled; existing configuration was preserved.")
            raise typer.Exit()

    if not typer.confirm(
        f"Apply guardrails to '{selected}' "
        f"({', '.join(config['apply_to'])})?",
        default=True,
    ):
        typer.echo("Cancelled.")
        raise typer.Exit()

    # Prepare the service integration before writing anything.
    
    # Prepare all generated files before writing anything.
    try:
        original_service = service_path.read_text(encoding="utf-8")
        updated_service = integrate_guardrails_into_service(service_path)

        updated_guardrails = generate_guardrails_module()
        updated_config = json.dumps(config, indent=2) + "\n"

        # Validate Python syntax before writing files.
        compile(updated_service, str(service_path), "exec")
        compile(updated_guardrails, str(guardrails_path), "exec")
        json.loads(updated_config)

    except (OSError, ValueError, SyntaxError) as exc:
        typer.echo(f"Could not prepare guardrails: {exc}", err=True)
        raise typer.Exit(code=1) from exc


    service_backup = service_path.with_suffix(".py.guardrails.bak")
    engine_backup = guardrails_path.with_suffix(".py.guardrails.bak")

    try:
        original_config = (
            config_path.read_bytes() if config_path.exists() else None
        )
        original_guardrails = (
            guardrails_path.read_bytes() if guardrails_path.exists() else None
        )

        # Preserve original files before changing them.
        if updated_service != original_service and not service_backup.exists():
            service_backup.write_text(original_service, encoding="utf-8")

        if (
            original_guardrails is not None
            and not engine_backup.exists()
        ):
            engine_backup.write_bytes(original_guardrails)

        try:
            service_path.write_text(updated_service, encoding="utf-8")
            guardrails_path.write_text(
                updated_guardrails,
                encoding="utf-8",
            )
            config_path.write_text(
                updated_config,
                encoding="utf-8",
            )

        except OSError:
            # Roll back if any file write fails.
            service_path.write_text(original_service, encoding="utf-8")

            if original_guardrails is not None:
                guardrails_path.write_bytes(original_guardrails)
            elif guardrails_path.exists():
                guardrails_path.unlink()

            if original_config is not None:
                config_path.write_bytes(original_config)
            elif config_path.exists():
                config_path.unlink()

            raise

    except OSError as exc:
        typer.echo(f"Could not save guardrail changes: {exc}", err=True)
        raise typer.Exit(code=1) from exc


    
    typer.echo("\nGuardrails configured successfully.")
    typer.echo(f"Agent: {selected}")
    typer.echo(f"Scope: {', '.join(config['apply_to'])}")
    typer.echo(f"Service updated: {service_path}")
    typer.echo(f"Guardrail engine generated: {guardrails_path}")
    typer.echo(f"Configuration saved: {config_path}")

    if service_backup.exists():
        typer.echo(f"Original service backup: {service_backup}")

    if engine_backup.exists():
        typer.echo(f"Original guardrail engine backup: {engine_backup}")



guardrail_app.command("add")(add_guardrail)
app.add_typer(guardrail_app, name="guardrail")

if __name__ == "__main__":
    app()
