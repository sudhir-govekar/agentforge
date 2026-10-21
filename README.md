# AgentForge --- Setup and Run Guide

This README documents the AgentForge workflow built so far: installing
the local CLI, generating a project and agent, configuring guardrails,
and running the agent.

> **Example paths used below** - AgentForge repository:
> `/Users/sudhir/Documents/Innovation_ideas_on_ai/agentforge` -
> Generated application:
> `/Users/sudhir/Documents/Innovation_ideas_on_ai/agentforge/bot_app` -
> Example agent: `rag_agent_1`
>
> Adjust these paths if your folders differ.

## 1. Architecture and project structure

``` text
agentforge/
├── .venv/
├── packages/
│   └── agentforge-cli/
│       └── src/agentforge/
│           ├── cli.py          # Typer commands: init, agent, guardrail
│           └── generator.py    # Project/agent scaffolding
└── bot_app/                    # Generated application
    ├── pyproject.toml
    └── src/bot_app/agents/rag_agent_1/
        ├── service.py          # Model call and guardrail hooks
        ├── graph.py            # Agent workflow
        ├── bootstrap.py        # Graph/service setup
        ├── runner.py           # Command-line entry point
        ├── guardrails.py       # GuardrailEngine implementation
        └── guardrails.json     # Rules and configuration
```

``` mermaid
flowchart TD
    A["runner.py"] --> B["Agent graph"]
    B --> C["AgentService.run()"]
    C --> D["Input guardrails"]
    D --> E["Chat model"]
    E --> F["Output guardrails"]
    F --> G["Agent response"]
    H["guardrails.json"] --> I["GuardrailEngine"]
    I --> D
    I --> F
```

The configured scope controls whether validation runs on input, output,
or both. The exact generated files can vary with the generator version.

## 2. Prerequisites

-   Python compatible with the project's `pyproject.toml`.
-   A virtual environment.
-   Required LLM provider configuration and credentials for the
    generated app.

Open a terminal and activate the existing virtual environment:

``` bash
cd /Users/sudhir/Documents/Innovation_ideas_on_ai/agentforge
source .venv/bin/activate
python --version
```

If the virtual environment does not exist yet, create it from the
AgentForge repository root:

``` bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

## 3. Install AgentForge CLI

**Working directory: AgentForge repository root**

``` bash
cd /Users/sudhir/Documents/Innovation_ideas_on_ai/agentforge
source .venv/bin/activate
python -m pip install -e "packages/agentforge-cli[dev]"
```

Verify the CLI:

``` bash
agentforge version
agentforge --help
agentforge agent --help
agentforge guardrail --help
```

Because the CLI is installed in editable mode, source changes are
reflected without building a wheel. Re-run the install command if
packaging or dependencies change.

## 4. Generate a new application

**Working directory: AgentForge repository root**

Choose a project name that does not already exist:

``` bash
cd /Users/sudhir/Documents/Innovation_ideas_on_ai/agentforge
agentforge init claims_assistant --path .
```

This should create a `claims_assistant` directory under the current
directory. Do not run this against an existing project directory unless
you have checked the generator's overwrite behavior.

**Working directory: generated application root**

``` bash
cd /Users/sudhir/Documents/Innovation_ideas_on_ai/agentforge/claims_assistant
python -m pip install -e ".[dev]"
```

Use the optional dependency group declared by the generated project's
`pyproject.toml`.

## 5. Generate a named agent

To create an agent in the existing `bot_app` project:

**Working directory: `bot_app` root**

``` bash
cd /Users/sudhir/Documents/Innovation_ideas_on_ai/agentforge/bot_app
agentforge agent create rag_agent_1
```

To pass the project path explicitly from another directory:

``` bash
agentforge agent create rag_agent_1 \
  --path /Users/sudhir/Documents/Innovation_ideas_on_ai/agentforge/bot_app
```

Use a different agent name if `rag_agent_1` already exists. Check
`agentforge agent create --help` for options supported by your installed
version.

## 6. Configure guardrails

The `guardrail add` command prompts for scope and rule selection.

**Recommended: working directory is the generated application root**

``` bash
cd /Users/sudhir/Documents/Innovation_ideas_on_ai/agentforge/bot_app
agentforge guardrail add --agent rag_agent_1
```

Alternatively, run it from another directory with an explicit project
path:

``` bash
agentforge guardrail add \
  --project-path /Users/sudhir/Documents/Innovation_ideas_on_ai/agentforge/bot_app \
  --agent rag_agent_1
```

Follow the prompts: 1. Choose input only, output only, or both. 2.
Choose default guardrails or default plus custom rules. 3. Confirm
replacement if a `guardrails.json` already exists. 4. Confirm applying
the selected configuration.

Expected files:

``` text
bot_app/src/bot_app/agents/rag_agent_1/
├── service.py
├── guardrails.py
└── guardrails.json
```

-   `service.py` should call `validate_input()` before the model and
    `validate_output()` before returning the response.
-   `guardrails.py` defines `GuardrailEngine`.
-   `guardrails.json` stores the enabled flag, scope, PII rules, and
    custom rules.

Verify the files and integration. **Run these commands from the
`bot_app` root:**

``` bash
ls -l src/bot_app/agents/rag_agent_1/guardrails*
grep -nE "GuardrailEngine|validate_input|validate_output" \
  src/bot_app/agents/rag_agent_1/service.py
cat src/bot_app/agents/rag_agent_1/guardrails.json
```

## 7. Install and run `bot_app`

**Working directory: `bot_app` root**

``` bash
cd /Users/sudhir/Documents/Innovation_ideas_on_ai/agentforge/bot_app
source ../.venv/bin/activate
python -m pip install -e ".[dev]"
python -m bot_app.agents.rag_agent_1.runner \
  --task "Explain how RAG works in simple terms."
```

The install command makes the generated app's `src` package importable
in the active environment. Repeat it when app dependencies or packaging
settings change.

### Other run examples

Normal request:

``` bash
python -m bot_app.agents.rag_agent_1.runner \
  --task "Explain RAG with a simple example."
```

Email redaction test:

``` bash
python -m bot_app.agents.rag_agent_1.runner \
  --task "Summarize this contact: sudhir.test@example.com"
```

Password blocking test:

``` bash
python -m bot_app.agents.rag_agent_1.runner \
  --task "Process this record: password=DemoPass123!"
```

API-key blocking test (dummy value only):

``` bash
python -m bot_app.agents.rag_agent_1.runner \
  --task "Check this test key: sk-test-1234567890abcdef"
```

Never use real credentials or payment details in guardrail tests.

## 8. Default guardrails

The default rules discussed so far are:

  Rule          Action     Expected behavior
  ------------- ---------- --------------------------------------------------
  Email         `redact`   Replace a matching email with a redaction marker
  Credit card   `redact`   Replace a matching card-like number
  Password      `block`    Reject matching content
  API key       `block`    Reject matching content

Actual behavior depends on the regular expressions in `guardrails.py`
and the active settings in `guardrails.json`. Confirm that `enabled` is
`true` and `apply_to` includes the stage being tested.

A traceback alone does not prove a guardrail worked. For blocking tests,
verify that the exception is a guardrail violation and that the model
was not called. Test output validation separately with a mocked model
response.

## 9. Add custom guardrails

**Working directory: generated application root**

``` bash
agentforge guardrail add --agent rag_agent_1
```

Choose **Default + custom guardrails** and provide a rule name, Python
regex pattern, and action (`block` or `redact`). Review the generated
`guardrails.json` and make sure its fields match the current engine
implementation.

## 10. Troubleshooting

### `ModuleNotFoundError` for `bot_app`

-   Confirm you are in the generated application root.
-   Activate the intended virtual environment.
-   Run `python -m pip install -e ".[dev]"` from the generated app root.
-   Check that `src/bot_app/` exists.

### `ModuleNotFoundError` for `bot_app.agents.rag_agent_1.guardrails`

From the `bot_app` root, run:

``` bash
ls -l src/bot_app/agents/rag_agent_1/guardrails.py
ls -l src/bot_app/agents/rag_agent_1/guardrails.json
```

If `guardrails.py` is missing, fix the CLI generator and rerun
`agentforge guardrail add --agent rag_agent_1`.

### `NameError: backup_path is not defined`

The success-message block in
`packages/agentforge-cli/src/agentforge/cli.py` may still refer to an
old variable. Use the current names (`service_backup` and
`engine_backup`) consistently.

### CLI changes do not appear

From the AgentForge repository root:

``` bash
python -m pip install -e "packages/agentforge-cli[dev]"
```

### A guardrail does not redact or block

-   Check `enabled` and `apply_to` in `guardrails.json`.
-   Check the specific rule's `enabled` and `action` values.
-   Check that the test text matches the regex in `guardrails.py`.
-   Test output validation independently with a mocked model response.

## 11. Command reference by directory

  --------------------------------------------------------------------------------------------------------------------
  Run from                Command                                                              Purpose
  ----------------------- -------------------------------------------------------------------- -----------------------
  AgentForge repository   `agentforge version`                                                 Show CLI version
  root                                                                                         

  AgentForge repository   `python -m pip install -e "packages/agentforge-cli[dev]"`            Install/update CLI
  root                                                                                         

  AgentForge repository   `agentforge init claims_assistant --path .`                          Create a new app
  root                                                                                         

  Generated application   `agentforge agent create rag_agent_1`                                Create an agent
  root                                                                                         

  Generated application   `agentforge guardrail add --agent rag_agent_1`                       Configure guardrails
  root                                                                                         

  `bot_app` root          `python -m bot_app.agents.rag_agent_1.runner --task "Explain RAG"`   Run the example agent
  --------------------------------------------------------------------------------------------------------------------

The final command is specific to the `bot_app` Python package. For
another generated project, substitute its Python package name.

## 12. Production-readiness checklist

The current work establishes scaffolding, CLI commands, agent execution,
and regex-based guardrails. Before production use:

-   Add unit tests for every built-in and custom rule.
-   Add integration tests proving blocked input never reaches the model.
-   Test output validation with deterministic mocked responses.
-   Validate configuration schema and handle missing/malformed config.
-   Return clean errors for guardrail violations rather than raw
    tracebacks.
-   Avoid logging sensitive prompt contents or secrets.
-   Treat regex-based PII detection as a baseline, not a complete
    security boundary.
-   Confirm model-provider settings and credentials are configured in
    the generated app.
