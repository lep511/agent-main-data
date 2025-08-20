# Durable Execution with Temporal

**Pydantic AI** enables you to build **durable agents** that:

- Preserve progress across transient API failures, errors, and restarts.
- Support long-running, asynchronous, and human-in-the-loop workflows.
- Provide production-grade reliability.
- Fully integrate with **streaming** and **MCP**, while adding **fault tolerance**.

**Temporal** is a widely used **durable execution platform** natively supported by Pydantic AI.  
The integration relies only on Pydantic AI’s public interface, making it a reference for integrating with other durable execution systems as well.

---

## Durable Execution with Temporal

### How it works
- Temporal ensures program resilience by **retrying after crashes or failures** until completion.
- It uses **replay mechanisms** to recover from failures:
  - **Deterministic parts (Workflows):** Always replayed consistently with the same inputs.  
  - **Non-deterministic parts (Activities):** Perform I/O or external operations, restarted from the beginning if they fail.

### Comparison
If you are familiar with **Celery**, Temporal activities are similar to Celery tasks but provide more **flexibility, fault tolerance, and workflow control**.

📖 See the [Temporal documentation](https://docs.temporal.io/) for more details.

---

## Agent Integration with Temporal

When integrating Pydantic AI agents with Temporal:

- **I/O operations** (model requests, tool calls, MCP communication) → must run as **activities**.  
- **Agent coordination logic** (the run loop) → lives inside the **workflow**.  

This separation ensures **fault tolerance** and **durable recovery**.

---

## Install

```bash
brew install temporal
temporal server start-dev
```

---

## Architecture

```
            +---------------------+
            |   Temporal Server   |      (Stores workflow state,
            +---------------------+       schedules activities,
                     ^                    persists progress)
                     |
        Save state,  |   Schedule Tasks,
        progress,    |   load state on resume
        timeouts     |
                     |
+------------------------------------------------------+
|                      Worker                          |
|   +----------------------------------------------+   |
|   |              Workflow Code                   |   |
|   |       (Agent Run Loop)                       |   |
|   +----------------------------------------------+   |
|          |          |                |               |
|          v          v                v               |
|   +-----------+ +------------+ +-------------+       |
|   | Activity  | | Activity   | |  Activity   |       |
|   | (Tool)    | | (MCP Tool) | | (Model API) |       |
|   +-----------+ +------------+ +-------------+       |
|         |           |                |               |
+------------------------------------------------------+
          |           |                |
          v           v                v
      [External APIs, services, databases, etc.]

```

---

## Durable Agents

Any agent can be wrapped in a **`TemporalAgent`**:

- Wraps an agent for use inside **Temporal workflows**.
- Automatically offloads **I/O work** to activities.
- Freezes **model and toolsets** at wrapping time to ensure consistency.
- Original agent remains usable outside workflows.

---

## Temporal Integration Considerations

### Requirements
- **Stable & unique names** for all activities (derived from agent name + toolset IDs).
- Agent/toolset names **must not change** after deployment, otherwise workflows may break.

### Context & Dependencies
- Data between workflows and activities must be **serializable**.
- Temporal enforces a **2MB payload size limit**.
- Only a subset of `RunContext` is available by default.  
  For more, subclass `TemporalRunContext` with custom serialization.

### Streaming
- `Agent.run_stream()` and `Agent.iter()` are **not supported** directly.  
- Use an **event stream handler** for streaming via `TemporalAgent.run()`.

### Activity Configuration
- Configurable via `temporalio.workflow.ActivityConfig`:
  - `activity_config`: Default settings (timeouts, retries).
  - `model_activity_config`: For model requests.
  - `toolset_activity_config`: For toolset-specific calls.
  - `tool_activity_config`: For specific tool calls.
- Non-I/O tools can be excluded from activities (must be `async`).

### Retries
- **Disable redundant retries** in provider clients (e.g., set `max_retries=0`).
- Use **Temporal’s retry policy** for consistency.

---

## Observability with Logfire

- **Temporal**: emits workflow/activity metrics and telemetry.  
- **Pydantic AI**: emits agent runs, model requests, and tool calls.  
- **Logfire**: aggregates both for **end-to-end observability**.

Integration requires adding `LogfirePlugin` when connecting the Temporal client.  
You can customize or disable metrics collection if needed.

---

## Known Issues

### Pandas Import Error
When using `pandas` with `logfire.info` inside an activity, you may see:

```

AttributeError: partially initialized module 'pandas' has no attribute '\_pandas\_parser\_CAPI'

````

**Fix:** Use Temporal’s import passthrough:

```python
from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    import pandas
````

---

## Resources

* [Pydantic AI Documentation](https://docs.pydantic.dev/ai)
* [Temporal Documentation](https://docs.temporal.io/)
* [Temporal Python SDK Guide](https://python.temporal.io/)



