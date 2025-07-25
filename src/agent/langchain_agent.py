"""LangChain tool-calling agent for financial risk analysis."""

import os
import logging
import pandas as pd

from src.agent.prompts import SYSTEM_PROMPT, NO_DATA_MESSAGE
from src.agent.tools import set_context, get_all_tools

logger = logging.getLogger(__name__)

last_tool_calls: list[str] = []

# Keywords that suggest a methodology/data-source question suitable for RAG
_RAG_KEYWORDS = (
    "what is", "how is", "how does", "explain", "define", "definition",
    "methodology", "formula", "calculation", "method", "approach",
    "where did", "data source", "data come from", "dataset", "sample",
    "safety", "rule", "policy", "limitation", "limitation",
    "mcp", "architecture", "responsible", "eu ai", "act",
    "expected shortfall", "value-at-risk", "var", "drawdown", "volatility",
    "return", "log return",
)


def _is_rag_question(question: str) -> bool:
    q = question.lower()
    return any(kw in q for kw in _RAG_KEYWORDS)


def _has_api_key() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY", "").strip())


def _build_agent():
    from langchain_anthropic import ChatAnthropic
    from langchain.agents import create_tool_calling_agent, AgentExecutor
    from langchain_core.prompts import ChatPromptTemplate

    llm = ChatAnthropic(model="claude-haiku-4-5", temperature=0, max_tokens=2048)

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
        "answer":      str,
        "tool_calls":  list[str],
        "rag_sources": list[str],
        "rag_chunks":  list[dict],
        "basis":       str,   # "calculation" | "rag" | "mixed" | "no_data" | "error"
        "error":       str | None,
    }
    """
    global last_tool_calls
    last_tool_calls = []

    if prices is None or len(prices) == 0:
        return {
            "answer": NO_DATA_MESSAGE,
            "tool_calls": [],
            "rag_sources": [],
            "rag_chunks": [],
            "basis": "no_data",
            "error": None,
        }

    set_context(prices, dataset_label, confidence, rolling_window)

    # --- RAG retrieval (runs for methodology/data-source questions) ---
    rag_context = ""
    rag_sources: list[str] = []
    rag_chunks: list[dict] = []

    if _is_rag_question(question):
        try:
            from src.rag.retriever import retrieve_with_context
            rag_result = retrieve_with_context(question)
            if rag_result["found"]:
                rag_context = "\n\n" + rag_result["context"]
                rag_sources = rag_result["sources"]
                rag_chunks = rag_result["chunks"]
        except Exception as e:
            logger.warning("RAG retrieval failed: %s", e)

    try:
        executor = _build_agent()
        augmented_input = (
            f"Dataset loaded: {dataset_label} ({len(prices):,} observations).\n\n"
            f"Question: {question}"
            + rag_context
        )
        result = executor.invoke({"input": augmented_input})
        raw_output = result.get("output", "")

        if isinstance(raw_output, list):
            answer = " ".join(
                block.get("text", "") if isinstance(block, dict) else str(block)
                for block in raw_output
            ).strip()
        else:
            answer = str(raw_output).strip()

        steps = result.get("intermediate_steps", [])
        tool_calls = []
        for step in steps:
            if isinstance(step, tuple) and len(step) == 2:
                action = step[0]
                if hasattr(action, "tool"):
                    tool_calls.append(action.tool)

        last_tool_calls = tool_calls

        if tool_calls and rag_sources:
            basis = "mixed"
        elif tool_calls:
            basis = "calculation"
        elif rag_sources:
            basis = "rag"
        else:
            basis = "reasoning"

        return {
            "answer": answer,
            "tool_calls": tool_calls,
            "rag_sources": rag_sources,
            "rag_chunks": rag_chunks,
            "basis": basis,
            "error": None,
        }

    except Exception as e:
        logger.error("Agent error: %s", e, exc_info=True)
        return {
            "answer": f"The agent encountered an error: {e}",
            "tool_calls": [],
            "rag_sources": [],
            "rag_chunks": [],
            "basis": "error",
            "error": str(e),
        }


def api_key_available() -> bool:
    return _has_api_key()
