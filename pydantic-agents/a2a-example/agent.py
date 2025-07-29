# advanced_agent.py

import os
import pickle
from typing import Optional, List, Any
from pydantic import BaseModel, Field

from pydantic_ai import Agent, RunContext, ModelRetry
from pydantic_ai.messages import ModelMessage, ModelResponse
from pydantic_ai.models.gemini import GeminiModel

# === Define structured result type ===
class CubeResult(BaseModel):
    expression: str = Field(description="The arithmetic expression")
    result: float = Field(description="Calculated numeric result")

# === Load Gemini model ===
model = GeminiModel('gemini-2.5-flash')

# === Create agent with structured output ===
agent = Agent(
    model=model,
    system_prompt="Evaluate Python math expressions step by step.",
    result_type=CubeResult
)

# === Optional: custom validator runs code execution ===
@agent.result_validator
def validate_result(ctx: RunContext[Any], result_data: CubeResult) -> CubeResult:
    """Validate the mathematical expression and result."""
    try:
        # Simple validation - evaluate the expression to check if result matches
        # WARNING: This is unsafe for production - use ast.literal_eval or a proper math parser
        calculated = eval(result_data.expression)
        if abs(calculated - result_data.result) > 0.0001:  # Allow for floating point precision
            raise ValueError(f"Expression result {calculated} doesn't match claimed result {result_data.result}")
        return result_data
    except Exception as e:
        raise ValueError(f"Invalid expression or result: {e}")

# === Message history persistence utilities ===
MEMORY_FILE = "./memory.pkl"
MAX_HISTORY = 10

def read_memory() -> List[ModelMessage]:
    """Load conversation history from disk."""
    try:
        if os.path.exists(MEMORY_FILE):
            with open(MEMORY_FILE, "rb") as f:
                return pickle.load(f)
    except Exception as e:
        print(f"Error reading memory: {e}")
    return []

def write_memory(history: List[ModelMessage]) -> None:
    """Save conversation history to disk."""
    try:
        with open(MEMORY_FILE, "wb") as f:
            pickle.dump(history, f)
    except Exception as e:
        print(f"Error writing memory: {e}")

def filter_msg_by_type(msgs: List[ModelMessage], msg_type) -> List[ModelMessage]:
    """Filter messages by type."""
    return [m for m in msgs if isinstance(m, msg_type)]

# === Create A2A app ===
app = agent.to_a2a(
    name="complex-calc-agent",
    description="Agent to compute math expressions and return structured outputs",
    version="0.1.0",
)

# === CLI loop example ===
if __name__ == "__main__":
    history = read_memory()
    print("Math Expression Calculator Agent")
    print("Enter math expressions to evaluate (or 'exit' to quit)")
    
    while True:
        try:
            usr = input("\nEnter math expression: ").strip()
            if usr.lower() in ("exit", "quit", "q"):
                break
            
            if not usr:
                continue
                
            # Run the agent
            result = agent.run_sync(
                usr,
                deps=usr,  # pass the expression as deps
                message_history=history
            )
            
            # Display results
            print(f"Expression: {result.data.expression}")
            print(f"Result: {result.data.result}")
            
            # Update message history
            history.extend(result.new_messages())
            # Keep only the most recent messages
            history = history[-MAX_HISTORY:]
            write_memory(history)
            
        except ModelRetry as e:
            print(f"Model requested retry: {e}")
            continue
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"Error: {e}")
            continue

    print("Agent stopped.")

    # To run A2A server instead, uncomment the following:
    # uvicorn advanced_agent:app --host 0.0.0.0 --port 8000