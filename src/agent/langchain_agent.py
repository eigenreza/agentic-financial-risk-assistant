"""LangChain tool-calling agent for financial risk analysis."""

import os
import json
import logging
import pandas as pd

from src.agent.prompts import SYSTEM_PROMPT, NO_DATA_MESSAGE
from src.agent.tools import set_context, get_all_tools

logger = logging.getLogger(__name__)

# Populated by the agent after each run for display in the UI
last_tool_calls: list[dict] = []


def _has_api_key() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY", "").strip())


def _build_agent():
    """Construct and return a LangChain ReAct agent with the risk tools."""
    from langchain_anthropic import ChatAnthropic
    from langchain.agents import create_tool_calling_agent, AgentExecutor
    from langchain_core.prompts import ChatPromptTemplate

    llm = ChatAnthropic(
        model="claude-haiku-4-5-20251001",
        temperature=0,
        max_tokens=2048,
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ])

    tools = get_all_tools()
    agent = create_tool_calling_agent(llm, tools, prompt)
    return AgentExecutor(agent=agent, tools=tools, verbose=True, max_iterations=5)


def run_agent(
    question: str,
    prices: pd.Series | None,
    dataset_label: str = "",
    confidence: float = 0.95,
    rolling_window: int = 21,
) -> dict:
    """
    Run the agent on a user question and return a structured response dict:
    {
        "answer": str,
        "tool_calls": list[str],
        "basis": str,          # "calculation" | "fallback" | "no_data"
        "error": str | None,
    }
    """
    global last_tool_calls
    last_tool_calls = []

    if prices is None or len(prices) == 0:
        return {
            "answer": NO_DATA_MESSAGE,
            "tool_calls": [],
            "basis": "no_data",
            "error": None,
        }

    set_context(prices, dataset_label, confidence, rolling_window)

    try:
        executor = _build_agent()
        result = executor.invoke({"input": question})
        answer = result.get("output", "")

        # Extract tool names from intermediate steps
        steps = result.get("intermediate_steps", [])
        tool_calls = []
        for step in steps:
            if isinstance(step, tuple) and len(step) == 2:
                action = step[0]
                if hasattr(action, "tool"):
                    tool_calls.append(action.tool)

        last_tool_calls = tool_calls
        return {
            "answer": answer,
            "tool_calls": tool_calls,
            "basis": "calculation" if tool_calls else "reasoning",
            "error": None,
        }

    except Exception as e:
        logger.error("Agent error: %s", e, exc_info=True)
        return {
            "answer": f"The agent encountered an error: {e}",
            "tool_calls": [],
            "basis": "error",
            "error": str(e),
        }


def api_key_available() -> bool:
    return _has_api_key()
