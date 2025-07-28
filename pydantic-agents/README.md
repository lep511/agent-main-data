### Installation

```bash
uv add pydantic-ai
```

Pydantic AI has an excellent (but completely optional) integration with Pydantic Logfire to help you view and understand agent runs.

To use Logfire with Pydantic AI, install pydantic-ai or pydantic-ai-slim with the logfire optional group:

```bash
uv add "pydantic-ai[logfire]"
```

### Usage

Run with:

```bash
    uv run -m bank_support
```